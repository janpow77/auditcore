# Changelog – auditcore_price_analysis

## 0.1.1 – Refaktorierung ohne Verhaltensänderung

- `profiles` nach Verantwortung geschnitten: die eingefrorenen Regelobjekte
  (`CalculationProfile`, `ComparisonProfile`, `ComponentRule`,
  `ConsumptionRule`, `MixedPriceRule`, `TierRule`) liegen in
  `_profile_model`; `profiles` validiert und lädt Profile und gibt alle
  Namen weiter aus (jetzt mit `__all__`).
- `calculation_profile_from_dict` in Einzelregeln zerlegt (Verbrauch,
  Komponente, Staffel, Mischpreis); Prüfreihenfolge unverändert.
- `parse_decimal` (C901 11) und `parse_tiers` (C901 11) in kurze Hilfen
  zerlegt; Fehlercodes und Meldungen unverändert.
- Typen: Eingabewerte als `object` statt `Any` (`parse_decimal`,
  `non_negative`, `parse_day`, `delta_pct`, `traffic_light`,
  `group_statistics`, `Tariff.from_mapping`, `select_tariff`, `calculate`).
  `Any` bleibt an Roh-JSON-Profilen, JSON-Ansichten (`to_dict`) und den
  Legacy-Nachbildungen.
- Keine Umbenennung öffentlicher Namen, keine Aliase nötig.

| Messung | 0.1.0 | 0.1.1 |
|---|---|---|
| Funktionen mit McCabe > 10 | 2 | 0 |
| Module > 400 Zeilen | 1 | 0 |
| `Any`-Vorkommen | 69 | 49 |
| mypy --strict | sauber | sauber |
| Tests / Abdeckung | 622 / 98,0 % | 633 / 98,0 % |
