"""Minimum sample sizes for non-statistical sampling, as named rule profiles.

* ``cpr_2021_art79_2`` – Art. 79(2) Regulation (EU) 2021/1060: allowed if the
  population has fewer than 300 sampling units; the random sample covers at
  least 10 % of the sampling units of the accounting year.
* ``cpr_2013_art127_1`` – Art. 127(1) Regulation (EU) No 1303/2013
  (2014–2020): at least 5 % of the operations and 10 % of the expenditure;
  the guidance adds the indicative coverage of Table 6 (section 6.4.3) by
  assurance level from the system audits.

The rule gives a lower bound; the audit authority decides the final size by
professional judgement (guidance 6.4.3).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType

from ..sizes import SamplingInputError
from .plan import GuidancePlan, finite, frozen, whole
from .sources import CPR_2013, Step, guidance, regulation

NONSTATISTICAL = "guidance.nonstatistical"


@dataclass(frozen=True)
class CoverageBand:
    """Indicative coverage of guidance Table 6 for one assurance level."""

    units: tuple[float, float]
    expenditure: tuple[float, float]


@dataclass(frozen=True)
class NonStatisticalRule:
    """A named legal minimum for non-statistical samples."""

    id: str
    label: str
    source: str
    min_unit_share: float
    min_expenditure_share: float | None
    max_population: int | None
    bands: MappingProxyType[str, CoverageBand]

    def to_dict(self) -> dict[str, object]:
        """JSON-compatible rule."""
        return {
            "id": self.id,
            "label": self.label,
            "source": self.source,
            "min_unit_share": self.min_unit_share,
            "min_expenditure_share": self.min_expenditure_share,
            "max_population": self.max_population,
            "assurance_levels": {
                key: {"units": list(b.units), "expenditure": list(b.expenditure)}
                for key, b in self.bands.items()
            },
        }


#: Guidance Table 6 (section 6.4.3), keys are the categories of the system audits.
TABLE_6 = MappingProxyType(
    {
        "works_well": CoverageBand((0.05, 0.05), (0.10, 0.10)),
        "works": CoverageBand((0.05, 0.10), (0.10, 0.10)),
        "works_partially": CoverageBand((0.10, 0.15), (0.10, 0.20)),
        "does_not_work": CoverageBand((0.15, 0.20), (0.10, 0.20)),
    }
)
RULES = MappingProxyType(
    {
        "cpr_2021_art79_2": NonStatisticalRule(
            "cpr_2021_art79_2",
            "Förderzeitraum 2021–2027: weniger als 300 Einheiten, mindestens 10 % der Einheiten",
            regulation("79 Abs. 2"),
            0.10,
            None,
            300,
            MappingProxyType({}),
        ),
        "cpr_2013_art127_1": NonStatisticalRule(
            "cpr_2013_art127_1",
            "Förderzeitraum 2014–2020: mindestens 5 % der Vorhaben und 10 % der Ausgaben",
            f"{regulation('127 Abs. 1', CPR_2013)}; {guidance('6.4.3')}, Tabelle 6",
            0.05,
            0.10,
            None,
            TABLE_6,
        ),
    }
)


def rule(rule_id: object) -> NonStatisticalRule:
    """The explicitly named rule profile."""
    found = RULES.get(rule_id) if isinstance(rule_id, str) else None
    if found is None:
        raise SamplingInputError(
            f"Unbekannte Regel '{rule_id}'. Zulässig: {', '.join(sorted(RULES))}."
        )
    return found


def _at_least(share: float, total: float) -> int:
    return max(1, math.ceil(round(share * total, 9)))


def _band_inputs(
    chosen: NonStatisticalRule, assurance: str | None, units: int
) -> dict[str, object]:
    if assurance is None:
        return {}
    band = chosen.bands.get(assurance)
    if band is None:
        allowed = ", ".join(chosen.bands) or "keine"
        raise SamplingInputError(
            f"Bewertungsstufe '{assurance}' ist in {chosen.id} nicht vorgesehen; "
            f"zulässig: {allowed}."
        )
    return {
        "assurance_level": assurance,
        "recommended_units": [_at_least(band.units[0], units), _at_least(band.units[1], units)],
        "recommended_unit_shares": list(band.units),
        "recommended_expenditure_shares": list(band.expenditure),
    }


def nonstatistical_minimum(
    rule_id: str,
    *,
    population_size: int,
    book_value: float | None = None,
    assurance_level: str | None = None,
) -> GuidancePlan:
    """Legal minimum of a non-statistical sample; ``sample_size`` is the minimum number of units.

    Raises:
        SamplingInputError: unknown rule or assurance level, population too
            large for a non-statistical method under the rule.
    """
    chosen = rule(rule_id)
    units = whole(population_size, "population_size")
    if chosen.max_population is not None and units >= chosen.max_population:
        raise SamplingInputError(
            f"Nicht-statistische Verfahren sind nur bei weniger als {chosen.max_population} "
            f"Stichprobeneinheiten zulässig ({chosen.source}); statistisch planen."
        )
    raw = chosen.min_unit_share * units
    size = _at_least(chosen.min_unit_share, units)
    steps = [
        Step("Mindestumfang (Einheiten)", f"⌈{chosen.min_unit_share:.0%} × N⌉", raw, chosen.source)
    ]
    inputs: dict[str, object] = {"rule": chosen.id, "population_size": units}
    if chosen.min_expenditure_share is not None:
        value = finite(book_value, "book_value", positive=True)
        minimum = chosen.min_expenditure_share * value
        steps.append(
            Step(
                "Mindestabdeckung (Ausgaben)",
                f"{chosen.min_expenditure_share:.0%} × BV",
                minimum,
                chosen.source,
            )
        )
        inputs |= {"book_value": value, "min_expenditure": minimum}
    inputs |= _band_inputs(chosen, assurance_level, units)
    warnings = [
        "Mindestwert: Die Prüfbehörde legt den Umfang nach pflichtgemäßem Ermessen fest und "
        "zieht zufällig (Leitfaden, Abschn. 6.4.3 und 6.4.4)."
    ]
    if units > 150:
        warnings.append(
            "Über 150 Einheiten empfiehlt der Leitfaden, vorab den Rat der Kommission einzuholen "
            "(Abschn. 6.4.1)."
        )
    return GuidancePlan(
        NONSTATISTICAL, size, raw, frozen(inputs), tuple(steps), warnings=tuple(warnings)
    )
