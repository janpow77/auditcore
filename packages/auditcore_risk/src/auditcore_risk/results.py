"""Result types of an evaluation: flag hits, record results, dataset findings."""

from __future__ import annotations

import warnings
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from auditcore_common.json_values import jsonable

from .base import JsonObject

#: Library identity recorded in every evaluation (T-31).
LIBRARY = "auditcore_risk 0.3.3"


@dataclass(frozen=True)
class FlagHit:
    """One raised flag with its justification."""

    code: str
    label: str
    reason: str
    evidence: JsonObject
    interpretation: str
    note: str | None
    origin: JsonObject
    severity: str | None = None
    messages: Mapping[str, str] | None = None


@dataclass(frozen=True)
class RecordResult:
    """Flags of one record in profile order (``None`` = not decidable)."""

    index: int
    flags: Mapping[str, bool | None]
    hits: tuple[FlagHit, ...]
    undetermined: Mapping[str, str]
    values: JsonObject
    assessment: JsonObject | None = None

    @property
    def codes(self) -> tuple[str, ...]:
        """Codes of the raised flags in profile order."""
        return tuple(hit.code for hit in self.hits)


@dataclass(frozen=True)
class DatasetFinding:
    """Result of a dataset-wide rule (for example a concentration share)."""

    code: str
    label: str
    triggered: bool
    value: float | None
    reason: str
    evidence: JsonObject
    origin: JsonObject


@dataclass(frozen=True)
class Evaluation:
    """Complete, profile-bound result; ``summary`` follows the profile's format."""

    profile: Mapping[str, str]
    records: tuple[RecordResult, ...]
    dataset: tuple[DatasetFinding, ...]
    skipped: Mapping[str, str]
    summary: tuple[JsonObject, ...]
    library: str = LIBRARY

    def to_dict(self) -> dict[str, Any]:
        """JSON-compatible view (evidence values are plain data)."""
        return {
            "library": self.library,
            "profile": dict(self.profile),
            "records": [
                {
                    "index": r.index,
                    "flags": dict(r.flags),
                    "codes": list(r.codes),
                    "undetermined": dict(r.undetermined),
                    "values": dict(r.values),
                    "assessment": None if r.assessment is None else jsonable(r.assessment),
                    "hits": [
                        {
                            "code": h.code,
                            "label": h.label,
                            "reason": h.reason,
                            "interpretation": h.interpretation,
                            "note": h.note,
                            "severity": h.severity,
                            "messages": None if h.messages is None else dict(h.messages),
                            "evidence": jsonable(h.evidence),
                            "origin": jsonable(h.origin),
                        }
                        for h in r.hits
                    ],
                }
                for r in self.records
            ],
            "dataset": [
                {
                    "code": d.code,
                    "label": d.label,
                    "triggered": d.triggered,
                    "value": d.value,
                    "reason": d.reason,
                    "evidence": jsonable(d.evidence),
                }
                for d in self.dataset
            ],
            "skipped": dict(self.skipped),
            "summary": [dict(s) for s in self.summary],
        }


def plain(value: object) -> object:
    """Veraltet: :func:`auditcore_common.json_values.jsonable` (gleiches Ergebnis)."""
    warnings.warn(
        "auditcore_risk.results.plain ist veraltet; "
        "auditcore_common.json_values.jsonable verwenden.",
        DeprecationWarning,
        stacklevel=2,
    )
    return jsonable(value)
