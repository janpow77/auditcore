"""Deterministic procurement prechecks over an explicitly selected, versioned profile.

Extraction of ``ProcurementPreChecker`` (AST-identical in
``janpow77/flowinvoice@fb2d185`` and ``janpow77/audit-portal@d8eefa4``) and
the ``threshold_rules``/``required_documents_by_procedure`` of the
``PROCUREMENT_HVTG`` ruleset. ``mode="legacy"`` reproduces the source results
exactly. ``mode="strict"`` applies the corrections listed in
``docs/behavior-changes.md`` (P-C01…P-C05, P-C10…P-C12); it never decides a
procurement case, it only reports rule results.

Profiles with schema 2 (``procurement.hvtg`` 2026.09.2: 2024–2027; 2026.09.3:
2014–2027) hold the EU thresholds per validity period with their official
source. In ``strict`` mode the EU threshold is selected by the date of the
measure/notice (``reference_date``) or an explicit ``year``; a missing period
yields ``REVIEW_REQUIRED``, never a fallback to another period. National tiers
remain application rules (REVIEW_REQUIRED). ``legacy`` mode keeps the source
table unchanged.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from .precheck_common import (
    FAIL,
    MODES,
    NOT_APPLICABLE,
    NOT_CHECKED,
    PASS,
    REVIEW_REQUIRED,
    WARNING,
    CheckResult,
    category_of,
    find_tier,
    result,
)
from .precheck_profile import (
    AUTHORITY_TYPES,
    CURRENT_PROFILE,
    SCHEMAS,
    EuThreshold,
    PrecheckProfile,
    ProfileError,
    ThresholdPeriod,
    ThresholdUnavailable,
    Tier,
    eu_period,
    eu_period_for_year,
    eu_threshold,
    load_profile,
    profile_from_dict,
    profile_from_ruleset,
)
from .precheck_threshold import check_threshold

__all__ = [
    "AUTHORITY_TYPES",
    "CURRENT_PROFILE",
    "FAIL",
    "MODES",
    "NOT_APPLICABLE",
    "NOT_CHECKED",
    "PASS",
    "REVIEW_REQUIRED",
    "SCHEMAS",
    "WARNING",
    "EuThreshold",
    "PrecheckProfile",
    "ProfileError",
    "ThresholdPeriod",
    "ThresholdUnavailable",
    "Tier",
    "check_minimum_bids",
    "check_procedure",
    "check_required_documents",
    "check_threshold",
    "check_value_deviation",
    "eu_period",
    "eu_period_for_year",
    "eu_threshold",
    "load_profile",
    "profile_from_dict",
    "profile_from_ruleset",
    "run_prechecks",
]


def check_procedure(
    profile: PrecheckProfile,
    procurement_type: str,
    threshold_tier: str,
    service_type: str,
    mode: str = "legacy",
) -> CheckResult:
    """Procedure vs. tier; legacy uses mutual substring matching."""
    name = "Verfahrenswahl vs. Schwellenwert"
    tier = find_tier(profile, category_of(profile, service_type), threshold_tier)
    expected = tier.procedure if tier else ""
    if mode == "strict" and tier is None:
        return result(
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
        return result(
            "precheck_procedure_threshold",
            name,
            PASS,
            f"Vergabeart '{procurement_type}' passt zum Schwellenwert '{threshold_tier}'.",
        )
    return result(
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
    documents: Sequence[Mapping[str, object]],
    mode: str = "legacy",
) -> CheckResult:
    """Required document types (with multiplicity) for the procedure."""
    name = "Pflichtdokumente"
    if not procurement_type:
        return result(
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
        return result(
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
        return result(
            "precheck_required_docs",
            name,
            FAIL,
            f"Fehlende Pflichtdokumente: {text}.",
            missing_documents=[{"type": t, "needed": n, "present": p} for t, n, p in missing],
        )
    return result("precheck_required_docs", name, PASS, "Alle Pflichtdokumente vorhanden.")


def check_minimum_bids(
    profile: PrecheckProfile,
    threshold_tier: str | None,
    service_type: str,
    documents: Sequence[Mapping[str, object]],
    mode: str = "legacy",
) -> CheckResult:
    """Number of bid documents against the tier minimum."""
    name = "Mindestangebote"
    if not threshold_tier:
        return result("precheck_min_bids", name, NOT_CHECKED, "Schwellenwert unbekannt.")
    tier = find_tier(profile, category_of(profile, service_type), threshold_tier)
    if mode == "strict" and tier is None:
        return result(
            "precheck_min_bids",
            name,
            NOT_CHECKED,
            f"Schwellenwert-Stufe '{threshold_tier}' ist im Profil nicht definiert.",
        )
    minimum = tier.min_bids if tier else profile.default_min_bids
    count = sum(1 for d in documents if d.get("procurement_doc_type") == profile.bid_document_type)
    if count < minimum:
        return result(
            "precheck_min_bids",
            name,
            WARNING if count > 0 else FAIL,
            f"Nur {count} Angebot(e) vorhanden, "
            f"mindestens {minimum} erwartet fuer '{threshold_tier}'.",
            min_required=minimum,
            actual_count=count,
        )
    return result(
        "precheck_min_bids",
        name,
        PASS,
        f"{count} Angebot(e) vorhanden (Minimum: {minimum}).",
        min_required=minimum,
        actual_count=count,
    )


def check_value_deviation(
    profile: PrecheckProfile, contract_value: Decimal, invoice_value: Decimal
) -> CheckResult:
    """Deviation of invoiced from contracted value in percent (float arithmetic of the source)."""
    if contract_value == 0:
        return result("precheck_value_deviation", "Wertabweichung", WARNING, "Vertragswert ist 0.")
    name = "Wertabweichung (Auftrags- vs. Abrechnungswert)"
    deviation = abs(float(invoice_value) - float(contract_value))
    percent = (deviation / float(contract_value)) * 100
    values = f"(Vertrag: {contract_value} EUR, Abrechnung: {invoice_value} EUR)"
    if percent > profile.fail_above_percent:
        return result(
            "precheck_value_deviation",
            name,
            FAIL,
            f"Erhebliche Abweichung: {percent:.1f}% {values}. "
            f"Pruefung gemaess {profile.fail_reference} erforderlich.",
            deviation_percent=round(percent, 1),
        )
    if percent > profile.warning_above_percent:
        return result(
            "precheck_value_deviation",
            name,
            WARNING,
            f"Abweichung: {percent:.1f}% {values}.",
            deviation_percent=round(percent, 1),
        )
    return result(
        "precheck_value_deviation",
        name,
        PASS,
        f"Abweichung akzeptabel: {percent:.1f}% {values}.",
        deviation_percent=round(percent, 1),
    )


def _deviation_step(
    profile: PrecheckProfile,
    contract_value: Decimal | None,
    invoice_value: Decimal | None,
    mode: str,
) -> CheckResult | None:
    """Value deviation if both values are given; strict reports a single missing value."""
    if mode == "strict":
        if contract_value is not None and invoice_value is not None:
            return check_value_deviation(profile, contract_value, invoice_value)
        if (contract_value is None) != (invoice_value is None):
            return result(
                "precheck_value_deviation",
                "Wertabweichung",
                NOT_CHECKED,
                "Vertrags- oder Abrechnungswert fehlt.",
            )
        return None
    if contract_value and invoice_value:
        return check_value_deviation(profile, contract_value, invoice_value)
    return None


def _overall(results: Sequence[Mapping[str, object]]) -> str:
    """Worst status: FAIL > REVIEW_REQUIRED > WARNING > PASS (first FAIL wins)."""
    overall = PASS
    for row in results:
        if row["status"] == FAIL:
            return FAIL
        if row["status"] == REVIEW_REQUIRED:
            overall = REVIEW_REQUIRED
        elif row["status"] == WARNING and overall != REVIEW_REQUIRED:
            overall = WARNING
    return overall


def run_prechecks(
    profile: PrecheckProfile,
    estimated_value: Decimal | None,
    contract_value: Decimal | None,
    invoice_value: Decimal | None,
    service_type: str,
    procurement_type: str | None,
    threshold_tier: str | None,
    documents: Sequence[Mapping[str, object]],
    *,
    mode: str = "legacy",
    now: datetime | None = None,
    reference_date: date | None = None,
    year: int | None = None,
    authority_type: str | None = None,
) -> CheckResult:
    """All prechecks in source order; overall status is the worst of
    FAIL > REVIEW_REQUIRED > WARNING > PASS (REVIEW_REQUIRED only in strict mode).

    ``mode="legacy"``: identical results to the source (``timestamp`` from
    ``now`` or the current UTC time); ``reference_date``/``year``/``authority_type``
    are ignored. ``mode="strict"`` additionally records ``mode`` and the profile
    identity and applies P-C01…P-C05 and P-C10…P-C12.
    """
    if mode not in MODES:
        raise ValueError(f"Unbekannter Modus '{mode}'.")
    if mode == "legacy":
        reference_date = year = authority_type = None
    results = [
        check_threshold(
            profile,
            estimated_value,
            service_type,
            threshold_tier,
            mode,
            reference_date=reference_date,
            year=year,
            authority_type=authority_type,
        )
    ]
    if procurement_type and threshold_tier:
        results.append(
            check_procedure(profile, procurement_type, threshold_tier, service_type, mode)
        )
    results.append(check_required_documents(profile, procurement_type, documents, mode))
    results.append(check_minimum_bids(profile, threshold_tier, service_type, documents, mode))
    deviation = _deviation_step(profile, contract_value, invoice_value, mode)
    if deviation is not None:
        results.append(deviation)
    overall = _overall(results)
    report: dict[str, Any] = {
        "checks": results,
        "overall_status": overall,
        "timestamp": (now or datetime.now(UTC)).isoformat(),
    }
    if mode == "strict":
        report["mode"] = mode
        report["profile"] = profile.reference
    return report
