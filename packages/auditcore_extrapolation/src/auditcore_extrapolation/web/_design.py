"""Reading strata, units, periods, groups and sub-samples of ``POST /evaluate``.

Additions to ``evaluation/1`` are optional fields, so earlier requests keep
their meaning: ``periods`` with ``period`` on strata and units (guidance
section 7.3), ``group`` on strata (7.8), ``subsample`` on units (7.6, 6.5.3;
nested once for three stages) and ``population_units``.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field

from ..design import Stratum
from ..errors import ExtrapolationInputError
from ..groups import Group
from ..periods import Period
from ..subsampling import SUBSAMPLE_ESTIMATORS, SubSample, SubSampleResult, project_subsample
from ..units import SampleUnit
from ._contract import MAX_STRATA, MAX_UNITS, ContractError, Reader

MAX_PERIODS = 12
#: Main sample plus two sub-sample stages (three-stage design, section 6.5.3.2.2).
MAX_DEPTH = 2


@dataclass
class _Context:
    """Unit budget over all stages and the collected sub-sample results."""

    units: int = 0
    subsamples: list[SubSampleResult] = field(default_factory=list)

    def count(self, amount: int) -> None:
        self.units += amount
        if self.units > MAX_UNITS:
            raise ContractError(f"Mehr als {MAX_UNITS} Einheiten über alle Stufen.")


@dataclass(frozen=True)
class _Unit:
    period: str
    stratum: str
    exhaustive: bool
    unit: SampleUnit


@dataclass(frozen=True)
class Design:
    """Validated input: exactly one of ``strata``, ``periods`` or ``groups``."""

    strata: list[Stratum]
    periods: list[Period] | None
    groups: list[Group] | None
    subsamples: list[SubSampleResult]
    population_units: int | None
    #: (period, stratum) → programme for groups over periods (guidance 6.3.4, 7.8).
    period_groups: dict[tuple[str, str], str] | None = None

    @property
    def kind(self) -> str:
        """``single``, ``periods`` or ``groups``."""
        if self.periods is not None:
            return "periods"
        return "groups" if self.groups is not None else "single"


def _checked(action: Callable[[], SubSampleResult]) -> SubSampleResult:
    try:
        return action()
    except ExtrapolationInputError as exc:
        raise ContractError(str(exc)) from exc


def _projected_error(entry: Reader, unit_id: str, book: float, ctx: _Context, depth: int) -> float:
    if not entry.has("subsample"):
        return entry.number("random_error", 0.0)
    if depth >= MAX_DEPTH:
        raise ContractError(
            f"Einheit '{unit_id}': höchstens drei Stufen (Leitfaden, Abschn. 6.5.3.2)."
        )
    if entry.number("random_error", 0.0):
        raise ContractError(
            f"Einheit '{unit_id}': zufälliger Fehler und Teilstichprobe schließen sich aus; der "
            "Fehler wird aus der Teilstichprobe hochgerechnet (Leitfaden, Abschn. 7.6.3)."
        )
    sub = Reader(entry.body["subsample"], f"{entry.where}.subsample")
    estimator = sub.text("estimator")
    if estimator not in SUBSAMPLE_ESTIMATORS:
        raise ContractError(f"'{sub.where}.estimator' muss {', '.join(SUBSAMPLE_ESTIMATORS)} sein.")
    strata = _assemble(sub, [_unit(e, ctx, depth + 1) for e in sub.items("units", MAX_UNITS)])
    result = _checked(lambda: project_subsample(SubSample(unit_id, estimator, tuple(strata))))
    if not math.isclose(result.book_value, book, rel_tol=1e-9, abs_tol=0.005):
        raise ContractError(
            f"Einheit '{unit_id}': Buchwert {book:.2f} ≠ Summe der Teilschichten "
            f"{result.book_value:.2f}."
        )
    ctx.subsamples.append(result)
    return result.projected_error


def _unit(entry: Reader, ctx: _Context, depth: int = 0) -> _Unit:
    ctx.count(1)
    unit_id = entry.text("id")
    book = entry.number("book_value")
    unit = SampleUnit(
        id=unit_id,
        book_value=book,
        random_error=_projected_error(entry, unit_id, book, ctx, depth),
        systemic_error=entry.number("systemic_error", 0.0),
        anomalous_error=entry.number("anomalous_error", 0.0),
        anomalous_reason=entry.text("anomalous_reason", required=False),
        anomalous_corrected=entry.flag("anomalous_corrected"),
    )
    period = entry.text("period", required=False).strip() if depth == 0 else ""
    return _Unit(period, entry.text("stratum"), entry.flag("exhaustive"), unit)


def _stratum(entry: Reader, members: list[_Unit]) -> Stratum:
    return Stratum(
        name=entry.text("name"),
        book_value=entry.number("book_value"),
        units=tuple(m.unit for m in members if not m.exhaustive),
        exhaustive_units=tuple(m.unit for m in members if m.exhaustive),
        population_size=entry.optional_whole("population_size", minimum=1),
        systemic_error=entry.number("systemic_error", 0.0),
        excluded_book_value=entry.number("excluded_book_value", 0.0),
        excluded_units=entry.optional_whole("excluded_units") or 0,
        excluded_exhaustive_book_value=entry.number("excluded_exhaustive_book_value", 0.0),
        excluded_exhaustive_units=entry.optional_whole("excluded_exhaustive_units") or 0,
    )


def _assemble(body: Reader, units: list[_Unit], period: str = "") -> list[Stratum]:
    entries = [e for e in body.items("strata", MAX_STRATA) if _label(e, "period") == period]
    strata = [
        _stratum(e, [u for u in units if u.stratum == e.text("name") and u.period == period])
        for e in entries
    ]
    known = {s.name for s in strata}
    unknown = sorted({u.stratum for u in units if u.period == period} - known)
    if unknown:
        where = f" im Zeitraum '{period}'" if period else ""
        raise ContractError(
            f"Einheiten verweisen{where} auf unbekannte Schichten: {', '.join(unknown)}."
        )
    return strata


def _label(entry: Reader, key: str) -> str:
    return entry.text(key, required=False).strip()


def _periods(body: Reader, units: list[_Unit]) -> list[Period]:
    names = [entry.text("name").strip() for entry in body.items("periods", MAX_PERIODS)]
    strata_periods = {_label(e, "period") for e in body.items("strata", MAX_STRATA)}
    stray = sorted((strata_periods | {u.period for u in units}) - set(names))
    if stray:
        shown = ", ".join(f"'{p}'" for p in stray)
        raise ContractError(f"Schichten oder Einheiten ohne gültigen Zeitraum: {shown}.")
    return [Period(name, tuple(_assemble(body, units, name))) for name in names]


def _groups(strata: list[Stratum], labels: list[str]) -> list[Group] | None:
    if not any(labels):
        return None
    if not all(labels):
        raise ContractError("Mit Gruppen (Leitfaden, Abschn. 7.8) braucht jede Schicht 'group'.")
    order = list(dict.fromkeys(labels))
    return [
        Group(name, tuple(s for s, label in zip(strata, labels, strict=True) if label == name))
        for name in order
    ]


def read_design(body: Reader) -> Design:
    """Strata, units and the optional periods, groups and sub-samples of a request."""
    ctx = _Context()
    units = [_unit(entry, ctx) for entry in body.items("units", MAX_UNITS)]
    population_units = body.optional_whole("population_units", minimum=1)
    entries = body.items("strata", MAX_STRATA)
    groups_labels = [_label(e, "group") for e in entries]
    if body.has("periods"):
        periods = _periods(body, units)
        strata = [s for p in periods for s in p.strata]
        labels = None
        if any(groups_labels):
            if not all(groups_labels):
                raise ContractError(
                    "Mit Gruppen (Leitfaden, Abschn. 7.8) braucht jede Schicht 'group'."
                )
            labels = {
                (_label(e, "period"), e.text("name")): g
                for e, g in zip(entries, groups_labels, strict=True)
            }
        return Design(strata, periods, None, ctx.subsamples, population_units, labels)
    if any(_label(e, "period") for e in entries) or any(u.period for u in units):
        raise ContractError("'period' setzt die Liste 'periods' voraus.")
    if population_units is not None:
        raise ContractError("'population_units' gilt nur für Stichproben über mehrere Zeiträume.")
    strata = _assemble(body, units)
    return Design(strata, None, _groups(strata, groups_labels), ctx.subsamples, None)
