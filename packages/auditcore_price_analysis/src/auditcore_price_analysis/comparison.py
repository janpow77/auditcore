"""Deviation, traffic light and group statistics with exact decimals.

Unlike the legacy float functions these never turn a missing or non-positive
reference into a result: without a usable reference the answer is ``None``
(unknown), not ``0 %`` or ``gruen``.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .numbers import parse_decimal, text
from .profiles import ComparisonProfile

GREEN = "gruen"
YELLOW = "gelb"
RED = "rot"


def delta_pct(value: Any, reference: Any, profile: ComparisonProfile) -> Decimal | None:
    """Percentage deviation ``(value - reference) / reference × 100``, rounded by profile.

    ``None`` if the reference is missing, zero or negative.
    """
    if reference is None or value is None:
        return None
    ref = parse_decimal(reference, field="reference")
    if ref <= 0:
        return None
    current = parse_decimal(value, field="value")
    return profile.delta_rounding.apply((current - ref) / ref * 100)


def traffic_light(value: Any, median: Any, profile: ComparisonProfile) -> str | None:
    """``gruen`` up to threshold × fraction, ``gelb`` up to the threshold, else ``rot``.

    Decided on the exact deviation (no float artifacts at the limits). ``None``
    without a positive median. Algorithmic signal only; no legal consequence.
    """
    if median is None or value is None:
        return None
    ref = parse_decimal(median, field="median")
    if ref <= 0:
        return None
    deviation = (parse_decimal(value, field="value") - ref) / ref * 100
    if deviation <= profile.threshold_pct * profile.yellow_from_fraction:
        return GREEN
    if deviation <= profile.threshold_pct:
        return YELLOW
    return RED


@dataclass(frozen=True)
class GroupStatistics:
    """Statistics of one comparison group; ``None`` when the group is empty."""

    count: int
    median: Decimal | None
    mean: Decimal | None
    stddev: Decimal | None
    minimum: Decimal | None
    maximum: Decimal | None
    stddev_method: str
    profile: Mapping[str, str]

    def to_dict(self) -> dict[str, Any]:
        """JSON view."""
        return {
            "count": self.count,
            "median": text(self.median),
            "mean": text(self.mean),
            "stddev": text(self.stddev),
            "min": text(self.minimum),
            "max": text(self.maximum),
            "stddev_method": self.stddev_method,
            "profile": dict(self.profile),
        }


def group_statistics(values: Iterable[Any], profile: ComparisonProfile) -> GroupStatistics:
    """Median, mean, standard deviation (population or sample per profile), min and max.

    ``None`` values are rejected instead of being skipped or counted as zero;
    the consumer decides beforehand which results belong to the group.
    """
    numbers = sorted(parse_decimal(v, field="value") for v in values)
    rounding = profile.statistics_rounding
    n = len(numbers)
    if n == 0:
        return GroupStatistics(0, None, None, None, None, None, profile.stddev, profile.reference)
    middle = n // 2
    median = numbers[middle] if n % 2 else (numbers[middle - 1] + numbers[middle]) / 2
    mean = sum(numbers, Decimal(0)) / n
    squares = sum(((x - mean) ** 2 for x in numbers), Decimal(0))
    divisor = n if profile.stddev == "population" else n - 1
    stddev = (squares / divisor).sqrt() if divisor > 0 else None
    return GroupStatistics(
        count=n,
        median=rounding.apply(median),
        mean=rounding.apply(mean),
        stddev=None if stddev is None else rounding.apply(stddev),
        minimum=rounding.apply(numbers[0]),
        maximum=rounding.apply(numbers[-1]),
        stddev_method=profile.stddev,
        profile=profile.reference,
    )
