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

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any
from xml.etree.ElementTree import Element  # noqa: S405 - type only; parsing uses defusedxml

from auditcore_harvest import ParserError, Transport, TransportError, raise_for_status

from .errors import DependencyError, QueryError
from .profiles import RegistryProfile

VIES_URL = "https://ec.europa.eu/taxation_customs/vies/services/checkVatService"
REGISTER_URL = "https://db.offeneregister.de/openregister"
_VAT = re.compile(r"^([A-Z]{2})(.+)$")
_SOAP = """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:urn="urn:ec.europa.eu:taxud:vies:services:checkVat:types">
    <soapenv:Body>
        <urn:checkVat>
            <urn:countryCode>{country}</urn:countryCode>
            <urn:vatNumber>{number}</urn:vatNumber>
        </urn:checkVat>
    </soapenv:Body>
</soapenv:Envelope>"""
UNDISCLOSED = "---"


def split_vat_id(vat_id: str) -> tuple[str, str, str]:
    """Normalised VAT id, country code and number; a wrong format is a :class:`QueryError`."""
    compact = vat_id.replace(" ", "").upper()
    match = _VAT.match(compact)
    if not match:
        raise QueryError("USt-IdNr. hat kein gültiges Format (Ländercode + Nummer).")
    return compact, match.group(1), match.group(2)


def vies_request(vat_id: str) -> tuple[str, bytes, dict[str, str]]:
    """URL, SOAP body and headers of a ``checkVat`` request (escaped values)."""
    _, country, number = split_vat_id(vat_id)
    from xml.sax.saxutils import escape  # noqa: S406 - escaping only, no parsing

    body = _SOAP.format(country=escape(country), number=escape(number))
    return VIES_URL, body.encode("utf-8"), {"Content-Type": "text/xml; charset=utf-8"}


@dataclass(frozen=True)
class VatCheck:
    """VIES answer; ``status`` is ``VALID``, ``INVALID`` or ``UNAVAILABLE``."""

    status: str
    vat_id: str
    country_code: str
    request_date: str | None = None
    name: str | None = None
    address: str | None = None
    name_disclosed: bool = False
    fault: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """JSON view."""
        return {
            "status": self.status,
            "vat_id": self.vat_id,
            "country_code": self.country_code,
            "request_date": self.request_date,
            "name": self.name,
            "address": self.address,
            "name_disclosed": self.name_disclosed,
            "fault": self.fault,
        }


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].rsplit(":", 1)[-1]


def parse_vies_response(vat_id: str, body: bytes) -> VatCheck:
    """Interpret a ``checkVat`` answer regardless of namespace prefixes."""
    compact, country, _ = split_vat_id(vat_id)
    try:
        from defusedxml.ElementTree import fromstring
    except ImportError as exc:  # pragma: no cover - exercised in the installed smoke test
        raise DependencyError(
            "Für VIES ist 'auditcore_registry_sources[xml]' zu installieren."
        ) from exc
    try:
        root: Element = fromstring(body)
    except Exception as exc:  # noqa: BLE001 - every parser failure is a parser error
        raise ParserError(f"VIES-Antwort nicht lesbar: {exc}") from exc
    values: dict[str, str] = {}
    for element in root.iter():
        name = _local(element.tag)
        if name in ("valid", "name", "address", "requestDate", "faultstring", "countryCode"):
            values.setdefault(name, (element.text or "").strip())
    if "faultstring" in values:
        return VatCheck("UNAVAILABLE", compact, country, fault=values["faultstring"] or "Fault")
    if "valid" not in values:
        raise ParserError("VIES-Antwort ohne Gültigkeitsangabe.")
    found_name = values.get("name") or None
    address = values.get("address") or None
    disclosed = bool(found_name and found_name != UNDISCLOSED)
    return VatCheck(
        status="VALID" if values["valid"].lower() == "true" else "INVALID",
        vat_id=compact,
        country_code=values.get("countryCode") or country,
        request_date=values.get("requestDate") or None,
        name=found_name if disclosed else None,
        address=address if address and address != UNDISCLOSED else None,
        name_disclosed=disclosed,
    )


def check_vat(transport: Transport, vat_id: str, *, timeout: float = 15.0) -> VatCheck:
    """One VIES request through the injected transport; failures become ``UNAVAILABLE``."""
    url, body, headers = vies_request(vat_id)
    compact, country, _ = split_vat_id(vat_id)
    try:
        response = transport.request("POST", url, headers=headers, data=body, timeout=timeout)
        if response.status >= 500:
            # VIES reports MS_UNAVAILABLE and similar as SOAP faults with HTTP 500.
            try:
                return parse_vies_response(vat_id, response.body)
            except ParserError:
                pass
        raise_for_status(response)
    except TransportError as exc:
        return VatCheck("UNAVAILABLE", compact, country, fault=str(exc))
    return parse_vies_response(vat_id, response.body)


