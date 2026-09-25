"""Input validation and window helpers shared by all indicators."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

from ._numeric import neumaier_sum, numpy_pairwise_sum
from .errors import IndicatorInputError
from .profiles import IndicatorProfile, Summation

Value = float | int | None
Series = list[float | None]


def _values(series: Sequence[Value], label: str) -> Series:
    if isinstance(series, (str, bytes)) or not isinstance(series, Sequence):
        raise IndicatorInputError(f"{label} muss eine Folge von Zahlen oder None sein.")
    out: Series = []
    for index, value in enumerate(series):
        if value is None:
            out.append(None)
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise IndicatorInputError(f"{label}[{index}] ist keine Zahl ({type(value).__name__}).")
        number = float(value)
        if not math.isfinite(number):
            raise IndicatorInputError(
                f"{label}[{index}] ist nicht endlich ({number!r}); fehlende Werte als None angeben."
            )
        out.append(number)
    return out


def _same_length(**columns: Series) -> int:
    lengths = {len(v) for v in columns.values()}
    if len(lengths) > 1:
        detail = ", ".join(f"{k}={len(v)}" for k, v in columns.items())
        raise IndicatorInputError(f"Reihen sind unterschiedlich lang ({detail}).")
    return lengths.pop() if lengths else 0


def _window(n: object, minimum: int, name: str = "n") -> int:
    if isinstance(n, bool) or not isinstance(n, int):
        raise IndicatorInputError(f"{name} muss eine ganze Zahl sein.")
    if n < minimum:
        raise IndicatorInputError(f"{name} muss > {minimum - 1} sein")
    return n


def _finite(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise IndicatorInputError(f"{name} muss eine Zahl sein.")
    number = float(value)
    if not math.isfinite(number):
        raise IndicatorInputError(f"{name} muss endlich sein.")
    return number


def _summer(summation: Summation) -> Callable[[Sequence[float]], float]:
    return neumaier_sum if summation == "neumaier" else numpy_pairwise_sum


def _first_present(values: Series) -> int | None:
    for index, value in enumerate(values):
        if value is not None:
            return index
    return None


def _reject_gaps(values: Series, label: str, profile: IndicatorProfile, *, leading: bool) -> None:
    """Raise if a value is missing (after the first present value unless ``leading``)."""
    first = _first_present(values)
    if first is None and not leading:
        return
    start = 0 if leading else (first or 0)
    for index in range(start, len(values)):
        if values[index] is None:
            raise IndicatorInputError(
                f"{label}[{index}] fehlt; Profil {profile.id} lässt keine Lücken zu."
            )


def _first_full_window(values: Series, n: int) -> int | None:
    """End index of the first run of ``n`` consecutive present values."""
    run = 0
    for index, value in enumerate(values):
        run = run + 1 if value is not None else 0
        if run >= n:
            return index
    return None


def _rolling(values: Series, n: int, statistic: Callable[[list[float]], float | None]) -> Series:
    out: Series = [None] * len(values)
    for index in range(n - 1, len(values)):
        window = values[index + 1 - n : index + 1]
        if any(v is None for v in window):
            continue
        out[index] = statistic([v for v in window if v is not None])
    return out
