"""Company verification: EU VIES VAT check, OffeneRegister lookup and indicator scoring.

Source: flowinvoice ``CompanyVerifier`` (profile ``flowinvoice.company_verification``).
Verified live on 2026-09-23: VIES answers with namespace prefixes
(``<ns2:valid>``) and German numbers without name (``---``); the source looks
for ``<valid>true</valid>`` without prefix and therefore reports *every* VAT
number as invalid (``INVALID_VAT_ID``). OffeneRegister's datasette endpoint
answered HTTP 502 on that day.

Deliberate differences (see ``docs/behavior-changes.md``): the VIES answer is
parsed as XML independent of prefixes; a SOAP fault or transport failure is
``UNAVAILABLE``, never ``INVALID``; an undisclosed name (``---``) is not
compared; the register query uses datasette parameters instead of SQL text;
an unreachable register is reported as unavailable instead of "not in
register"; legal forms are removed as whole words (the source removes
``ag`` inside ``Hagen``).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from ._company_register import (
    REGISTER_SQL,
    REGISTER_URL,
    RegisterCompany,
    RegisterLookup,
    lookup_register,
    parse_register_rows,
    register_query,
    register_status,
)
from ._company_vat import (
    UNDISCLOSED,
    VIES_URL,
    VatCheck,
    check_vat,
    parse_vies_response,
    split_vat_id,
    vies_request,
)
from ._types import JsonObject, JsonValue
from .profiles import RegistryProfile

__all__ = [
    "REGISTER_SQL",
    "REGISTER_URL",
    "UNDISCLOSED",
    "VIES_URL",
    "CompanyVerification",
    "RegisterCompany",
    "RegisterLookup",
    "VatCheck",
    "check_vat",
    "lookup_register",
    "names_match",
    "normalize_company_name",
    "parse_register_rows",
    "parse_vies_response",
    "register_query",
    "register_status",
    "score_indicators",
    "split_vat_id",
    "verify_company",
    "vies_request",
]


def normalize_company_name(name: str, profile: RegistryProfile) -> str:
    """Lower case, legal forms of the profile removed as whole word sequences."""
    tokens = name.lower().split()
    forms = sorted(
        (tuple(f.split()) for f in profile.setting("legal_forms")), key=len, reverse=True
    )
    result: list[str] = []
    index = 0
    while index < len(tokens):
        for form in forms:
            if tuple(tokens[index : index + len(form)]) == form:
                index += len(form)
                break
        else:
            result.append(tokens[index])
            index += 1
    return " ".join(result)


def names_match(a: str, b: str, profile: RegistryProfile) -> bool:
    """Equal, contained, or enough shared leading words (source rule, word-based forms)."""
    rule = profile.setting("name_match")
    n1, n2 = normalize_company_name(a, profile), normalize_company_name(b, profile)
    if n1 == n2 or n1 in n2 or n2 in n1:
        return True
    w1, w2 = n1.split()[: int(rule["leading_words"])], n2.split()[: int(rule["leading_words"])]
    if w1 and w2:
        common = len(set(w1) & set(w2))
        if common >= min(len(w1), len(w2)) * float(rule["threshold"]):
            return True
    return False


@dataclass(frozen=True)
class CompanyVerification:
    """Indicators, score and the checks that could not be carried out."""

    is_verified: bool
    indicators: tuple[str, ...]
    score: float
    vat: VatCheck | None
    register: RegisterLookup | None
    unavailable: tuple[str, ...]
    notes: tuple[str, ...]
    profile: Mapping[str, str]
    decisions: tuple[Mapping[str, JsonValue], ...] = field(default_factory=tuple)

    @property
    def complete(self) -> bool:
        """True if every requested check produced an answer."""
        return not self.unavailable

    def to_dict(self) -> JsonObject:
        """JSON view."""
        return {
            "is_verified": self.is_verified,
            "complete": self.complete,
            "indicators": list(self.indicators),
            "score": self.score,
            "vat": None if self.vat is None else self.vat.to_dict(),
            "register": None if self.register is None else self.register.to_dict(),
            "unavailable": list(self.unavailable),
            "notes": list(self.notes),
            "profile": dict(self.profile),
            "decisions": [dict(d) for d in self.decisions],
        }


def score_indicators(indicators: Sequence[str], profile: RegistryProfile) -> tuple[bool, float]:
    """``is_verified`` (no critical indicator) and the score after the profile's deductions."""
    critical, warning = profile.setting("critical"), profile.setting("warning")
    deduction = profile.setting("deduction")
    score = 1.0
    for indicator in indicators:
        if indicator in critical:
            score -= float(deduction["critical"])
        elif indicator in warning:
            score -= float(deduction["warning"])
        else:
            score -= float(deduction["other"])
    verified = not any(i in critical for i in indicators)
    return verified, round(max(0.0, score), int(profile.setting("score_digits")))


def _vat_findings(
    vat: VatCheck, name: str, profile: RegistryProfile
) -> tuple[list[str], list[str], list[str]]:
    """Indicators, unavailable checks and notes of the VIES answer."""
    if vat.status == "UNAVAILABLE":
        return ["VIES_SERVICE_UNAVAILABLE"], ["vies"], []
    if vat.status == "INVALID":
        return ["INVALID_VAT_ID"], [], []
    if vat.name_disclosed and vat.name:
        mismatch = not names_match(name, vat.name, profile)
        return (["VAT_NAME_MISMATCH"] if mismatch else []), [], []
    return [], [], ["VIES nennt keinen Namen (---); der Namensabgleich entfällt."]


#: Register company status → indicator (other states raise no indicator).
_REGISTER_STATUS_INDICATORS = {"dissolved": "COMPANY_DISSOLVED", "inactive": "COMPANY_INACTIVE"}


def _register_findings(register: RegisterLookup | None) -> tuple[list[str], list[str], list[str]]:
    """Indicators, unavailable checks and notes of the register lookup."""
    if register is None or register.status == "UNAVAILABLE":
        return (
            [],
            ["register"],
            ["Das Register war nicht erreichbar; „nicht im Register“ ist nicht belegt."],
        )
    if register.status == "NOT_FOUND":
        return ["NOT_IN_REGISTER"], [], []
    if register.company is not None:
        indicator = _REGISTER_STATUS_INDICATORS.get(register.company.status)
        return ([indicator] if indicator else []), [], []
    return [], [], []


def verify_company(
    name: str,
    profile: RegistryProfile,
    *,
    vat: VatCheck | None = None,
    register: RegisterLookup | None = None,
    country: str = "DE",
) -> CompanyVerification:
    """Combine a VIES check and a register lookup into indicators and a score."""
    profile.require_kind("company_verification")
    indicators: list[str] = []
    unavailable: list[str] = []
    notes: list[str] = []
    findings = []
    if vat is not None:
        findings.append(_vat_findings(vat, name, profile))
    if country in profile.setting("register_countries"):
        findings.append(_register_findings(register))
    for found, missing, remarks in findings:
        indicators.extend(found)
        unavailable.extend(missing)
        notes.extend(remarks)
    verified, score = score_indicators(indicators, profile)
    return CompanyVerification(
        is_verified=verified,
        indicators=tuple(indicators),
        score=score,
        vat=vat,
        register=register,
        unavailable=tuple(unavailable),
        notes=tuple(notes),
        profile=profile.reference,
        decisions=profile.decisions,
    )
