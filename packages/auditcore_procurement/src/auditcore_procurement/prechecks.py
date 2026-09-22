"""Deterministic procurement prechecks over an explicitly selected, versioned profile.

Extraction of ``ProcurementPreChecker`` (AST-identical in
``janpow77/flowinvoice@fb2d185`` and ``janpow77/audit-portal@d8eefa4``) and
the ``threshold_rules``/``required_documents_by_procedure`` of the
``PROCUREMENT_HVTG`` ruleset. ``mode="legacy"`` reproduces the source results
exactly. ``mode="strict"`` applies the corrections listed in
``docs/behavior-changes.md`` (P-C01…P-C05); it never decides a procurement
case, it only reports rule results. Thresholds are source values whose
currency is not confirmed (HUMAN_DECISION_REQUIRED).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from importlib import resources
from typing import Any

PASS = "PASS"
WARNING = "WARNING"
FAIL = "FAIL"
NOT_APPLICABLE = "NOT_APPLICABLE"
NOT_CHECKED = "NOT_CHECKED"
MODES = ("legacy", "strict")


class ProfileError(ValueError):
    """The precheck profile is missing or malformed."""


@dataclass(frozen=True)
class Tier:
    """Threshold tier: inclusive upper bound (``None`` = open), expected procedure, bids."""

    name: str
    maximum: float | None
    procedure: str
    min_bids: int


@dataclass(frozen=True)
class PrecheckProfile:
    """Versioned, source-bound rules of the deterministic prechecks."""

    id: str
    version: str
    status: str
    legal_status: str
    construction_marker: str
    tiers: Mapping[str, tuple[Tier, ...]]
    fallback_tier: str
    required_documents: Mapping[str, tuple[str, ...]]
    bid_document_type: str
    default_min_bids: int
    warning_above_percent: float
    fail_above_percent: float
    fail_reference: str
    source: Mapping[str, Any]
    fingerprint: str

    @property
    def reference(self) -> dict[str, str]:
        """Identity recorded in every result."""
        return {"id": self.id, "version": self.version, "fingerprint": self.fingerprint}


def profile_from_dict(data: Mapping[str, Any]) -> PrecheckProfile:
    """Validate and build a profile; nothing is defaulted silently."""
    try:
        if data["schema"] != "auditcore_procurement.precheck-profile/1":
            raise ProfileError("Unbekanntes Profilschema.")
        tiers = {
            category: tuple(
                Tier(
                    t["tier"],
                    None if t["max"] is None else float(t["max"]),
                    str(t["procedure"]),
                    int(t["min_bids"]),
                )
                for t in rows
            )
            for category, rows in data["tiers"].items()
        }
        for category, rows in tiers.items():
            bounds = [t.maximum for t in rows if t.maximum is not None]
            if bounds != sorted(bounds) or not rows or rows[-1].maximum is not None:
                raise ProfileError(
                    f"Schwellenstufen von '{category}' sind nicht aufsteigend/offen."
                )
        deviation = data["value_deviation"]
        if not 0 <= deviation["warning_above_percent"] <= deviation["fail_above_percent"]:
            raise ProfileError("Ungültige Abweichungsschwellen.")
        canonical = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return PrecheckProfile(
            id=data["id"],
            version=data["version"],
            status=data["status"],
            legal_status=data["legal_status"],
            construction_marker=data["construction_marker"],
            tiers=tiers,
            fallback_tier=data["fallback_tier"],
            required_documents={k: tuple(v) for k, v in data["required_documents"].items()},
            bid_document_type=data["bid_document_type"],
            default_min_bids=int(data["default_min_bids"]),
            warning_above_percent=float(deviation["warning_above_percent"]),
            fail_above_percent=float(deviation["fail_above_percent"]),
            fail_reference=deviation["fail_reference"],
            source=dict(data["source"]),
            fingerprint=hashlib.sha256(canonical.encode()).hexdigest(),
        )
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, ProfileError):
            raise
        raise ProfileError(f"Profil ist unvollständig oder fehlerhaft: {exc!r}") from exc


def load_profile(profile_id: str, version: str) -> PrecheckProfile:
    """Load an explicitly named packaged profile version."""
    name = f"{profile_id}-{version}.json"
    entry = resources.files("auditcore_procurement.profiles").joinpath(name)
    if "/" in name or "\\" in name or not entry.is_file():
        raise ProfileError(f"Profil {profile_id} in Version {version} ist nicht vorhanden.")
    profile = profile_from_dict(json.loads(entry.read_text(encoding="utf-8")))
    if (profile.id, profile.version) != (profile_id, version):
        raise ProfileError("Profildatei und Profilkennung stimmen nicht überein.")
    return profile


def _category(profile: PrecheckProfile, service_type: str) -> str:
    return "construction" if profile.construction_marker in service_type else "supply_service"


def _tier(profile: PrecheckProfile, category: str, name: str | None) -> Tier | None:
    for tier in profile.tiers.get(category, ()):
        if tier.name == name:
            return tier
    return None


def _result(check_id: str, name: str, status: str, message: str, **extra: Any) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "name_de": name,
        "status": status,
        "message": message,
        **extra,
        "source": "RULE",
    }


def _missing(value: Decimal | None, mode: str) -> bool:
    return value is None if mode == "strict" else not value


def check_threshold(
    profile: PrecheckProfile,
    estimated_value: Decimal | None,
    service_type: str,
    threshold_tier: str | None,
    mode: str = "legacy",
) -> dict[str, Any]:
    """Tier from the estimated value (inclusive maxima in profile order)."""
    name = "Schwellenwert-Klassifikation"
    if _missing(estimated_value, mode):
        return _result(
            "precheck_threshold", name, WARNING, "Kein geschaetzter Auftragswert angegeben."
        )
    assert estimated_value is not None
    category = _category(profile, service_type)
    calculated = (
        next(
            (
                t.name
                for t in profile.tiers.get(category, ())
                if t.maximum is None or float(estimated_value) <= t.maximum
            ),
            None,
        )
        or profile.fallback_tier
    )
    if threshold_tier and threshold_tier != calculated:
        return _result(
            "precheck_threshold",
            name,
            FAIL,
            f"Schwellenwert-Stufe '{threshold_tier}' stimmt nicht mit berechnetem Wert "
            f"'{calculated}' ueberein "
            f"(Auftragswert: {estimated_value} EUR, Kategorie: {category}).",
            calculated_tier=calculated,
        )
    return _result(
        "precheck_threshold",
        name,
        PASS,
        f"Schwellenwert korrekt: {calculated} ({estimated_value} EUR).",
        calculated_tier=calculated,
    )


def check_procedure(
    profile: PrecheckProfile,
    procurement_type: str,
    threshold_tier: str,
    service_type: str,
    mode: str = "legacy",
) -> dict[str, Any]:
    """Procedure vs. tier; legacy uses mutual substring matching."""
    name = "Verfahrenswahl vs. Schwellenwert"
    tier = _tier(profile, _category(profile, service_type), threshold_tier)
    expected = tier.procedure if tier else ""
    if mode == "strict" and tier is None:
        return _result(
            "precheck_procedure_threshold",
            name,
            NOT_CHECKED,
            f"Schwellenwert-Stufe '{threshold_tier}' ist im Profil nicht definiert.",
        )
    proc_lower, expected_lower = procurement_type.lower(), expected.lower()
    matches = (
        proc_lower == expected_lower
        if mode == "strict"
        else expected_lower in proc_lower or proc_lower in expected_lower
    )
    if matches:
        return _result(
            "precheck_procedure_threshold",
            name,
            PASS,
            f"Vergabeart '{procurement_type}' passt zum Schwellenwert '{threshold_tier}'.",
        )
    return _result(
        "precheck_procedure_threshold",
        name,
        FAIL,
        f"Vergabeart '{procurement_type}' passt NICHT zum Schwellenwert '{threshold_tier}'. "
        f"Erwartet: '{expected}'.",
        expected_procedure=expected,
    )


def check_required_documents(
    profile: PrecheckProfile,
    procurement_type: str | None,
    documents: Sequence[Mapping[str, Any]],
    mode: str = "legacy",
) -> dict[str, Any]:
    """Required document types (with multiplicity) for the procedure."""
    name = "Pflichtdokumente"
    if not procurement_type:
        return _result(
            "precheck_required_docs",
            name,
            WARNING,
            "Vergabeart unbekannt, Pflichtdokumente nicht pruefbar.",
        )
    required = None
    for procedure, docs in profile.required_documents.items():
        lowered = procedure.lower()
        if (
            lowered == procurement_type.lower()
            if mode == "strict"
            else lowered in procurement_type.lower() or procurement_type.lower() in lowered
        ):
            required = docs
            break
    if required is None:
        return _result(
            "precheck_required_docs",
            name,
            WARNING,
            f"Keine Pflichtdokument-Regel fuer '{procurement_type}' hinterlegt.",
        )
    present = [d.get("procurement_doc_type", "") for d in documents]
    missing: list[tuple[str, int, int]] = []
    for doc_type in required:
        needed, have = required.count(doc_type), present.count(doc_type)
        if have < needed and doc_type not in [m[0] for m in missing]:
            missing.append((doc_type, needed, have))
    if missing:
        text = ", ".join(f"{t} (benoetigt: {n}, vorhanden: {p})" for t, n, p in missing)
        return _result(
            "precheck_required_docs",
            name,
            FAIL,
            f"Fehlende Pflichtdokumente: {text}.",
            missing_documents=[{"type": t, "needed": n, "present": p} for t, n, p in missing],
        )
    return _result("precheck_required_docs", name, PASS, "Alle Pflichtdokumente vorhanden.")


def check_minimum_bids(
    profile: PrecheckProfile,
    threshold_tier: str | None,
    service_type: str,
    documents: Sequence[Mapping[str, Any]],
    mode: str = "legacy",
) -> dict[str, Any]:
    """Number of bid documents against the tier minimum."""
    name = "Mindestangebote"
    if not threshold_tier:
        return _result("precheck_min_bids", name, NOT_CHECKED, "Schwellenwert unbekannt.")
    tier = _tier(profile, _category(profile, service_type), threshold_tier)
    if mode == "strict" and tier is None:
        return _result(
            "precheck_min_bids",
            name,
            NOT_CHECKED,
            f"Schwellenwert-Stufe '{threshold_tier}' ist im Profil nicht definiert.",
        )
    minimum = tier.min_bids if tier else profile.default_min_bids
    count = sum(1 for d in documents if d.get("procurement_doc_type") == profile.bid_document_type)
    if count < minimum:
        return _result(
            "precheck_min_bids",
            name,
            WARNING if count > 0 else FAIL,
            f"Nur {count} Angebot(e) vorhanden, "
            f"mindestens {minimum} erwartet fuer '{threshold_tier}'.",
            min_required=minimum,
            actual_count=count,
        )
    return _result(
        "precheck_min_bids",
        name,
        PASS,
        f"{count} Angebot(e) vorhanden (Minimum: {minimum}).",
        min_required=minimum,
        actual_count=count,
    )


def check_value_deviation(
    profile: PrecheckProfile, contract_value: Decimal, invoice_value: Decimal
) -> dict[str, Any]:
    """Deviation of invoiced from contracted value in percent (float arithmetic of the source)."""
    if contract_value == 0:
        return _result("precheck_value_deviation", "Wertabweichung", WARNING, "Vertragswert ist 0.")
    name = "Wertabweichung (Auftrags- vs. Abrechnungswert)"
    deviation = abs(float(invoice_value) - float(contract_value))
    percent = (deviation / float(contract_value)) * 100
    values = f"(Vertrag: {contract_value} EUR, Abrechnung: {invoice_value} EUR)"
    if percent > profile.fail_above_percent:
        return _result(
            "precheck_value_deviation",
            name,
            FAIL,
            f"Erhebliche Abweichung: {percent:.1f}% {values}. "
            f"Pruefung gemaess {profile.fail_reference} erforderlich.",
            deviation_percent=round(percent, 1),
        )
    if percent > profile.warning_above_percent:
        return _result(
            "precheck_value_deviation",
            name,
            WARNING,
            f"Abweichung: {percent:.1f}% {values}.",
            deviation_percent=round(percent, 1),
        )
    return _result(
        "precheck_value_deviation",
        name,
        PASS,
        f"Abweichung akzeptabel: {percent:.1f}% {values}.",
        deviation_percent=round(percent, 1),
    )


def run_prechecks(
    profile: PrecheckProfile,
    estimated_value: Decimal | None,
    contract_value: Decimal | None,
    invoice_value: Decimal | None,
    service_type: str,
    procurement_type: str | None,
    threshold_tier: str | None,
    documents: Sequence[Mapping[str, Any]],
    *,
    mode: str = "legacy",
    now: datetime | None = None,
) -> dict[str, Any]:
    """All prechecks in source order; overall status is the worst of FAIL/WARNING/PASS.

    ``mode="legacy"``: identical results to the source (``timestamp`` from
    ``now`` or the current UTC time). ``mode="strict"`` additionally records
    ``mode`` and the profile identity and applies P-C01…P-C05.
    """
    if mode not in MODES:
        raise ValueError(f"Unbekannter Modus '{mode}'.")
    results = [check_threshold(profile, estimated_value, service_type, threshold_tier, mode)]
    if procurement_type and threshold_tier:
        results.append(
            check_procedure(profile, procurement_type, threshold_tier, service_type, mode)
        )
    results.append(check_required_documents(profile, procurement_type, documents, mode))
    results.append(check_minimum_bids(profile, threshold_tier, service_type, documents, mode))
    both = (
        (contract_value is not None and invoice_value is not None)
        if mode == "strict"
        else (bool(contract_value) and bool(invoice_value))
    )
    if both:
        assert contract_value is not None and invoice_value is not None
        results.append(check_value_deviation(profile, contract_value, invoice_value))
    elif mode == "strict" and (contract_value is None) != (invoice_value is None):
        results.append(
            _result(
                "precheck_value_deviation",
                "Wertabweichung",
                NOT_CHECKED,
                "Vertrags- oder Abrechnungswert fehlt.",
            )
        )
    overall = PASS
    for row in results:
        if row["status"] == FAIL:
            overall = FAIL
            break
        if row["status"] == WARNING:
            overall = WARNING
    report: dict[str, Any] = {
        "checks": results,
        "overall_status": overall,
        "timestamp": (now or datetime.now(UTC)).isoformat(),
    }
    if mode == "strict":
        report["mode"] = mode
        report["profile"] = profile.reference
    return report
