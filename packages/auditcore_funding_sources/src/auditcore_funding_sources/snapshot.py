"""Inventory semantics of the four flowworkshop harvest modes, as a database-free plan.

The modes are **not** parser options. They describe what happens to the stored
records of one source; the consumer executes the plan inside one transaction:

* ``smart``: insert rows with new identities, skip known identities. A changed
  row gets a new identity and is inserted *in addition*; the old one stays.
* ``full-refresh``: insert new identities, overwrite known ones.
* ``force`` and ``snapshot``: delete every stored record of the source, then
  insert the file; a repeated identity within the file is skipped. Both have
  the same effect on the inventory; ``force`` additionally reports the
  deletion as run message.

The whole file is parsed and validated before any deletion; a rejected
snapshot leaves the inventory untouched. Counters follow the source exactly,
including its quirks (FS-W06/W07): nameless rows count as ``failed`` and turn
the run status into ``partial``; ``full-refresh`` counts overwritten rows as
``inserted``.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from .errors import SnapshotRejected
from .workshop import MODES, SnapshotContext, compute_record_hash, filter_by_fund, validate_rows


@dataclass(frozen=True)
class SnapshotPlan:
    """What a harvest run does to the stored records of one source."""

    source_key: str
    mode: str
    delete_all_first: bool
    inserts: tuple[tuple[str, Mapping[str, Any]], ...]
    updates: tuple[tuple[str, Mapping[str, Any]], ...]
    skipped: tuple[str, ...]
    failed_rows: tuple[int, ...]
    removed_other_fund: int
    records_seen: int
    records_inserted: int
    records_skipped: int
    records_failed: int
    status: str
    message: str | None = None
    deleted_count: int = 0
    notes: tuple[str, ...] = field(default_factory=tuple)

    def resulting_identities(self, stored: Iterable[str]) -> list[str]:
        """Identities of the source after executing the plan."""
        base = set() if self.delete_all_first else set(stored)
        return sorted(base | {identity for identity, _ in self.inserts})


def plan_snapshot(
    rows: Sequence[Mapping[str, Any]],
    context: SnapshotContext,
    *,
    mode: str,
    stored_identities: Iterable[str],
) -> SnapshotPlan:
    """Validate a parsed file and derive the mode-specific plan.

    Raises:
        ValueError: unknown mode, or no row with a beneficiary name.
        SnapshotRejected: validation errors; nothing may be deleted.
    """
    if not context.source_key:
        raise ValueError("source_key ist Pflicht.")
    if mode not in MODES:
        raise ValueError("mode muss smart|full-refresh|force|snapshot sein.")
    kept, removed = filter_by_fund(list(rows), context.fonds)
    valid = [r for r in kept if not r.get("_skip_reason")]
    if not valid:
        raise ValueError("Keine valide Begünstigtenzeile bzw. keine Namensspalte erkannt.")
    errors = validate_rows(kept, context)
    if errors:
        raise SnapshotRejected(errors)
    stored = set(stored_identities)
    delete_first = mode in ("force", "snapshot")
    present: set[str] = set() if delete_first else set(stored)
    inserts: list[tuple[str, Mapping[str, Any]]] = []
    updates: list[tuple[str, Mapping[str, Any]]] = []
    skipped: list[str] = []
    failed: list[int] = []
    inserted_count = 0
    for row in kept:
        if row.get("_skip_reason"):
            failed.append(int(row.get("_row_number") or 0))
            continue
        identity = compute_record_hash(row, context.source_key)
        if identity in present:
            if mode == "full-refresh":
                updates.append((identity, row))
                inserted_count += 1
            else:
                skipped.append(identity)
            continue
        present.add(identity)
        inserts.append((identity, row))
        inserted_count += 1
    deleted = len(stored) if delete_first else 0
    message = (
        f"force-mode: {deleted} bestehende Records vorab geloescht."
        if mode == "force" and deleted
        else None
    )
    notes = []
    if failed:
        notes.append(
            f"{len(failed)} Zeile(n) ohne Begünstigtennamen (etwa Summen- oder Leerzeilen) sind als "
            "failed gezählt; der Laufstatus lautet deshalb partial."
        )
    return SnapshotPlan(
        source_key=context.source_key,
        mode=mode,
        delete_all_first=delete_first,
        inserts=tuple(inserts),
        updates=tuple(updates),
        skipped=tuple(skipped),
        failed_rows=tuple(failed),
        removed_other_fund=removed,
        records_seen=len(kept),
        records_inserted=inserted_count,
        records_skipped=len(skipped),
        records_failed=len(failed),
        status="ok" if not failed else "partial",
        message=message,
        deleted_count=deleted,
        notes=tuple(notes),
    )
