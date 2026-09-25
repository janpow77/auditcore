"""De-minimis register inventory: record identities and reconciliation of one harvest.

Part of the source profile ``designer.deminimis.register`` (source
``de_minimis_ernte.py``); :mod:`auditcore_funding_sources.deminimis` re-exports
every name here. Database-free: the consumer applies the outcome.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

HASH_FIELDS = (
    "referenceNumber",
    "beneficiaryName",
    "beneficiaryReferenceNumber",
    "amountEur",
    "grantingDate",
    "deMinimisType",
    "grantingAuthorityName",
    "sector",
    "instrument",
    "country",
)


def record_hash(record: Mapping[str, object]) -> str:
    """SHA-256 over the content fields of a register record (change detection)."""
    canonical = json.dumps(
        {f: record.get(f) for f in HASH_FIELDS},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def inventory_hash(hashes: Iterable[str]) -> str:
    """SHA-256 over the sorted record hashes of one run."""
    return hashlib.sha256("".join(sorted(hashes)).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Inventory reconciliation (source semantics, no database)
# ---------------------------------------------------------------------------


@dataclass
class Reconciliation:
    """Outcome of one harvest over the pages that were actually received."""

    reported: int | None = None
    seen: dict[str, str] = field(default_factory=dict)
    inserted: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    skipped_without_reference: int = 0
    requests: int = 0
    error: str | None = None
    vanished: list[str] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        """Only a run that saw at least the reported total without error is complete."""
        return self.error is None and self.reported is not None and len(self.seen) >= self.reported

    @property
    def status(self) -> str:
        """``ok``, ``partial`` or ``failed`` exactly as in the source."""
        if self.complete:
            return "ok"
        return "failed" if self.error else "partial"

    @property
    def content_hash(self) -> str:
        """Inventory hash over the records seen in this run."""
        return inventory_hash(self.seen.values())


def reconcile_page(
    state: Reconciliation,
    rows: Sequence[Mapping[str, Any]],
    reported: int | None,
    stored: Mapping[str, str],
) -> bool:
    """Apply one received page; returns whether another page is required.

    ``stored`` maps reference numbers to the stored content hash (``None``
    entries mean unknown). Records without reference number are skipped and
    counted. Order and counters follow ``de_minimis_ernte.ernte``.
    """
    state.requests += 1
    state.reported = reported
    if not rows:
        return False
    for record in rows:
        reference = record.get("referenceNumber")
        if not reference:
            state.skipped_without_reference += 1
            continue
        digest = record_hash(record)
        key = str(reference)
        # A reference repeated within the run compares with the value just written.
        previous = state.seen[key] if key in state.seen else stored.get(key)
        state.seen[key] = digest
        if previous is None:
            state.inserted.append(key)
        elif previous != digest:
            state.updated.append(key)
        else:
            state.unchanged.append(key)
    return not (reported is not None and len(state.seen) >= reported)


def mark_vanished(state: Reconciliation, active_references: Iterable[str]) -> list[str]:
    """References to mark as vanished — only after a complete run, never after a partial one."""
    if not state.complete:
        state.vanished = []
        return []
    state.vanished = sorted(r for r in active_references if r not in state.seen)
    return state.vanished


def inventory_state(
    runs: Sequence[Mapping[str, Any]], active: int, vanished: int, *, legacy: bool = False
) -> dict[str, Any]:
    """What the inventory says about itself.

    ``legacy=True`` reproduces ``bestandsstand``: it reports the last *ok* run
    as current and ``vollstaendig=True`` even when a newer failed or partial
    run already changed stored rows (FS-D02). The corrected form reports the
    newest run and is complete only if that newest run is ``ok``.
    """
    ordered = sorted(runs, key=lambda r: str(r.get("started_at") or ""), reverse=True)
    last_ok = next((r for r in ordered if r.get("status") == "ok"), None)
    newest = ordered[0] if ordered else None
    if legacy:
        return {
            "stand_am": last_ok.get("finished_at") if last_ok else None,
            "inhaltshash": last_ok.get("content_hash") if last_ok else None,
            "saetze": active,
            "verschwunden": vanished,
            "vollstaendig": bool(last_ok),
        }
    return {
        "stand_am": newest.get("finished_at") if newest else None,
        "inhaltshash": newest.get("content_hash") if newest else None,
        "letzter_status": newest.get("status") if newest else None,
        "letzter_vollstaendiger_lauf": last_ok.get("finished_at") if last_ok else None,
        "saetze": active,
        "verschwunden": vanished,
        "vollstaendig": bool(newest and newest.get("status") == "ok"),
    }
