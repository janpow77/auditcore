"""Deterministic selection of the tariff that applies on a reference day.

Rules (profile ``selection``): only released records if the profile demands
it, no record whose validity starts after the reference day, optionally no
record whose ``valid_to`` lies before it, exact meter size (Q3) preferred with
a stated tolerance and fallback marked in ``datenstatus``, latest validity
start wins, standard variants preferred, ties resolved stably by variant id
and row id and reported as ``ambiguous``. Every excluded record is listed
with its reason; nothing is dropped silently and no status is changed.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from .errors import PriceAnalysisError
from .numbers import optional_non_negative, parse_day
from .profiles import ComparisonProfile
from .tariff import ReleaseStatus, Tariff

STATUS_OK = "ok"
STATUS_Q3_FALLBACK = "nicht_verfuegbar_fuer_q3"
STATUS_NONE = "kein_tarif"


@dataclass(frozen=True)
class Selection:
    """Chosen tariff (or ``None``) with data status, ambiguity and exclusions."""

    tariff: Tariff | None
    datenstatus: str
    ambiguous: bool
    excluded: tuple[tuple[int, str], ...]
    profile: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        """JSON view (the tariff by its row id and full content)."""
        return {
            "tariff": None if self.tariff is None else self.tariff.to_dict(),
            "datenstatus": self.datenstatus,
            "ambiguous": self.ambiguous,
            "excluded": [{"index": i, "reason": r} for i, r in self.excluded],
            "profile": self.profile,
        }


def _order(tariff: Tariff) -> tuple[bool, int, int]:
    return (
        tariff.variant_id is None,
        tariff.variant_id if tariff.variant_id is not None else 0,
        tariff.row_id if tariff.row_id is not None else 0,
    )


def _latest(candidates: list[Tariff], prefer_standard: bool) -> tuple[Tariff, bool]:
    newest = max(t.valid_from for t in candidates if t.valid_from is not None)
    same_day = [t for t in candidates if t.valid_from == newest]
    preferred = [t for t in same_day if t.standard_variant] if prefer_standard else []
    chosen = sorted(preferred or same_day, key=_order)[0]
    return chosen, len(same_day) > 1


def select_tariff(
    candidates: Iterable[Tariff],
    *,
    stichtag: date | str,
    profile: ComparisonProfile,
    q3: Any = None,
) -> Selection:
    """Select one tariff for ``stichtag`` (and meter size ``q3`` for water)."""
    day = parse_day(stichtag)
    wanted_q3: Decimal | None = optional_non_negative(q3, field="q3")
    eligible: list[Tariff] = []
    excluded: list[tuple[int, str]] = []
    for index, tariff in enumerate(candidates):
        if tariff.valid_from is None:
            excluded.append((index, "ohne_gueltigkeitsbeginn"))
        elif profile.only_released and tariff.release is not ReleaseStatus.FREIGEGEBEN:
            excluded.append((index, f"freigabe:{tariff.release.value}"))
        elif profile.not_after_reference_date and tariff.valid_from > day:
            excluded.append((index, "gueltig_erst_spaeter"))
        elif profile.respect_valid_to and tariff.valid_to is not None and tariff.valid_to < day:
            excluded.append((index, "abgelaufen"))
        else:
            eligible.append(tariff)
    if len({t.kind for t in eligible}) > 1:
        raise PriceAnalysisError("mixed_kinds", "Kandidaten verschiedener Tarifarten.")
    if not eligible:
        return Selection(None, STATUS_NONE, False, tuple(excluded), profile.reference)
    status = STATUS_OK
    pool = eligible
    if wanted_q3 is not None:
        exact = [
            t for t in eligible if t.q3 is not None and abs(t.q3 - wanted_q3) < profile.q3_tolerance
        ]
        if exact:
            pool = exact
        else:
            status = STATUS_Q3_FALLBACK
    chosen, ambiguous = _latest(pool, profile.prefer_standard_variants)
    return Selection(chosen, status, ambiguous, tuple(excluded), profile.reference)
