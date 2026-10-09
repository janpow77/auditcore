"""Evidence and safeguards: what is proven, what is only planned.

A tick is no proof. Evidence names its kind, a reference to the protected
document (never the document itself), its version, when and by whom it was
checked and whether it is still reachable. A safeguard only counts as
effective with the state ``wirksam_nachgewiesen`` and at least one usable
piece of evidence; planned measures never lower the proven residual risk.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date
from enum import StrEnum

from .errors import ValidationError
from .model import Assessment
from .results import RiskResult
from .risk import assess_risk
from .rules import RuleProfile


class EvidenceKind(StrEnum):
    """Kinds of evidence; the kind decides which checklist item it can prove."""

    CONCEPT = "konzept"
    TEST = "test"
    CONTRACT = "vertrag"
    STATEMENT = "stellungnahme"
    PROCESSING_LOG = "fachprotokoll"
    REGISTER_HISTORY = "vvt_historie"
    OPERATIONS = "betriebsnachweis"
    DECISION = "entscheidung"
    OTHER = "sonstiges"


class SafeguardState(StrEnum):
    """Implementation state of one safeguard."""

    NOT_STARTED = "nicht_begonnen"
    PLANNED = "geplant"
    IMPLEMENTED = "umgesetzt"
    EFFECTIVE = "wirksam_nachgewiesen"
    NOT_APPLICABLE = "nicht_anwendbar"


@dataclass(frozen=True)
class Evidence:
    """Reference to a protected document that proves something."""

    id: str
    kind: EvidenceKind
    reference: str
    version: str
    checked_on: date | None = None
    checked_by: str | None = None
    valid_until: date | None = None
    available: bool = True
    protection: str = "intern"

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> Evidence:
        """Validated evidence from JSON data; unknown kinds are rejected."""
        try:
            kind = EvidenceKind(str(raw.get("kind")))
        except ValueError as exc:
            raise ValidationError(f"Unbekannte Nachweisart „{raw.get('kind')}“.") from exc
        reference = str(raw.get("reference") or "").strip()
        if not reference or not str(raw.get("id") or "").strip():
            raise ValidationError("Ein Nachweis braucht Kennung und Fundstelle.")
        return cls(
            id=str(raw["id"]),
            kind=kind,
            reference=reference,
            version=str(raw.get("version") or ""),
            checked_on=_date(raw.get("checked_on")),
            checked_by=_text(raw.get("checked_by")),
            valid_until=_date(raw.get("valid_until")),
            available=raw.get("available", True) is not False,
            protection=str(raw.get("protection") or "intern"),
        )

    def to_dict(self) -> dict[str, object]:
        """JSON form stored in the register version."""
        return {
            "id": self.id,
            "kind": self.kind.value,
            "reference": self.reference,
            "version": self.version,
            "checked_on": None if self.checked_on is None else self.checked_on.isoformat(),
            "checked_by": self.checked_by,
            "valid_until": None if self.valid_until is None else self.valid_until.isoformat(),
            "available": self.available,
            "protection": self.protection,
        }


def _text(value: object) -> str | None:
    return value.strip() or None if isinstance(value, str) else None


def _date(value: object) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValidationError(f"Ungültiges Datum „{value}“ (JJJJ-MM-TT).") from exc


def evidence_problem(evidence: Evidence, today: date) -> str | None:
    """Why the evidence cannot carry a "proven" status, or ``None`` (T-36)."""
    if not evidence.available:
        return f"Nachweis {evidence.id} ist nicht mehr zugänglich."
    if not evidence.version:
        return f"Nachweis {evidence.id} nennt keine Version."
    if evidence.checked_on is None or not evidence.checked_by:
        return f"Nachweis {evidence.id} ist nicht geprüft (Prüfdatum und prüfende Rolle fehlen)."
    if evidence.valid_until is not None and evidence.valid_until < today:
        return f"Nachweis {evidence.id} ist seit {evidence.valid_until.isoformat()} veraltet."
    return None


def usable(evidence_ids: Sequence[str], catalog: Mapping[str, Evidence], today: date) -> bool:
    """True if at least one referenced evidence exists and has no problem."""
    return any(e in catalog and evidence_problem(catalog[e], today) is None for e in evidence_ids)


@dataclass(frozen=True)
class Safeguard:
    """A measure with its state, the risks it addresses and its evidence."""

    key: str
    state: SafeguardState
    evidence_ids: tuple[str, ...] = ()
    owner: str = ""
    justification: str = ""

    def effective(self, catalog: Mapping[str, Evidence], today: date) -> bool:
        """Only proven effectiveness with usable evidence counts (T-12, GATE-06)."""
        return self.state is SafeguardState.EFFECTIVE and usable(self.evidence_ids, catalog, today)


def safeguards_from_data(raw: object) -> dict[str, Safeguard]:
    """Safeguards of an activity (``schutzmassnahmen``), validated JSON data."""
    if raw is None:
        return {}
    if not isinstance(raw, list):
        raise ValidationError("„schutzmassnahmen“ muss eine Liste sein.")
    result: dict[str, Safeguard] = {}
    for entry in raw:
        if not isinstance(entry, Mapping) or not str(entry.get("key") or "").strip():
            raise ValidationError("Jede Schutzmaßnahme braucht einen Schlüssel.")
        try:
            state = SafeguardState(str(entry.get("state")))
        except ValueError as exc:
            raise ValidationError(
                f"Unbekannter Umsetzungsstand „{entry.get('state')}“ der Maßnahme "
                f"{entry.get('key')}."
            ) from exc
        ids = entry.get("evidence_ids") or []
        if not isinstance(ids, list):
            raise ValidationError("„evidence_ids“ muss eine Liste sein.")
        key = str(entry["key"])
        result[key] = Safeguard(
            key,
            state,
            tuple(str(i) for i in ids),
            str(entry.get("owner") or ""),
            str(entry.get("justification") or ""),
        )
    return result


@dataclass(frozen=True)
class ProvenRisk:
    """Residual risk with all measures versus only proven-effective measures."""

    claimed: RiskResult
    proven: RiskResult
    unproven_measures: tuple[str, ...]

    @property
    def planned_effect_only(self) -> bool:
        """True if the claimed risk relies on measures that are not proven effective."""
        return self.claimed.net_maximum < self.proven.net_maximum


def proven_risk(
    profile: RuleProfile,
    assessment: Assessment,
    safeguards: Mapping[str, Safeguard],
    catalog: Mapping[str, Evidence],
    today: date,
) -> ProvenRisk:
    """Re-assess the scenarios with only effective safeguards (T-12)."""
    unproven: set[str] = set()
    reduced = []
    for scenario in assessment.scenarios:
        kept = tuple(
            m
            for m in scenario.measures
            if m in safeguards and safeguards[m].effective(catalog, today)
        )
        unproven.update(m for m in scenario.measures if m not in kept)
        reduced.append(
            replace(scenario, measures=kept, residual_severity=None, residual_likelihood=None)
        )
    claimed = assess_risk(profile, [s.to_dict() for s in assessment.scenarios])
    proven = assess_risk(profile, [s.to_dict() for s in reduced])
    return ProvenRisk(claimed, proven, tuple(sorted(unproven)))


def evidence_from_data(raw: object) -> dict[str, Evidence]:
    """Evidence catalogue of an activity (``nachweise``), validated JSON data."""
    if raw is None:
        return {}
    if not isinstance(raw, list):
        raise ValidationError("„nachweise“ muss eine Liste sein.")
    catalog: dict[str, Evidence] = {}
    for entry in raw:
        if not isinstance(entry, Mapping):
            raise ValidationError("Jeder Nachweis muss eine Zuordnung sein.")
        item = Evidence.from_dict(entry)
        if item.id in catalog:
            raise ValidationError(f"Doppelte Nachweiskennung {item.id}.")
        catalog[item.id] = item
    return catalog
