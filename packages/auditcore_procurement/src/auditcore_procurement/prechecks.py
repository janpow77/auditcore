"""Deterministic procurement prechecks over an explicitly selected, versioned profile.

Extraction of ``ProcurementPreChecker`` (AST-identical in
``janpow77/flowinvoice@fb2d185`` and ``janpow77/audit-portal@d8eefa4``) and
the ``threshold_rules``/``required_documents_by_procedure`` of the
``PROCUREMENT_HVTG`` ruleset. ``mode="legacy"`` reproduces the source results
exactly. ``mode="strict"`` applies the corrections listed in
``docs/behavior-changes.md`` (P-C01…P-C05, P-C10…P-C12); it never decides a
procurement case, it only reports rule results.

Profiles with schema 2 (``procurement.hvtg`` 2026.09.2) hold the EU thresholds
per validity period with their official source. In ``strict`` mode the EU
threshold is selected by the date of the measure/notice (``reference_date``) or
an explicit ``year``; a missing period yields ``REVIEW_REQUIRED``, never a
fallback to another period. National tiers remain application rules
(REVIEW_REQUIRED). ``legacy`` mode keeps the source table unchanged.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from importlib import resources
from typing import Any

PASS = "PASS"
WARNING = "WARNING"
FAIL = "FAIL"
NOT_APPLICABLE = "NOT_APPLICABLE"
NOT_CHECKED = "NOT_CHECKED"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
MODES = ("legacy", "strict")
AUTHORITY_TYPES = ("central", "sub_central")
SCHEMAS = ("auditcore_procurement.precheck-profile/1", "auditcore_procurement.precheck-profile/2")


class ProfileError(ValueError):
    """The precheck profile is missing or malformed."""


class ThresholdUnavailable(LookupError):
    """No verified EU threshold is recorded for the requested date/year."""


@dataclass(frozen=True)
class ThresholdPeriod:
    """EU thresholds valid from/to (inclusive) with their official source."""

    valid_from: date
    valid_to: date
    values: Mapping[str, int]
    source: Mapping[str, Any]


@dataclass(frozen=True)
class EuThreshold:
    """The EU threshold applicable to one case."""

    value: int
    key: str
    period: ThresholdPeriod

    def to_dict(self) -> dict[str, Any]:
        """JSON view recorded in strict results."""
        return {
            "value": self.value,
            "key": self.key,
            "valid_from": self.period.valid_from.isoformat(),
            "valid_to": self.period.valid_to.isoformat(),
            "regulation": self.period.source.get("regulation"),
            "official_journal": self.period.source.get("official_journal"),
        }


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
    eu_periods: tuple[ThresholdPeriod, ...] = ()
    eu_tier: str | None = None
    eu_categories: Mapping[str, Any] | None = None
    national_tiers: tuple[str, ...] = ()
    national_status: str = ""

    @property
    def reference(self) -> dict[str, str]:
        """Identity recorded in every result."""
        return {"id": self.id, "version": self.version, "fingerprint": self.fingerprint}


def profile_from_dict(data: Mapping[str, Any]) -> PrecheckProfile:
    """Validate and build a profile; nothing is defaulted silently."""
    try:
        if data["schema"] not in SCHEMAS:
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
        periods, eu_tier, eu_categories, national, national_status = _schema2(data, tiers)
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
            eu_periods=periods,
            eu_tier=eu_tier,
            eu_categories=eu_categories,
            national_tiers=national,
            national_status=national_status,
        )
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, ProfileError):
            raise
        raise ProfileError(f"Profil ist unvollständig oder fehlerhaft: {exc!r}") from exc


def _schema2(
    data: Mapping[str, Any], tiers: Mapping[str, tuple[Tier, ...]]
) -> tuple[tuple[ThresholdPeriod, ...], str | None, Mapping[str, Any] | None, tuple[str, ...], str]:
    """Validate the year-bound EU table and the national tier block of schema 2."""
    if data["schema"].endswith("/1"):
        return (), None, None, (), ""
    table = data["eu_thresholds"]
    periods: list[ThresholdPeriod] = []
    for row in table["periods"]:
        source = row["source"]
        if not all(source.get(k) for k in ("regulation", "official_journal", "url")):
            raise ProfileError("EU-Schwellenwert ohne amtliche Fundstelle.")
        start, end = date.fromisoformat(row["valid_from"]), date.fromisoformat(row["valid_to"])
        if end < start:
            raise ProfileError("Gültigkeitszeitraum endet vor seinem Beginn.")
        values = {str(k): int(v) for k, v in row["values"].items()}
        if any(v <= 0 for v in values.values()):
            raise ProfileError("EU-Schwellenwerte müssen positiv sein.")
        periods.append(ThresholdPeriod(start, end, values, dict(source)))
    periods.sort(key=lambda p: p.valid_from)
    for before, after in zip(periods, periods[1:], strict=False):
        if after.valid_from <= before.valid_to:
            raise ProfileError("EU-Schwellenwertzeiträume überschneiden sich.")
    categories = dict(table["categories"])
    keys = {k for p in periods for k in p.values}
    for category, spec in categories.items():
        wanted = spec.values() if isinstance(spec, Mapping) else [spec]
        if category not in tiers or not set(wanted) <= keys:
            raise ProfileError(f"EU-Schwellenwertzuordnung für '{category}' ist unvollständig.")
    eu_tier = str(table["tier"])
    national = data["national_tiers"]
    names = tuple(str(n) for n in national["tiers"])
    for rows in tiers.values():
        known = [t.name for t in rows]
        if eu_tier not in known or not set(names) <= set(known):
            raise ProfileError("Nationale Stufen oder EU-Stufe fehlen in der Stufentabelle.")
    return tuple(periods), eu_tier, categories, names, str(national["status"])


def _packaged_eu_block() -> dict[str, Any]:
    """EU table and national block of the packaged ``procurement.hvtg`` profile."""
    entry = resources.files("auditcore_procurement.profiles").joinpath(
        f"{CURRENT_PROFILE[0]}-{CURRENT_PROFILE[1]}.json"
    )
    data = json.loads(entry.read_text(encoding="utf-8"))
    return {"eu_thresholds": data["eu_thresholds"], "national_tiers": data["national_tiers"]}


CURRENT_PROFILE = ("procurement.hvtg", "2026.09.2")


def profile_from_ruleset(
    ruleset: Mapping[str, Any],
    *,
    profile_id: str,
    version: str,
    source: Mapping[str, Any],
    year_bound: bool = False,
) -> PrecheckProfile:
    """Profile from an application ruleset with ``threshold_rules`` and
    ``required_documents_by_procedure`` (source format), so a consumer keeps its
    own rule authority. Tier order and values are taken over unchanged.

    ``year_bound=True`` adds the verified year-bound EU table of the packaged
    ``procurement.hvtg`` profile for ``strict`` mode (schema 2); the ruleset's
    own ``BELOW_EU`` maxima are then used only by ``legacy`` mode."""
    try:
        tiers = {
            category: [
                {
                    "tier": name,
                    "max": rule.get("max"),
                    "procedure": rule.get("procedure", ""),
                    "min_bids": rule.get("min_bids", 1),
                }
                for name, rule in rules.items()
            ]
            for category, rules in ruleset["threshold_rules"].items()
        }
        required = ruleset["required_documents_by_procedure"]
    except (KeyError, AttributeError, TypeError) as exc:
        raise ProfileError(f"Regelwerk ohne threshold_rules/required_documents: {exc!r}") from exc
    extra = _packaged_eu_block() if year_bound else {}
    return profile_from_dict(
        {
            "schema": f"auditcore_procurement.precheck-profile/{2 if year_bound else 1}",
            **extra,
            "id": profile_id,
            "version": version,
            "status": "CONSUMER_RULESET",
            "legal_status": "Regelwerk der Anwendung; nicht durch diese Bibliothek geprüft.",
            "source": dict(source),
            "construction_marker": "Bau",
            "tiers": tiers,
            "fallback_tier": "ABOVE_EU",
            "required_documents": {k: list(v) for k, v in required.items()},
            "bid_document_type": "ANGEBOT",
            "default_min_bids": 1,
            "value_deviation": {
                "warning_above_percent": 10,
                "fail_above_percent": 20,
                "fail_reference": "§ 132 GWB",
            },
        }
    )


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


def eu_period(profile: PrecheckProfile, on: date) -> ThresholdPeriod:
    """Verified period containing ``on``; no fallback to a neighbouring period.

    Raises:
        ThresholdUnavailable: the profile has no year-bound table or no period for ``on``.
    """
    if not profile.eu_periods:
        raise ThresholdUnavailable(
            f"Profil {profile.id} {profile.version} enthält keine jahresbezogenen "
            "EU-Schwellenwerte."
        )
    for period in profile.eu_periods:
        if period.valid_from <= on <= period.valid_to:
            return period
    raise ThresholdUnavailable(
        f"Für den {on.strftime('%d.%m.%Y')} ist im Profil {profile.id} {profile.version} "
        "kein belegter EU-Schwellenwert hinterlegt."
    )


def eu_period_for_year(profile: PrecheckProfile, year: int) -> ThresholdPeriod:
    """Period covering the whole calendar ``year``, else ``ThresholdUnavailable``."""
    period = eu_period(profile, date(year, 1, 1))
    if period.valid_to < date(year, 12, 31):
        raise ThresholdUnavailable(f"Das Jahr {year} liegt nicht vollständig in einem Zeitraum.")
    return period


def eu_threshold(
    profile: PrecheckProfile, category: str, period: ThresholdPeriod, authority_type: str
) -> EuThreshold:
    """Threshold of a category (``construction``/``supply_service``) and authority type."""
    if profile.eu_categories is None or category not in profile.eu_categories:
        raise ThresholdUnavailable(f"Keine EU-Schwellenwertzuordnung für '{category}'.")
    spec = profile.eu_categories[category]
    if isinstance(spec, Mapping):
        if authority_type not in AUTHORITY_TYPES:
            raise ValueError(f"authority_type muss eine von {AUTHORITY_TYPES} sein.")
        spec = spec[authority_type]
    key = str(spec)
    return EuThreshold(period.values[key], key, period)


def _strict_threshold(
    profile: PrecheckProfile,
    estimated_value: Decimal,
    category: str,
    threshold_tier: str | None,
    reference_date: date | None,
    year: int | None,
    authority_type: str | None,
) -> dict[str, Any]:
    """Tier with the EU threshold of the case's period (reached or exceeded = above EU)."""
    name = "Schwellenwert-Klassifikation"
    if profile.eu_tier is None:
        return _result(
            "precheck_threshold",
            name,
            REVIEW_REQUIRED,
            f"Profil {profile.id} {profile.version} hat keine jahresbezogenen "
            "EU-Schwellenwerte; bitte procurement.hvtg verwenden.",
        )
    if authority_type is not None and authority_type not in AUTHORITY_TYPES:
        raise ValueError(f"authority_type muss eine von {AUTHORITY_TYPES} oder None sein.")
    if reference_date is None and year is None:
        return _result(
            "precheck_threshold",
            name,
            REVIEW_REQUIRED,
            "Stichtag fehlt: Datum der Maßnahme/Bekanntmachung oder Jahr angeben; "
            "der EU-Schwellenwert gilt je Zeitraum.",
        )
    try:
        period = (
            eu_period(profile, reference_date)
            if reference_date is not None
            else eu_period_for_year(profile, int(year or 0))
        )
    except ThresholdUnavailable as exc:
        return _result("precheck_threshold", name, REVIEW_REQUIRED, str(exc))
    value = float(estimated_value)
    candidates = (
        {t: eu_threshold(profile, category, period, t) for t in AUTHORITY_TYPES}
        if isinstance((profile.eu_categories or {}).get(category), Mapping)
        else {"": eu_threshold(profile, category, period, "sub_central")}
    )
    if authority_type is not None and "" not in candidates:
        threshold = candidates[authority_type]
    else:
        limits = sorted(candidates.values(), key=lambda c: c.value)
        if len(limits) > 1 and limits[0].value <= value < limits[-1].value:
            return _result(
                "precheck_threshold",
                name,
                REVIEW_REQUIRED,
                f"Der Auftragswert {estimated_value} EUR liegt zwischen den "
                f"EU-Schwellenwerten für zentrale ({limits[0].value} EUR) und "
                f"sonstige Auftraggeber ({limits[-1].value} EUR); Art des "
                "Auftraggebers (authority_type) angeben.",
                eu_thresholds=[c.to_dict() for c in limits],
            )
        threshold = limits[-1] if value >= limits[-1].value else limits[0]
    calculated = next(
        (
            t.name
            for t in profile.tiers.get(category, ())
            if t.name in profile.national_tiers and t.maximum is not None and value <= t.maximum
        ),
        None,
    )
    if calculated is None:
        calculated = profile.eu_tier if value < threshold.value else profile.fallback_tier
    extra = {
        "calculated_tier": calculated,
        "eu_threshold": threshold.to_dict(),
        "national_tiers_status": profile.national_status,
    }
    if threshold_tier and threshold_tier != calculated:
        return _result(
            "precheck_threshold",
            name,
            FAIL,
            f"Schwellenwert-Stufe '{threshold_tier}' stimmt nicht mit berechnetem Wert "
            f"'{calculated}' überein (Auftragswert: {estimated_value} EUR, "
            f"EU-Schwellenwert {threshold.value} EUR gültig "
            f"{threshold.period.valid_from:%d.%m.%Y}–{threshold.period.valid_to:%d.%m.%Y}).",
            **extra,
        )
    return _result(
        "precheck_threshold",
        name,
        PASS,
        f"Schwellenwert korrekt: {calculated} ({estimated_value} EUR; EU-Schwellenwert "
        f"{threshold.value} EUR, {threshold.period.source.get('regulation')}).",
        **extra,
    )


