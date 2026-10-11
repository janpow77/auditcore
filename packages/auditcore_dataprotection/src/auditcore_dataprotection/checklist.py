"""Persistent checklist (CHK-01 to CHK-30) with status, owner, evidence and due date.

The checklist is not a second tick system: its items are stored in the
register activity (``pruefpunkte``) next to the answers they are about, so the
wizard, the checklist, the register export and the DPIA report read the same
versioned record. Answering a question never marks an item as done.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date, datetime
from enum import StrEnum
from importlib.resources import files

from .errors import ConflictError, ValidationError
from .evidence import Evidence, EvidenceKind, evidence_problem


class ItemStatus(StrEnum):
    """Status model of one checklist item."""

    OPEN = "offen"
    IN_PROGRESS = "in_bearbeitung"
    FOR_REVIEW = "zur_pruefung"
    PROVEN = "nachgewiesen"
    CLARIFICATION = "klaerungsbedarf"
    NOT_MET = "nicht_erfuellt"
    NOT_APPLICABLE = "nicht_anwendbar"
    RECHECK = "erneut_zu_pruefen"


#: Statuses that count as settled (no open work left).
SETTLED = frozenset({ItemStatus.PROVEN, ItemStatus.NOT_APPLICABLE})


@dataclass(frozen=True)
class ChecklistDefinition:
    """One item of the catalogue."""

    id: str
    area: str
    title: str
    owner_role: str
    essential: bool = True
    evidence_kinds: frozenset[EvidenceKind] = frozenset()
    blocks: str = ""


def _load_catalog() -> tuple[ChecklistDefinition, ...]:
    """Packaged catalogue (data, not code); CHK ids are stable."""
    raw = json.loads(
        files("auditcore_dataprotection.catalogs")
        .joinpath(CATALOG_FILE)
        .read_text(encoding="utf-8")
    )
    return tuple(
        ChecklistDefinition(
            id=str(entry["id"]),
            area=str(entry["area"]),
            title=str(entry["title"]),
            owner_role=str(entry["owner_role"]),
            essential=bool(entry["essential"]),
            evidence_kinds=frozenset(EvidenceKind(k) for k in entry["evidence_kinds"]),
            blocks=str(entry["blocks"]),
        )
        for entry in raw["items"]
    )


CATALOG_FILE = "checklist-2026.10.1.json"
CATALOG: tuple[ChecklistDefinition, ...] = _load_catalog()
_BY_ID = {d.id: d for d in CATALOG}


def definition(item_id: str) -> ChecklistDefinition:
    """Catalogue entry or ``ValidationError`` for an unknown id."""
    try:
        return _BY_ID[item_id]
    except KeyError as exc:
        raise ValidationError(f"Unbekannter Prüfpunkt „{item_id}“.") from exc


@dataclass(frozen=True)
class ChecklistItem:
    """State of one checklist item inside a register version."""

    id: str
    status: ItemStatus = ItemStatus.OPEN
    owner: str = ""
    due: str = ""
    evidence_ids: tuple[str, ...] = ()
    justification: str = ""
    objection: str = ""
    updated_by: str = ""
    updated_at: str = ""
    confirmed_by: str = ""

    @classmethod
    def from_dict(cls, item_id: str, raw: Mapping[str, object]) -> ChecklistItem:
        """Validated item from JSON data."""
        definition(item_id)
        try:
            status = ItemStatus(str(raw.get("status", ItemStatus.OPEN.value)))
        except ValueError as exc:
            raise ValidationError(f"{item_id}: unbekannter Status „{raw.get('status')}“.") from exc
        ids = raw.get("evidence_ids") or []
        if not isinstance(ids, list):
            raise ValidationError(f"{item_id}: „evidence_ids“ muss eine Liste sein.")
        text = {k: str(raw.get(k) or "") for k in _TEXT_KEYS}
        return cls(item_id, status, evidence_ids=tuple(str(i) for i in ids), **text)

    def to_dict(self) -> dict[str, object]:
        """JSON form stored in ``pruefpunkte``."""
        return {
            "status": self.status.value,
            "evidence_ids": list(self.evidence_ids),
            **{k: getattr(self, k) for k in _TEXT_KEYS},
        }


_TEXT_KEYS = (
    "owner",
    "due",
    "justification",
    "objection",
    "updated_by",
    "updated_at",
    "confirmed_by",
)


def items_from_data(raw: object) -> dict[str, ChecklistItem]:
    """All 30 items; missing ones are ``offen`` (never silently settled)."""
    if raw is not None and not isinstance(raw, Mapping):
        raise ValidationError("„pruefpunkte“ muss eine Zuordnung sein.")
    stored = dict(raw or {})
    result: dict[str, ChecklistItem] = {}
    for entry in CATALOG:
        value = stored.pop(entry.id, None)
        if value is not None and not isinstance(value, Mapping):
            raise ValidationError(f"{entry.id}: Eintrag muss eine Zuordnung sein.")
        result[entry.id] = (
            ChecklistItem(entry.id) if value is None else ChecklistItem.from_dict(entry.id, value)
        )
    if stored:
        raise ValidationError(f"Unbekannte Prüfpunkte: {', '.join(sorted(stored))}.")
    return result


@dataclass(frozen=True)
class Transition:
    """Requested change of one item."""

    status: ItemStatus
    actor: str
    at: datetime
    justification: str = ""
    evidence_ids: tuple[str, ...] = ()
    owner: str | None = None
    due: str | None = None
    objection: str | None = None


def _check_proven(
    item_id: str, evidence_ids: Sequence[str], catalog: Mapping[str, Evidence], today: date
) -> None:
    """ "Nachgewiesen" names concrete, usable evidence of an accepted kind (T-21, T-36)."""
    if not evidence_ids:
        raise ValidationError(f"{item_id}: „nachgewiesen“ braucht einen konkreten Nachweis.")
    kinds = definition(item_id).evidence_kinds
    for evidence_id in evidence_ids:
        if evidence_id not in catalog:
            raise ValidationError(f"{item_id}: Nachweis {evidence_id} ist nicht erfasst.")
        evidence = catalog[evidence_id]
        problem = evidence_problem(evidence, today)
        if problem:
            raise ValidationError(f"{item_id}: {problem}")
        if kinds and evidence.kind not in kinds:
            allowed = ", ".join(sorted(k.value for k in kinds))
            raise ValidationError(
                f"{item_id}: Nachweisart „{evidence.kind.value}“ trägt diesen Prüfpunkt nicht; "
                f"zulässig: {allowed}."
            )


def apply_transition(
    item: ChecklistItem,
    change: Transition,
    catalog: Mapping[str, Evidence],
    min_justification: int,
) -> ChecklistItem:
    """Validated new state of an item; "nicht anwendbar" needs a justification."""
    if change.status is ItemStatus.PROVEN:
        _check_proven(item.id, change.evidence_ids, catalog, change.at.date())
    if change.status in (ItemStatus.NOT_APPLICABLE, ItemStatus.NOT_MET) and (
        len(change.justification.strip()) < min_justification
    ):
        raise ValidationError(
            f"{item.id}: „{change.status.value}“ braucht eine Begründung von mindestens "
            f"{min_justification} Zeichen."
        )
    return replace(
        item,
        status=change.status,
        evidence_ids=change.evidence_ids or item.evidence_ids,
        justification=change.justification.strip() or item.justification,
        owner=item.owner if change.owner is None else change.owner,
        due=item.due if change.due is None else change.due,
        objection=item.objection if change.objection is None else change.objection,
        updated_by=change.actor,
        updated_at=change.at.isoformat(),
        confirmed_by="",
    )


def confirm_not_applicable(item: ChecklistItem, actor: str) -> ChecklistItem:
    """Second person confirms "nicht anwendbar" of an essential item."""
    if item.status is not ItemStatus.NOT_APPLICABLE:
        raise ConflictError(f"{item.id}: nur „nicht anwendbar“ wird gesondert bestätigt.")
    if actor == item.updated_by:
        raise ConflictError(f"{item.id}: Die Bestätigung muss eine zweite Person geben.")
    return replace(item, confirmed_by=actor)


def settled(item: ChecklistItem) -> bool:
    """Settled: proven, or not applicable with the required confirmation."""
    if item.status is ItemStatus.PROVEN:
        return True
    if item.status is ItemStatus.NOT_APPLICABLE:
        return bool(item.confirmed_by) or not definition(item.id).essential
    return False


def filter_items(
    items: Mapping[str, ChecklistItem],
    *,
    owner: str | None = None,
    blocking_only: bool = False,
    missing_evidence: bool = False,
    recheck_only: bool = False,
) -> tuple[ChecklistItem, ...]:
    """Views of the work list: mine, blocking, evidence missing, changed since review."""
    result = []
    for item in items.values():
        if owner is not None and item.owner != owner:
            continue
        if blocking_only and (settled(item) or not definition(item.id).blocks):
            continue
        if missing_evidence and (item.evidence_ids or settled(item)):
            continue
        if recheck_only and item.status is not ItemStatus.RECHECK:
            continue
        result.append(item)
    return tuple(result)


def reopen(
    items: Mapping[str, ChecklistItem], item_ids: Sequence[str], reason: str, at: datetime
) -> dict[str, ChecklistItem]:
    """Mark settled or reviewed items as "erneut zu prüfen" after a relevant change."""
    result = dict(items)
    for item_id in item_ids:
        item = result[item_id]
        if item.status in (ItemStatus.PROVEN, ItemStatus.FOR_REVIEW, ItemStatus.NOT_APPLICABLE):
            result[item_id] = replace(
                item,
                status=ItemStatus.RECHECK,
                objection=reason,
                updated_by="system",
                updated_at=at.isoformat(),
                confirmed_by="",
            )
    return result
