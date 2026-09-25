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
| PA-L15 | Zahlentext mit Exponent („1e2“) wird als 100 akzeptiert (nw-ungueltig-010) | Nur einfache Dezimalschreibweise, kein Exponent; bis 0.1.1 wurde jedes Dezimalkomma abgelehnt, ab 0.1.2 wird deutsche Schreibweise gelesen → **PA-C01** |
| PA-L16 | Unbekannte Preisschlüssel werden ignoriert (Tippfehler bleiben unbemerkt, nw-ungueltig-015) | Fehler `unknown_component`; zusätzliche Angaben in Staffelstufen werden in `issues` genannt |
| PA-L17 | Q3-Toleranz im Gleitkomma: \|4,01 − 4,0\| gilt als Treffer (wasser-auswahl-005) | Exakter Vergleich `< 0,01`; 4,01 ist Rückfall mit `nicht_verfuegbar_fuer_q3` |

## Korrekturen nach Veröffentlichung (PA-C)

| Nr. | Bis 0.1.1 (jetzt `legacy_parse_decimal`) | Ab 0.1.2 (`parse_decimal`) | Grundlage |
|---|---|---|---|
| PA-C01 | Zahlentext nur mit Dezimalpunkt; jedes Komma → `invalid_number` („Dezimalkomma wird nicht umgedeutet“). Deutsche Beträge wie „1.234,56“, „1234,56“ oder „10,82“ waren nicht lesbar (Original regulierung ebenso: nw-verbrauch-013, nw-ungueltig-001, wa-verbrauch-011, wa-ungueltig-001, wa-staffelform-025/026). | Einfacher Punkttext (`"2.5"`, `"1.234"`, `".5"`) bleibt das eigene Textformat des Pakets und behält seinen Wert. Jeder andere Text wird nach dem gemeinsamen Vertrag `contracts/common-cases/parse-number.json`, Modus `de`, über `auditcore_common.numbers_de` gelesen: Dezimalkomma, Punkte nur als Tausendertrenner in Dreiergruppen, höchstens zwei Nachkommastellen, `€`/`EUR`/Leerraum erlaubt („1.234,56 €“ → 1234.56, „1.000.000“ → 1000000). Mehrdeutiges („1,234“, „0,125“, „1.234 €“) → neuer Code `ambiguous_number` mit Hinweis statt einer geratenen Zahl; sonst `invalid_number`. `Decimal`, `int` und `float` unverändert. | Nutzerauftrag 25.09.2026 („deutsche Beträge korrekt lesen“), Festlegungen in `contracts/common-cases/DECISIONS.md`. Drei oder mehr Nachkommastellen (Arbeitspreise in ct/kWh) weiter in Punktschreibweise oder als `Decimal`. Tests: `tests/test_parse_decimal_de.py` (alle `de`-Fälle des Vertrags mit Komma bzw. Währung; die vier Punkttexte „1.5“, „1.23“, „1.234“, „-1.234“ sind hier bewusst Dezimalzahlen), Rechnung mit Kommatext gleich Rechnung mit Punkttext. |

## Beobachtungen am Consumer (nicht Teil der Bibliothek)

- Viele Aufrufer in regulierung übergeben `float(p.arbeitspreis_ct_kwh or 0)`
  (u. a. `provider_routes.py`, `clustering.py`, `export_routes.py`). Damit wird
  ein fehlender Preis schon **vor** dem Rechenkern zu 0, und
  `vergleichsfaehig`/`fehlende_komponenten` können nicht mehr anschlagen. Bei
  der Umstellung `None` durchreichen (siehe `consumer-migration.md`).
- Freigabestatus: Die DB-Lader filtern `freigabe_status == "approved"` und
  `stichtag <= Stichtag`; `select_tariff` bildet genau diese Regeln ab und
  listet ausgeschlossene Zeilen mit Grund. Die Bibliothek setzt nie einen Status.

## Entscheidungen (DECIDED, 23.09.2026)

Nutzerentscheidung vom 23.09.2026, Zitat: „alle empfehlungen … p3 180“. Umgesetzt in den empfohlenen
Profilen `regulierung.hpp.nahwaerme`, `.wasser`, `.vergleich` **@2026.09.2**
(`recommended: true`, `load_recommended_calculation_profile`,
`load_recommended_comparison_profile`). Die charakterisierten Profile
@2026.09.1 und das Legacy-Modul bleiben bitgenau unverändert.

- **PA-H01 – DECIDED:** Fehlende optionale Preisbestandteile schließen die
  Vergleichbarkeit nicht aus; das Ergebnis wird sichtbar als
  `vollstaendigkeit: unvollstaendig` markiert (`CalculationResult.completeness`,
  Summe als Untergrenze, Lücken in `missing_optional`).
- **PA-H02 – DECIDED:** Abweichung, Ampel und Gruppenstatistik mit exakter
  Dezimalrundung (ROUND_HALF_UP) – `delta_pct`, `traffic_light`,
  `group_statistics` des korrigierten Vertrags.
- **PA-H03 – DECIDED:** Standardverbrauch Wasser **180 m³**, einzige Quelle ist
  die Einstellung `wasser_standard_m3`; das Profil @2026.09.2 nennt ihn
  (`standard_consumption`). Der Vorgabewert 150 m³ gilt nur noch im
  Legacy-Modul (bitgenaue Nachbildung) und entfällt bei der Umstellung.
- **PA-H04 – DECIDED:** `valid_to` der Preiszeile wird bei der Tarifauswahl
  beachtet (`selection.respect_valid_to: true`, Ausschlussgrund `abgelaufen`).

## REVIEW_REQUIRED

- **Umlagenstichtag 01.07.2025:** Recherche vom 23.09.2026 ohne belastbare
  Rechtsgrundlage für einen Wechsel zu einem „Wärmeumlagenpreis“. Zum
  01.07.2025 änderte sich nur die Höhe der Gasspeicherumlage nach § 35e EnWG
  (0,289 ct/kWh); die Umlage entfiel erst zum 01.01.2026 durch Änderung des
  EnWG (Bundestag 06.11.2025, Bundesrat 21.11.2025). Für Fernwärme gilt das
  EnWG nicht unmittelbar (Preisänderungsklauseln nach AVBFernwärmeV). Der
  „Wärmeumlagenpreis“ ist danach ein vertraglicher Preisbestandteil. Wert
  unverändert, Status und Quellen im Profil @2026.09.2 (`legal_dates`).
- Datenrechte: keine Versorgerdaten enthalten (synthetische Fixtures).
