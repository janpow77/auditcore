# auditcore_price_analysis

Exakte Preisberechnung für regulierte Tarife ohne Netzwerk- oder
Datenbankabhängigkeit (Laufzeit: nur Standardbibliothek). Erster Consumer:
`janpow77/regulierung` (`services/calculator.py`, `services/preisauswahl.py`).

```bash
pip install auditcore_price_analysis==0.1.0
```

```python
from auditcore_price_analysis import Tariff, calculate, load_calculation_profile

profil = load_calculation_profile("regulierung.hpp.nahwaerme", "2026.09.1")
tarif = Tariff.from_mapping(
    {"grundpreis_eur_kw": "28.50", "arbeitspreis_ct_kwh": "10.82"},
    profil,
    release="freigegeben",
    valid_from="2025-01-01",
)
ergebnis = calculate(tarif, profil, consumption={"kw": 12, "kwh": 27000}, stichtag="2025-07-01")
ergebnis.total_rounded  # Decimal('3263.40') – Untergrenze, s. missing_optional
ergebnis.missing_optional  # ('verrechnungspreis_eur_jahr', 'emissionspreis_ct_kwh', 'waermeumlagenpreis_ct_kwh')
ergebnis.to_dict()  # JSON mit Profil-ID/-Version/-Fingerprint, Zeilen, Einheiten
```

Vertrag `auditcore_price_analysis.contract/1`:

- **Profile** (`profiles/*.json`, versioniert, quellengebunden, Fingerprint):
  Bestandteile mit Einheit, Bezugsgröße und Faktor, Gültigkeitsfenster
  (Umlagenwechsel 01.07.2025), Staffelregeln, Rundung, Umgang mit fehlenden
  Werten, Freigabeanforderung, Ampel-/Statistik-/Auswahlregeln. Es gibt kein
  stilles Standardprofil; Version immer ausdrücklich angeben.
- **`calculate`**: Jahreskosten mit exakten Dezimalwerten und Rundung je Profil.
  Fehlende Werte sind nie 0: fehlender Verbrauch ist ein Fehler, fehlende
  Bestandteile stehen im Ergebnis und machen die Summe zur Untergrenze.
- **Freigabe**: `ReleaseStatus` wird nur gelesen. Nicht freigegebene oder am
  Stichtag nicht gültige Tarife sind „nicht vergleichbar“ mit Grund. Die
  Bibliothek gibt keinen Preis frei.
- **`select_tariff`**: deterministische Auswahl nach Freigabe, Stichtag, Q3
  (mit Rückfallkennzeichen), Standardvariante; ausgeschlossene Zeilen mit Grund.
- **`delta_pct`, `traffic_light`, `group_statistics`**: Vergleichsregeln
  ohne Gleitkommaartefakte; ohne gültige Referenz `None`.
- **`auditcore_price_analysis.legacy`**: exakte Nachbildung der Originalfunktionen
  für die schrittweise Umstellung des Consumers.

Empfohlen sind die Profile **@2026.09.2** mit den Nutzerentscheidungen vom
23.09.2026 (PA-H01 bis PA-H04 DECIDED; Wasser-Standardverbrauch 180 m³,
`load_recommended_calculation_profile`, `standard_consumption`). Beobachtetes
Originalverhalten, Korrekturen (PA-L01 bis PA-L17) und Entscheidungen:
[docs/behavior-changes.md](docs/behavior-changes.md).
Umstellung von regulierung: [docs/consumer-migration.md](docs/consumer-migration.md).

LLM-Extraktion, Plausibilisierung, Reviewqueue, Scheduler, Datenbank und
Rechte bleiben in der Anwendung. Herkunft und Lizenz: `NOTICE`,
`provenance.json` (MIT, Freigabe des Rechteinhabers vom 22.09.2026; keine
Umlizenzierung der Quelle). Debian-Paket: `python3-auditcore-price-analysis`.
