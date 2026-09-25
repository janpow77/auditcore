# Umstellung von regulierung auf auditcore_price_analysis

Status: **getestete Integrationsvariante, noch nicht umgestellt.** Die
Requirements von regulierung werden erst mit dem zentralen Release v0.3.0
geändert. Der vollständige Änderungssatz liegt als Patch unter
`docs/migrations/regulierung-price.patch` (Basis
`janpow77/regulierung@853676d2`, nicht gepusht).

## Consumer-Stellen

| Datei | Symbol | Umstellung |
|---|---|---|
| `backend/app/services/calculator.py` | `calculate_nahwaerme`, `calculate_wasser`, `_calculate_staffel`, `_calculate_staffel_decimal`, `calculate_delta`, `determine_compliance`, `calculate_cluster_statistics`, `UMLAGEN_STICHTAG`, `CENT`, `ZEHNTEL` | Modul bindet `auditcore_price_analysis.legacy` (gleiche Namen, gleiches Verhalten) |
| `backend/app/services/preisauswahl.py` | `waehle_preis_deterministisch`, `waehle_wasser_preis`, `Q3_TOLERANZ`, `DATENSTATUS_*` | reine Auswahl aus der Bibliothek; `lade_wasser_preis`/`lade_nahwaerme_preis` (DB) bleiben |
| Aufrufer (unverändert) | `api/calculate_routes.py`, `api/export_routes.py`, `api/provider_routes.py`, `services/clustering.py`, `services/cluster_comparison.py`, `services/flagging.py` | keine Änderung nötig |

## Nachweis (lokal, isoliert)

- Umgebung: eigene venv mit den Wheels `auditcore_price_analysis-0.1.0`,
  `auditcore_price_sources-0.1.0` sowie den veröffentlichten, hashgleichen
  Wheels `auditcore_harvest-0.1.0`, `auditcore_dataprotection-0.1.0`,
  `auditcore_reporting-0.2.0`; übrige Abhängigkeiten nur lesend aus der
  regulierung-venv. Datenbank: Wegwerf-Container
  `hpp-postgres:16-timescale-postgis` (keine Produktions-DB), Testdatenbank
  durch die conftest-Wächter angelegt und verworfen.
- Gezielte Tests (Rechner, Preisauswahl, Cluster, Destatis, Registry):
  **124 passed** vor und nach der Umstellung.
- Neue Bindungstests `tests/test_auditcore_preis_bindung.py`: 3 passed.
- Gesamte Suite: siehe Bericht `docs/reports/PRICE_PACKAGES_REPORT.md`.

## Umstellung (nach Release v0.3.0)

1. `backend/requirements.txt` ergänzen (Hash aus dem Release übernehmen):

   ```text
   auditcore_price_analysis @ https://github.com/janpow77/auditcore/releases/download/v0.3.0/auditcore_price_analysis-0.1.0-py3-none-any.whl#sha256=<aus Release>
   ```
2. Patch `docs/migrations/regulierung-price.patch` anwenden (Teil `calculator.py`,
   `preisauswahl.py`).
3. Tests wie oben gegen eine Wegwerf-Datenbank ausführen.

## Weiterer Schritt: korrigierter Vertrag (empfohlene Profile @2026.09.2)

Neue Aufrufe nutzen die entschiedenen Profile:

```python
from auditcore_price_analysis import (
    ReleaseStatus,
    Tariff,
    calculate,
    load_recommended_calculation_profile,
    standard_consumption,
)

profil = load_recommended_calculation_profile("regulierung.hpp.wasser")  # @2026.09.2
tarif = Tariff.from_mapping(
    preisdaten,
    profil,
    release=ReleaseStatus.from_legacy(p.freigabe_status),
    valid_from=p.valid_from,
    valid_to=p.valid_to,
    q3=p.zaehlergroesse_q3,
)
verbrauch = {"q3": settings.wasser_standard_q3, "m3": settings.wasser_standard_m3}  # 180 m³
ergebnis = calculate(tarif, profil, consumption=verbrauch, stichtag=stichtag)
```

- **PA-H03 (180 m³, eine Quelle):** Der Vorgabewert **150 m³** des Rechners
  wird ersetzt. Heute rufen `calculate_wasser` ohne `m3` auf und bekommen damit
  150 m³: `api/export_routes.py` (Zeilen 258, 596), `api/provider_routes.py`
  (963), `services/flagging.py` (427, 725, 728, 836). Diese Aufrufe übergeben
  künftig `m3=settings.wasser_standard_m3` (180), wie es
  `api/calculate_routes.py` bereits tut; `standard_consumption(profil)` liefert
  denselben Wert für Prüfungen. Die Einstellung bleibt die einzige Quelle.
- **PA-H01:** `ergebnis.completeness == "unvollstaendig"` in der Oberfläche
  anzeigen; die Vergleichbarkeit bleibt bestehen.
- **PA-H02:** `delta_pct`, `traffic_light`, `group_statistics` statt der
  Legacy-Gleitkommafunktionen.
- **PA-H04:** `select_tariff(..., profile=load_recommended_comparison_profile("regulierung.hpp.vergleich"))`
  schließt abgelaufene Preiszeilen (`valid_to`) aus.
- `None` durchreichen statt `float(x or 0)`, sonst bleibt ein fehlender Preis
  unsichtbar.

## Ab 0.1.2: deutsche Zahlentexte (PA-C01)

`parse_decimal` liest Texte wie „1.234,56 €“ oder „10,82“ jetzt selbst
(bisher `invalid_number`); mehrdeutige Texte („1,234“) ergeben
`ambiguous_number`. Punkttext, `Decimal` und `float` rechnen unverändert.
regulierung übergibt Preise aus der Datenbank als Zahl und ist deshalb nicht
betroffen; wer Eingaben aus Formularen oder CSV durchreicht, sollte
`ambiguous_number` wie `invalid_number` als Eingabefehler anzeigen (Meldung
enthält den Hinweis). Pflichtabhängigkeit `auditcore_common==0.1.1`.
