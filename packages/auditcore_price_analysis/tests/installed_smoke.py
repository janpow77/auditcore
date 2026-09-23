"""Run with python -I against an installed wheel or Debian package; no pytest needed."""

from datetime import date
from decimal import Decimal
from importlib.metadata import distribution
from importlib.util import find_spec


def main() -> None:
    """Calculate, select and compare with shipped profiles; replay one legacy case."""
    package = distribution("auditcore_price_analysis")
    assert package.version == "0.1.0"
    assert [r for r in package.requires or [] if "extra ==" not in r] == []
    assert find_spec("auditcore") is None
    from auditcore_price_analysis import (
        Tariff,
        available_profiles,
        calculate,
        group_statistics,
        legacy,
        load_calculation_profile,
        load_comparison_profile,
        select_tariff,
        traffic_light,
    )

    assert len(available_profiles()) == 3
    wasser = load_calculation_profile("regulierung.hpp.wasser", "2026.09.1")
    tarif = Tariff.from_mapping(
        {
            "grundpreis_eur_monat": "10",
            "arbeitspreis_staffel": [{"bis_m3": 50, "preis": "1.8"}, {"preis": "2.2"}],
            "verrechnungspreis_eur_monat": "2.5",
            "wasserentnahmeentgelt_eur_m3": "0.15",
        },
        wasser,
        release="freigegeben",
        valid_from="2025-01-01",
    )
    result = calculate(tarif, wasser, consumption={"q3": 4, "m3": 150}, stichtag=date(2025, 7, 1))
    assert result.total_rounded == Decimal("482.50") and result.comparable
    vergleich = load_comparison_profile("regulierung.hpp.vergleich", "2026.09.1")
    assert select_tariff([tarif], stichtag="2025-07-01", profile=vergleich, q3=4).tariff is tarif
    assert traffic_light(result.total_rounded, Decimal("420"), vergleich) == "gelb"
    assert group_statistics([], vergleich).median is None
    legacy_result = legacy.calculate_wasser(
        {
            "grundpreis_eur_monat": 0,
            "arbeitspreis_eur_m3": 1.07,
            "verrechnungspreis_eur_monat": 0,
            "wasserentnahmeentgelt_eur_m3": 0,
        },
        m3=2.5,
    )
    assert legacy_result["jahreskosten"] == 2.68
    print("PASS: installed auditcore_price_analysis calculation, selection, comparison, legacy")


if __name__ == "__main__":
    main()
