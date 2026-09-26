# Changelog – auditcore_price_analysis

## 0.1.3 – 2026-09-26 – Paketstand für Release v0.4.2

Keine Verhaltensänderung. README mit den Installationsangaben aus Release v0.4.1. Pins: `auditcore_common==0.2.0`.

## 0.1.2 – 2026-09-25

Verhaltensänderung PA-C01 (Nutzerauftrag vom 25.09.2026).

- `parse_decimal` (und damit `non_negative`, `calculate`, `delta_pct`,
  `traffic_light`, `group_statistics`) liest deutsche Zahlentexte nach dem
  gemeinsamen Vertrag `contracts/common-cases/parse-number` (Modus `de`) über
  `auditcore_common.numbers_de`: „1.234,56 €“ → 1234.56, „10,82“ → 10.82,
  „1.000.000“ → 1000000. Bisher `invalid_number`.
- Mehrdeutige deutsche Texte („1,234“, „0,125“, „1.234 €“) ergeben den neuen
  Fehlercode `ambiguous_number` mit Hinweis statt einer geratenen Zahl.
- Einfacher Punkttext („2.5“, „1.234“) sowie `Decimal`/`int`/`float`
  unverändert.
- Neu `legacy_parse_decimal`: das Verhalten von 0.1.1 (nur Punkt, jedes Komma
  `invalid_number`).
- Pflichtabhängigkeit `auditcore_common==0.1.1`.

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
- `legacy.calculate_nahwaerme` (70 Zeilen): Umlagenwahl (`_levy`) und
  Anteilsrechnung (`_heat_shares`) als eigene Schritte; Prüfreihenfolge,
  Decimal-Rechnung und Rundung unverändert (Differenzlauf gegen 0.1.0 mit
  30 000 Zufallseingaben inkl. Fehlerpfaden bitgleich).
- Interne Hilfen englisch benannt: `_nicht_negativ` → `_non_negative`,
  `_sortier_schluessel` → `_sort_key` (privat, daher ohne Alias).
- Keine Umbenennung öffentlicher Namen, keine Aliase nötig.

Messung mit `auditcore-codegate check --package auditcore_price_analysis`:

| Messung | 0.1.0 | 0.1.1 |
|---|---|---|
| Funktionen mit McCabe > 10 | 2 | 0 |
| Funktionen > 60 Zeilen | 2 | 0 |
| Module > 400 Zeilen | 1 | 0 |
| `Any`-Verwendungen | 61 | 42 |
| nicht-englische Bezeichner | 2 | 0 |
| mypy --strict | sauber | sauber |
| Tests / Abdeckung | 622 / 98,0 % | 633 / 98,0 % |

## 0.1.0 – 2026-09-23

Erstausgabe: Vertrag `auditcore_price_analysis.contract/1` mit `calculate`,
`select_tariff`, `delta_pct`, `traffic_light`, `group_statistics`,
charakterisierte Profile @2026.09.1 und Modul `legacy` (274 ausgeführte Fälle
aus regulierung, exakt). Nachgetragen am selben Tag: empfohlene Profile
@2026.09.2 mit den Nutzerentscheidungen PA-H01 bis PA-H04
(`load_recommended_calculation_profile`, `load_recommended_comparison_profile`,
`standard_consumption`).
