"""Population strata and the separation of the high-value (top) stratum.

A :class:`Stratum` describes one stratum of the audited population: its book
value, the audited sample of its sampling part and, if any, the units audited
at 100 % (exhaustive/high-value units). Without stratification there is one
stratum. A stratum without sample and with exhaustive units only is a pure
100 % stratum (guidance sections 6.1.2.1 and 6.2.2.1).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from .errors import ExtrapolationInputError
from .sources import Step, guidance
from .units import SampleUnit, check_units


@dataclass(frozen=True)
class Stratum:
    """One stratum: book value, sampled units, exhaustive units, systemic errors.

    ``book_value`` (BV_h) and ``population_size`` (N_h, only needed for equal
    probability methods) include the exhaustive units. ``systemic_error`` is
    the delimited amount of systemic error in the *sampling part* of the
    stratum population, including the amounts found in the sampled units;
    systemic errors of exhaustive units are taken from those units.

    Units excluded from the sample selection under proportional control
    (Art. 148(1) Regulation (EU) No 1303/2013, guidance section 7.10; single
    audit, Art. 80 Regulation (EU) 2021/1060) are *not* part of
    ``book_value``/``population_size`` (the reduced population that was
    sampled); ``excluded_*`` give their book value and number, split into the
    sampling part and the exhaustive (high-value) part. The projection is then
    extended to the original population (section 7.10.2).
    """

    name: str
    book_value: float
    units: tuple[SampleUnit, ...] = ()
    exhaustive_units: tuple[SampleUnit, ...] = ()
    population_size: int | None = None
    systemic_error: float = 0.0
    excluded_book_value: float = 0.0
    excluded_units: int = 0
    excluded_exhaustive_book_value: float = 0.0
    excluded_exhaustive_units: int = 0

    @property
    def original_book_value(self) -> float:
        """Book value of the original population including the excluded units (7.10.2)."""
        return self.book_value + self.excluded_book_value + self.excluded_exhaustive_book_value

    @property
    def has_exclusions(self) -> bool:
        """True if units were excluded under proportional control (section 7.10)."""
        return bool(
            self.excluded_book_value
            or self.excluded_units
            or self.excluded_exhaustive_book_value
            or self.excluded_exhaustive_units
        )

    @property
    def exhaustive_book_value(self) -> float:
        """Book value audited at 100 %."""
        return math.fsum(u.book_value for u in self.exhaustive_units)

    @property
    def sampling_book_value(self) -> float:
        """Book value of the sampling part, BV_s = BV_h − Σ BV of exhaustive units."""
        return self.book_value - self.exhaustive_book_value

    @property
    def sampling_population_size(self) -> int | None:
        """N_s = N_h − number of exhaustive units (``None`` without N_h)."""
        if self.population_size is None:
            return None
        return self.population_size - len(self.exhaustive_units)

    @property
    def is_exhaustive_only(self) -> bool:
        """True for a pure 100 % stratum."""
        return not self.units


def _check_numbers(stratum: Stratum) -> None:
    label = f"Schicht '{stratum.name}'"
    if not math.isfinite(stratum.book_value) or stratum.book_value <= 0:
        raise ExtrapolationInputError(f"{label}: Der Buchwert muss größer als 0 sein.")
    if stratum.sampling_book_value < -1e-6 * stratum.book_value:
        raise ExtrapolationInputError(
            f"{label}: Die vollständig geprüften Einheiten übersteigen den Buchwert."
        )
    if not math.isfinite(stratum.systemic_error) or stratum.systemic_error < 0:
        raise ExtrapolationInputError(f"{label}: Systemische Fehler dürfen nicht negativ sein.")
    found = math.fsum(u.systemic_error for u in stratum.units)
    if stratum.systemic_error + 1e-9 < found:
        raise ExtrapolationInputError(
            f"{label}: Der abgegrenzte systemische Fehler ({stratum.systemic_error:.2f}) ist "
            f"kleiner als der in der Stichprobe gefundene ({found:.2f}). Nicht abgegrenzte "
            "systemische Fehler sind als zufällige Fehler zu erfassen (Leitfaden, Anhang 1)."
        )


def _check_exclusions(stratum: Stratum) -> None:
    label = f"Schicht '{stratum.name}'"
    for value in (stratum.excluded_book_value, stratum.excluded_exhaustive_book_value):
        if not math.isfinite(value) or value < 0:
            raise ExtrapolationInputError(
                f"{label}: Ausgeschlossene Beträge dürfen nicht negativ sein."
            )
    for count in (stratum.excluded_units, stratum.excluded_exhaustive_units):
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ExtrapolationInputError(
                f"{label}: Die Zahl ausgeschlossener Einheiten ist eine ganze Zahl ≥ 0."
            )
    if (
        stratum.excluded_exhaustive_book_value or stratum.excluded_exhaustive_units
    ) and not stratum.exhaustive_units:
        raise ExtrapolationInputError(
            f"{label}: Ohne geprüfte Einheit der Hochwertschicht kann ihr Fehler nicht auf die "
            "ausgeschlossenen Einheiten hochgerechnet werden; die Einheit ist durch eine "
            "Einheit der Stichprobenschicht zu ersetzen (Leitfaden, Abschn. 7.10.3.1 b)."
        )


def check_stratum(stratum: Stratum, *, needs_population_size: bool) -> Stratum:
    """Validate a stratum for the chosen method."""
    if not stratum.name.strip():
        raise ExtrapolationInputError("Jede Schicht braucht einen Namen.")
    check_units(stratum.units + stratum.exhaustive_units, minimum=1)
    _check_numbers(stratum)
    _check_exclusions(stratum)
    size = stratum.population_size
    if needs_population_size and not stratum.is_exhaustive_only:
        if isinstance(size, bool) or not isinstance(size, int):
            raise ExtrapolationInputError(
                f"Schicht '{stratum.name}': Die Anzahl der Einheiten (N) ist Pflicht."
            )
        sampled = stratum.sampling_population_size or 0
        if sampled < len(stratum.units):
            raise ExtrapolationInputError(
                f"Schicht '{stratum.name}': Die Stichprobe ist größer als die Grundgesamtheit."
            )
    return stratum


def check_strata(strata: Sequence[Stratum], *, needs_population_size: bool) -> tuple[Stratum, ...]:
    """Validate all strata; names must be unique and at least one stratum is sampled."""
    checked = tuple(check_stratum(s, needs_population_size=needs_population_size) for s in strata)
    if not checked:
        raise ExtrapolationInputError("Mindestens eine Schicht ist erforderlich.")
    names = [s.name for s in checked]
    if len(set(names)) != len(names):
        raise ExtrapolationInputError("Die Namen der Schichten müssen eindeutig sein.")
    ids = [u.id for s in checked for u in s.units + s.exhaustive_units]
    if len(set(ids)) != len(ids):
        raise ExtrapolationInputError("Eine Einheit darf nur in einer Schicht vorkommen.")
    if all(s.is_exhaustive_only for s in checked):
        raise ExtrapolationInputError("Mindestens eine Schicht muss eine Stichprobe enthalten.")
    return checked


@dataclass(frozen=True)
class TopStratum:
    """Result of the iterative separation of the high-value stratum."""

    exhaustive: tuple[int, ...]
    sampling_book_value: float
    sampling_size: int
    interval: float
    cut_off: float
    steps: tuple[Step, ...]


def split_top_stratum(book_values: Sequence[float], sample_size: int) -> TopStratum:
    """Separate the 100 % stratum for MUS (guidance section 6.3.1.3).

    First cut-off BV/n; then, as long as a remaining unit exceeds the
    interval BV_s/n_s, it is moved to the exhaustive stratum and the interval
    is recomputed. Returns the positions of the exhaustive units.
    """
    if isinstance(sample_size, bool) or not isinstance(sample_size, int) or sample_size < 1:
        raise ExtrapolationInputError("Der Stichprobenumfang muss eine ganze Zahl ≥ 1 sein.")
    values = [float(v) for v in book_values]
    if not values or any(not math.isfinite(v) or v <= 0 for v in values):
        raise ExtrapolationInputError("Buchwerte müssen endlich und größer als 0 sein.")
    total = math.fsum(values)
    cut_off = total / sample_size
    source = guidance("6.3.1.3")
    steps = [Step("Schwellenwert der Vollerhebung", "BV / n", cut_off, source)]
    exhaustive = {i for i, v in enumerate(values) if v > cut_off}
    while True:
        remaining = sample_size - len(exhaustive)
        if remaining < 1:
            raise ExtrapolationInputError(
                "Alle Stichprobenplätze entfallen auf die Vollerhebung; Umfang erhöhen."
            )
        rest = math.fsum(v for i, v in enumerate(values) if i not in exhaustive)
        interval = rest / remaining
        moved = {i for i, v in enumerate(values) if i not in exhaustive and v > interval}
        if not moved:
            break
        exhaustive |= moved
    steps.append(
        Step("Stichprobenintervall der Stichprobenschicht", "SI = BV_s / n_s", interval, source)
    )
    return TopStratum(tuple(sorted(exhaustive)), rest, remaining, interval, cut_off, tuple(steps))


class SizePlanLike(Protocol):
    """The part of ``auditcore_sampling.SizePlan`` used here."""

    @property
    def sample_size(self) -> int: ...


def split_top_stratum_for_plan(book_values: Sequence[float], plan: SizePlanLike) -> TopStratum:
    """:func:`split_top_stratum` with the sample size of an ``auditcore_sampling`` plan."""
    return split_top_stratum(book_values, plan.sample_size)