#: Datasette query with bound parameters; the name is never part of the SQL text.
REGISTER_SQL = "select * from companies where name like :pattern limit :limit"


def register_query(name: str, *, limit: int = 5) -> tuple[str, dict[str, str]]:
    """URL and parameters of a register lookup (datasette named parameters)."""
    if not name or not name.strip():
        raise QueryError("Pflichtangabe fehlt: Firmenname.")
    return f"{REGISTER_URL}.json", {
        "sql": REGISTER_SQL,
        "pattern": f"%{name.strip()}%",
        "limit": str(int(limit)),
        "_shape": "objects",
    }


@dataclass(frozen=True)
class RegisterCompany:
    """First register row with the mapped status."""

    name: str
    status: str
    legal_form: str | None
    registration_number: str | None
    registration_authority: str | None
    address: str | None
    raw_status: str

    def to_dict(self) -> dict[str, Any]:
        """JSON view."""
        return {
            "name": self.name,
            "status": self.status,
            "legal_form": self.legal_form,
            "registration_number": self.registration_number,
            "registration_authority": self.registration_authority,
            "address": self.address,
            "raw_status": self.raw_status,
        }


@dataclass(frozen=True)
class RegisterLookup:
    """``FOUND``, ``NOT_FOUND`` or ``UNAVAILABLE`` — the last is never "not in register"."""

    status: str
    company: RegisterCompany | None = None
    candidates: int = 0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """JSON view."""
        return {
            "status": self.status,
            "company": None if self.company is None else self.company.to_dict(),
            "candidates": self.candidates,
            "error": self.error,
        }


def register_status(raw: str, profile: RegistryProfile) -> str:
    """Map an OffeneRegister status text with the profile's words (else ``unknown``)."""
    words = profile.setting("register_status")
    text = (raw or "").lower()
    if any(w in text for w in words["dissolved"]):
        return "dissolved"
    if any(w in text for w in words["active"]):
        return "active"
    return "unknown"


def parse_register_rows(body: bytes, profile: RegistryProfile) -> RegisterLookup:
    """Datasette ``_shape=objects`` answer → first company (as the source)."""
    try:
        data = json.loads(body)
        rows = data["rows"]
        if not isinstance(rows, list):
            raise TypeError("rows")
    except (ValueError, KeyError, TypeError) as exc:
        raise ParserError(f"Registerantwort nicht lesbar: {exc!r}") from exc
    if not rows:
        return RegisterLookup("NOT_FOUND")
    row = rows[0]
    raw = str(row.get("current_status") or "")
    return RegisterLookup(
        "FOUND",
        RegisterCompany(
            name=str(row.get("name", "")),
            status=register_status(raw, profile),
            legal_form=row.get("company_type"),
            registration_number=row.get("company_number"),
            registration_authority=row.get("native_company_number"),
            address=row.get("registered_address"),
            raw_status=raw,
        ),
        candidates=len(rows),
    )


def lookup_register(
    transport: Transport, name: str, profile: RegistryProfile, *, timeout: float = 15.0
) -> RegisterLookup:
    """One datasette request; transport failures become ``UNAVAILABLE``."""
    url, params = register_query(name, limit=int(profile.setting("register_query")["limit"]))
    try:
        response = raise_for_status(transport.request("GET", url, params=params, timeout=timeout))
    except TransportError as exc:
        return RegisterLookup("UNAVAILABLE", error=str(exc))
    return parse_register_rows(response.body, profile)


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
    decisions: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)

    @property
    def complete(self) -> bool:
        """True if every requested check produced an answer."""
        return not self.unavailable

    def to_dict(self) -> dict[str, Any]:
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
    if vat is not None:
        if vat.status == "UNAVAILABLE":
            indicators.append("VIES_SERVICE_UNAVAILABLE")
            unavailable.append("vies")
        elif vat.status == "INVALID":
            indicators.append("INVALID_VAT_ID")
        elif vat.name_disclosed and vat.name:
            if not names_match(name, vat.name, profile):
                indicators.append("VAT_NAME_MISMATCH")
        else:
            notes.append("VIES nennt keinen Namen (---); der Namensabgleich entfällt.")
    if country in profile.setting("register_countries"):
        if register is None or register.status == "UNAVAILABLE":
            unavailable.append("register")
            notes.append("Das Register war nicht erreichbar; „nicht im Register“ ist nicht belegt.")
        elif register.status == "NOT_FOUND":
            indicators.append("NOT_IN_REGISTER")
        elif register.company is not None:
            if register.company.status == "dissolved":
                indicators.append("COMPANY_DISSOLVED")
            elif register.company.status == "inactive":
                indicators.append("COMPANY_INACTIVE")
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
