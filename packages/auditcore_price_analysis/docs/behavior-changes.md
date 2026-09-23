# Beobachtetes Originalverhalten und bewusste Korrekturen

Quelle: `janpow77/regulierung@853676d2` (`services/calculator.py`,
`services/preisauswahl.py`). `tools/capture_regulierung_calculator.py` hat das
Original tatsächlich ausgeführt; **274 Fälle** stehen mit Eingabe und Ergebnis
bzw. Fehler in `tests/fixtures/regulierung_calculator_observed.json`.

- `auditcore_price_analysis.legacy` reproduziert **alle 274 Fälle exakt**
  (Werte, Gleitkommadarstellung, Fehlertyp und Fehlertext).
- Der neue Vertrag (`calculate`, `select_tariff`, `delta_pct`,
  `traffic_light`, `group_statistics`) liefert in allen Fällen, in denen beide
  Seiten rechnen, dieselben gerundeten Beträge, Summen und dieselbe
  Vergleichbarkeit. Jede Abweichung ist unten mit Nummer belegt und in
  `tests/test_contract_vs_legacy.py`, `test_comparison.py` und
  `test_selection.py` fallgenau festgeschrieben.

## Legacy-Befunde (PA-L) und neuer Vertrag

| Nr. | Beobachtung im Original (Fall-ID) | Neuer Vertrag |
|---|---|---|
| PA-L01 | Fehlender Verbrauch (`kw`, `kwh`, `m3`, `q3` = `None`) zählt still als 0; Ergebnis bleibt „vergleichsfähig“ (nw-verbrauch-009/010, wa-verbrauch-009, wa-q3-004) | Jede Verbrauchsgröße des Profils ist Pflicht, `missing_value`; keine Vorgabewerte |
| PA-L02 | Nur Grund- und Arbeitspreis gelten als Pflicht; fehlende Verrechnungs-, Emissions-, Umlage- oder WEE-Preise zählen still als 0 (nw-fehlt-*, wa-fehlt-*) | Fehlende optionale Bestandteile stehen in `missing_optional`, Zeilenstatus `fehlt`, Summe als Untergrenze (`total_is_lower_bound`). Ob sie die Vergleichbarkeit ausschließen, ist Profilregel → **PA-H01** |
| PA-L03 | Staffelstufe ohne Preis wird mit 0 €/m³ berechnet (wa-staffelform-015…018) | Fehler `missing_value` |
| PA-L04 | Offene letzte Stufe (`bis_m3` fehlt) wird abgelehnt, obwohl die letzte Stufe ohnehin unbegrenzt gilt; Meldung „muss groesser als 0 sein“ (wa-staffelform-011…014, 019/020) | Offene Grenze nur für die letzte Stufe zulässig und so berechnet; offene Grenze davor ist ein Fehler |
| PA-L05 | Unbekannte Staffelformen (`"50:1.8"`, `{"stufen": …}`, `{}`) werden ignoriert, dann gilt der Einzelpreis oder 0 (wa-staffelform-039…044) | Fehler `invalid_tiers`; nur Liste oder Objekt mit genau `staffeln` |
| PA-L06 | Staffel und Einzelarbeitspreis gleichzeitig: Staffel gewinnt stillschweigend | Gleiches Ergebnis, Hinweis „durch Staffel … überlagert“ in `issues` |
| PA-L07 | Letzte Stufe gilt unbegrenzt, auch mit deklarierter Grenze (Quellregel) | Beibehalten als Profilregel `open_last`; Überschreitung wird in `issues` genannt. Profile mit `open_last=false` lehnen sie ab (`beyond_last_tier`) |
| PA-L08 | Mischpreis 0 bei Verbrauch 0; Fix-/Variabelanteil 0 %/100 % bei Kosten 0 | `None` (nicht definiert) |
| PA-L09 | `datetime` als Stichtag: TypeError bei Nahwärme, stilles Akzeptieren bei Wasser (nw-stichtag-008, wa-stichtag-004) | Nur Kalendertag (`date` oder `JJJJ-MM-TT`), sonst `invalid_date` |
| PA-L10 | Jede Zeile und die Summe werden einzeln kaufmännisch gerundet; Summe der gerundeten Zeilen kann von der gerundeten Summe abweichen (nw-rundung-009) | Beibehalten; zusätzlich exakte Werte je Zeile und Summe |
| PA-L11 | `calculate_delta`: Gleitkomma und `round` (Banker's Rounding auf Binärwerten): 0,25 → 0,2; Referenz 0 → 0,0; negative Referenz → Wert (delta-004…009) | Exakte Dezimalrechnung, ROUND_HALF_UP; Referenz fehlt oder ≤ 0 → `None` |
| PA-L12 | `determine_compliance`: Median ≤ 0 → „gruen“; Gleitkommaartefakte an den Grenzen (1,1 zu 1,0 → „gelb“ statt „gruen“; 3,6 zu 3,0 → „rot“ statt „gelb“); negative Schwelle wird verarbeitet | Exakte Abweichung; ohne positiven Median `None`; negative Schwelle ist ein ungültiges Profil |
| PA-L13 | Gruppenstatistik: leere Gruppe → alle Kennzahlen 0; `round` auf Binärwerten (2,675 → 2,67) | Leere Gruppe → `None`; exakte ROUND_HALF_UP-Rundung; Populations-Standardabweichung als benannte Profilvariante (`sample` möglich) |
| PA-L14 | Komponente des nicht aktiven Umlagenregimes wird nicht geprüft (negativer Wert akzeptiert, nw-umlage-005) | Alle Bestandteile werden validiert; nicht anwendbare Zeile mit Status `nicht_anwendbar` |
| PA-L15 | Zahlentext mit Exponent („1e2“) wird als 100 akzeptiert (nw-ungueltig-010) | Nur einfache Dezimalschreibweise; Dezimalkomma wird nie umgedeutet |
| PA-L16 | Unbekannte Preisschlüssel werden ignoriert (Tippfehler bleiben unbemerkt, nw-ungueltig-015) | Fehler `unknown_component`; zusätzliche Angaben in Staffelstufen werden in `issues` genannt |
| PA-L17 | Q3-Toleranz im Gleitkomma: \|4,01 − 4,0\| gilt als Treffer (wasser-auswahl-005) | Exakter Vergleich `< 0,01`; 4,01 ist Rückfall mit `nicht_verfuegbar_fuer_q3` |

## Beobachtungen am Consumer (nicht Teil der Bibliothek)

- Viele Aufrufer in regulierung übergeben `float(p.arbeitspreis_ct_kwh or 0)`
  (u. a. `provider_routes.py`, `clustering.py`, `export_routes.py`). Damit wird
  ein fehlender Preis schon **vor** dem Rechenkern zu 0, und
  `vergleichsfaehig`/`fehlende_komponenten` können nicht mehr anschlagen. Bei
  der Umstellung `None` durchreichen (siehe `consumer-migration.md`).
- Freigabestatus: Die DB-Lader filtern `freigabe_status == "approved"` und
  `stichtag <= Stichtag`; `select_tariff` bildet genau diese Regeln ab und
  listet ausgeschlossene Zeilen mit Grund. Die Bibliothek setzt nie einen Status.

## HUMAN_DECISION_REQUIRED

- **PA-H01** Sollen fehlende optionale Bestandteile (Verrechnungspreis,
  Emissionspreis, Umlage des geltenden Regimes, Wasserentnahmeentgelt) die
  Vergleichbarkeit ausschließen? Legacy: nein. Profil
  `optional_missing_blocks_comparison` ist `false` (wie Legacy); die Lücke ist
  aber immer sichtbar.
- **PA-H02** Umstellung von Abweichung, Ampel und Gruppenstatistik auf exakte
  Dezimalrundung (PA-L11 bis PA-L13) ändert Anzeigen an Grenzwerten.
- **PA-H03** Standardverbrauch Wasser: `calculate_wasser` nutzt 150 m³
  (Aufrufer `export_routes`, `provider_routes`, `flagging`), die Einstellung
  `wasser_standard_m3` ist 180 m³ (Aufrufer `calculate_routes`). Der neue
  Vertrag verlangt den Verbrauch ausdrücklich und entscheidet das nicht.
- **PA-H04** Soll `valid_to` einer Preiszeile bei der Tarifauswahl beachtet
  werden? Legacy: nein (nur `valid_to` der Standardvariante). Profilregel
  `respect_valid_to` ist `false`.

Der Umlagenstichtag 01.07.2025 steht im Profil mit `SOURCE_STATED`; die
Rechtsquelle ist in regulierung nicht zitiert und wurde hier nicht geprüft.
