"""Where the list inventory comes from and how current it is (Quellenstand).

The consumer owns loading and storing lists (for example with the harvest
adapters of this package); the review API asks a :class:`SnapshotProvider`
for the state and for the snapshots of a run. ``as_of`` is the state of the
list as stated by the source, not the time of loading. Without ``as_of`` the
state is *unknown*, never assumed current.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from ..model import ListSnapshot, SanctionsList
from .contract import KINDS

FRESH_CURRENT = "current"
FRESH_STALE = "stale"
FRESH_UNKNOWN = "unknown"
FRESH_NOT_JUDGED = "not_judged"
FRESHNESS_LABELS = {
    FRESH_CURRENT: "aktuell",
    FRESH_STALE: "veraltet",
    FRESH_UNKNOWN: "Stand unbekannt",
    FRESH_NOT_JUDGED: "nicht bewertet",
}


@dataclass(frozen=True)
class SourceState:
    """State of one list without its entries."""

    list: SanctionsList
    kind: str
    entry_count: int
    as_of: str | None
    retrieved_at: str | None = None
    content_sha256: str | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"Unbekannte Quellenart {self.kind!r}.")


class SnapshotProvider(Protocol):
    """What the review API needs from the consumer's list inventory."""

    def states(self) -> Sequence[SourceState]:
        """State of every list that can be screened."""
        ...

    def snapshots(self, list_keys: Sequence[str]) -> Sequence[ListSnapshot]:
        """Snapshots of the named lists, in that order; an empty one means *not searched*."""
        ...


class StaticSnapshotProvider:
    """Provider over snapshots held in memory (tests, demos, small deployments)."""

    def __init__(self, snapshots: Sequence[tuple[str, ListSnapshot]]) -> None:
        self._items = {snap.list.key: (kind, snap) for kind, snap in snapshots}
        for kind, _snap in self._items.values():
            if kind not in KINDS:
                raise ValueError(f"Unbekannte Quellenart {kind!r}.")

    def states(self) -> Sequence[SourceState]:
        """States derived from the snapshots."""
        return tuple(
            SourceState(
                list=snap.list,
                kind=kind,
                entry_count=len(snap.entries),
                as_of=snap.as_of,
                retrieved_at=snap.retrieved_at,
                content_sha256=snap.content_sha256,
                note=snap.note,
            )
            for kind, snap in self._items.values()
        )

    def snapshots(self, list_keys: Sequence[str]) -> Sequence[ListSnapshot]:
        """The held snapshots of the named lists."""
        return tuple(self._items[key][1] for key in list_keys)


def parse_instant(value: str | None) -> datetime | None:
    """ISO date or timestamp → aware datetime (dates at midnight UTC); else ``None``."""
    if not value:
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def freshness(as_of: str | None, now: datetime, stale_after_days: float | None) -> dict[str, Any]:
    """Age of a list state and its judgement against the configured maximum age."""
    instant = parse_instant(as_of)
    if instant is None:
        status = FRESH_UNKNOWN
        age = None
    else:
        age = round((now - instant).total_seconds() / 86400, 1)
        if stale_after_days is None:
            status = FRESH_NOT_JUDGED
        else:
            status = FRESH_STALE if age > stale_after_days else FRESH_CURRENT
    return {
        "status": status,
        "label": FRESHNESS_LABELS[status],
        "age_days": age,
        "stale_after_days": stale_after_days,
    }


def state_view(state: SourceState, now: datetime, stale_after_days: float | None) -> dict[str, Any]:
    """JSON view of a list state including licence and freshness."""
    return {
        "list": state.list.to_dict(),
        "kind": state.kind,
        "entry_count": state.entry_count,
        "as_of": state.as_of,
        "retrieved_at": state.retrieved_at,
        "content_sha256": state.content_sha256,
        "note": state.note,
        "searchable": state.entry_count > 0,
        "freshness": freshness(state.as_of, now, stale_after_days),
    }
