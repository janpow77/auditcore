"""EU thresholds of all regimes: catalogue, lookup and classification without national tiers.

Works on profiles of schema 3 (``procurement.hvtg`` from 2026.10.1). A caller
names the regime (directive), the contract type, where required the authority
type, and the reference date; the answer is the threshold of that date with
its official source, or an explicit "not recorded". Nothing national (tiers,
procedures, required documents) is read or returned here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from .eu_regimes import (
    ContractType,
    Label,
    Regime,
    RegimeTable,
    Series,
    ThresholdRow,
    find_series,
    row_for_year,
    row_on,
)
from .precheck_common import PASS, REVIEW_REQUIRED, CheckResult, result
from .precheck_profile import PrecheckProfile, ThresholdUnavailable

_CHECK = ("precheck_eu_threshold", "EU-Schwellenwert")


@dataclass(frozen=True)
class RegimeThreshold:
    """The EU threshold applicable to one case, with regime, contract type and source."""

    regime: Regime
    contract_type: str
    series: Series
    row: ThresholdRow
    source: dict[str, str]

    @property
    def value(self) -> int:
        """Threshold in EUR (net of VAT)."""
        return self.row.value

    def to_dict(self) -> dict[str, object]:
        """JSON view recorded in results (same core keys as the year-table threshold)."""
        authority = None if self.series.id == self.contract_type else self.series.id
        return {
            "value": self.row.value,
            "key": f"{self.regime.id}.{self.contract_type}"
            + (f".{authority}" if authority else ""),
            "valid_from": self.row.valid_from.isoformat(),
            "valid_to": self.row.valid_to.isoformat(),
            "regulation": self.source["regulation"],
            "official_journal": self.source["official_journal"],
            "celex": self.source["celex"],
            "url": self.source["url"],
            "provision": self.row.provision,
            "legal_basis": self.series.legal_basis,
            "regime": self.regime.id,
            "contract_type": self.contract_type,
            "authority_type": authority,
        }


def _table(profile: PrecheckProfile) -> RegimeTable:
    if profile.eu_regimes is None:
        raise ThresholdUnavailable(
            f"Profil {profile.id} {profile.version} enthält keine EU-Schwellenwerte je "
            "Regime; bitte procurement.hvtg ab 2026.10.1 verwenden."
        )
    return profile.eu_regimes


def _threshold(
    profile: PrecheckProfile,
    regime: Regime,
    contract_type: str,
    series: Series,
    on: date | None,
    year: int | None,
) -> RegimeThreshold:
    row = row_on(series, on) if on is not None else row_for_year(series, int(year or 0))
    if row is None:
        when = f"den {on:%d.%m.%Y}" if on is not None else f"das ganze Jahr {year}"
        raise ThresholdUnavailable(
            f"Für {when} ist im Profil {profile.id} {profile.version} kein belegter "
            f"EU-Schwellenwert für {regime.label.de} – {series.label.de} hinterlegt."
        )
    source = dict(_table(profile).sources[row.source])
    return RegimeThreshold(regime, contract_type, series, row, source)


def eu_regime_threshold(
    profile: PrecheckProfile,
    regime: str,
    contract_type: str,
    on: date,
    authority_type: str | None = None,
) -> RegimeThreshold:
    """Verified threshold of a regime and contract type on ``on``; no fallback.

    Raises:
        ThresholdUnavailable: no regime table, or no verified value for ``on``.
        ValueError: unknown regime, contract type or authority type, or the
            authority type is required and missing.
    """
    found = _table(profile).regime(regime)
    series = find_series(found, contract_type, authority_type)
    if series is None:
        raise ValueError(f"authority_type ist für '{contract_type}' erforderlich.")
    return _threshold(profile, found, contract_type, series, on, None)


def _candidates(
    profile: PrecheckProfile,
    regime: Regime,
    contract_type: str,
    authority_type: str | None,
    on: date | None,
    year: int | None,
) -> list[RegimeThreshold]:
    """The applicable threshold, or one per authority type when none was given."""
    series = find_series(regime, contract_type, authority_type)
    if series is not None:
        return [_threshold(profile, regime, contract_type, series, on, year)]
    kind = next(c for c in regime.contract_types if c.id == contract_type)
    found = [_threshold(profile, regime, contract_type, s, on, year) for s in kind.authority_types]
    return sorted(found, key=lambda t: t.value)


def check_eu_threshold(
    profile: PrecheckProfile,
    estimated_value: Decimal,
    *,
    regime: str,
    contract_type: str,
    authority_type: str | None = None,
    reference_date: date | None = None,
    year: int | None = None,
) -> CheckResult:
    """Whether the estimated value reaches the EU threshold of the case (EU part only).

    ``PASS`` carries ``above_threshold`` (reached or exceeded) and the threshold
    with its source; ``REVIEW_REQUIRED`` means "not recorded" or undecidable
    (date missing, no verified period, authority type needed). National tiers
    are neither evaluated nor returned.

    Raises:
        ValueError: unknown regime, contract type or authority type.
    """
    try:
        found = _table(profile).regime(regime)
        if reference_date is None and year is None:
            find_series(found, contract_type, authority_type)
            return result(
                *_CHECK,
                REVIEW_REQUIRED,
                "Stichtag fehlt: Datum der Maßnahme/Bekanntmachung oder Jahr angeben; "
                "der EU-Schwellenwert gilt je Zeitraum.",
            )
        limits = _candidates(profile, found, contract_type, authority_type, reference_date, year)
    except ThresholdUnavailable as exc:
        return result(*_CHECK, REVIEW_REQUIRED, str(exc))
    if len(limits) > 1 and limits[0].value <= estimated_value < limits[-1].value:
        return result(
            *_CHECK,
            REVIEW_REQUIRED,
            f"Der Auftragswert {estimated_value} EUR liegt zwischen den EU-Schwellenwerten "
            f"{limits[0].value} EUR ({limits[0].series.label.de}) und {limits[-1].value} EUR "
            f"({limits[-1].series.label.de}); Art des Auftraggebers (authority_type) angeben.",
            eu_thresholds=[t.to_dict() for t in limits],
        )
    limit = limits[-1] if estimated_value >= limits[-1].value else limits[0]
    above = estimated_value >= limit.value
    return result(
        *_CHECK,
        PASS,
        f"EU-Schwellenwert {limit.value} EUR "
        f"{'erreicht oder überschritten' if above else 'nicht erreicht'} "
        f"({estimated_value} EUR; {limit.regime.label.de}, {limit.series.label.de}; "
        f"{limit.source['regulation']}).",
        above_threshold=above,
        eu_threshold=limit.to_dict(),
    )


def _label(label: Label | None) -> dict[str, str] | None:
    return None if label is None else label.to_dict()


def _series_view(series: Series) -> dict[str, object]:
    return {
        "id": series.id,
        "label": series.label.to_dict(),
        "legal_basis": series.legal_basis,
        "note": _label(series.note),
        "thresholds": [
            {
                "valid_from": row.valid_from.isoformat(),
                "valid_to": row.valid_to.isoformat(),
                "value": row.value,
                "source": row.source,
                "provision": row.provision,
            }
            for row in series.thresholds
        ],
    }


def _contract_type_view(kind: ContractType) -> dict[str, object]:
    view = _series_view(kind.series)
    if kind.authority_types:
        del view["thresholds"]
    return {**view, "authority_types": [_series_view(s) for s in kind.authority_types]}


def eu_catalogue(profile: PrecheckProfile) -> dict[str, object]:
    """Catalogue of the EU thresholds: regimes, contract types, authority types, sources.

    Labels are German and English (terms of the directives); every threshold
    row refers to an entry of ``sources`` (regulation, Official Journal, CELEX,
    URL, checksum and wording of the text read). Contains no national rules.

    Raises:
        ThresholdUnavailable: the profile has no regime table (schema 1 or 2).
    """
    table = _table(profile)
    return {
        "profile": profile.reference,
        "comparison": table.comparison,
        "comparison_reference": table.comparison_reference,
        "not_entered": table.not_entered,
        "regimes": [
            {
                "id": regime.id,
                "directive": regime.directive,
                "celex": regime.celex,
                "label": regime.label.to_dict(),
                "buyer": regime.buyer.to_dict(),
                "legal_basis": regime.legal_basis,
                "national_reference": regime.national_reference,
                "note": _label(regime.note),
                "contract_types": [_contract_type_view(c) for c in regime.contract_types],
            }
            for regime in table.regimes
        ],
        "sources": {celex: dict(source) for celex, source in table.sources.items()},
    }