def check_threshold(
    profile: PrecheckProfile,
    estimated_value: Decimal | None,
    service_type: str,
    threshold_tier: str | None,
    mode: str = "legacy",
    *,
    reference_date: date | None = None,
    year: int | None = None,
    authority_type: str | None = None,
) -> dict[str, Any]:
    """Tier from the estimated value.

    ``legacy``: inclusive maxima of the source table in profile order.
    ``strict``: national tiers from the profile, then the EU threshold of the
    period of ``reference_date``/``year`` (schema 2 profiles only).
    """
    name = "Schwellenwert-Klassifikation"
    if _missing(estimated_value, mode):
        return _result(
            "precheck_threshold", name, WARNING, "Kein geschaetzter Auftragswert angegeben."
        )
    assert estimated_value is not None
    category = _category(profile, service_type)
    if mode == "strict":
        return _strict_threshold(
            profile, estimated_value, category, threshold_tier, reference_date, year, authority_type
        )
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


def _deviation_step(
    profile: PrecheckProfile,
    contract_value: Decimal | None,
    invoice_value: Decimal | None,
    mode: str,
) -> dict[str, Any] | None:
    """Value deviation if both values are given; strict reports a single missing value."""
    if mode == "strict":
        if contract_value is not None and invoice_value is not None:
            return check_value_deviation(profile, contract_value, invoice_value)
        if (contract_value is None) != (invoice_value is None):
            return _result(
                "precheck_value_deviation",
                "Wertabweichung",
                NOT_CHECKED,
                "Vertrags- oder Abrechnungswert fehlt.",
            )
        return None
    if contract_value and invoice_value:
        return check_value_deviation(profile, contract_value, invoice_value)
    return None


def _overall(results: Sequence[Mapping[str, Any]]) -> str:
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
    documents: Sequence[Mapping[str, Any]],
    *,
    mode: str = "legacy",
    now: datetime | None = None,
    reference_date: date | None = None,
    year: int | None = None,
    authority_type: str | None = None,
) -> dict[str, Any]:
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
