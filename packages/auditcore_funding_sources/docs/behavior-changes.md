# Legacyverhalten, bewusst korrigiertes Verhalten und offene Entscheidungen

Grundlage sind tatsächlich ausgeführte Originale (`tools/capture_legacy.py`):

| Quelle | Revision | Aufgezeichnet |
|---|---|---|
| flowworkshop | `a05bb2143bd96d5e981f9462f05b965e1658be36` | 315 Fälle; zusätzlich 11 Harvest-Läufe gegen eine Wegwerf-PostgreSQL |
| flowsearch | `10cb2a3ead3892cbf9fa94f2ed18763187d3e0e4` | 112 Fälle |
| audit_designer | `030a71e083ef0feddc14545b095a4945bc0bbd7a` | 384 Fälle, darunter 7 De-minimis-Ernteläufe auf In-Memory-SQLite |

Die Profile `flowworkshop`, `flowsearch` und `designer` bleiben **getrennt**.
Ähnliche Funktionsnamen belegen keine gleiche Semantik: `parse_betrag`
(Designer) versteht Tausenderpunkte ohne Komma, `parse_amount`
(flowworkshop) nicht; flowsearch setzt fehlende Beträge auf `0.0`; die drei
Identitäten (SHA-256 flowworkshop, SHA-256 Designer, MD5 flowsearch) sind
nicht austauschbar. Sämtliche Funktionen der Profilmodule reproduzieren das
Original exakt. Korrekturen sind nur als ausdrücklich gewählte Option oder im
neuen Vertrag wirksam.

## flowworkshop

| ID | Beobachtung im Original | Bibliothek | Begründung |
|---|---|---|---|
| FS-W01 | `compute_record_hash` enthält `bundesland`, `periode`, `fonds`; geparste Zeilen tragen diese Felder nicht, sie gehen als leere Zeichenkette ein. | Unverändert. | Änderung würde alle gespeicherten Identitäten ändern. **HUMAN_DECISION_REQUIRED**, ob der Quellkontext Teil der Identität sein soll. |
| FS-W02 | pandas-Typinferenz: PLZ `01067` wird `1067`. | `typing="legacy"` wie Original; `typing="text"` erhält `01067`. | Führende Nullen sind Teil der PLZ; Umstellung ändert Identitäten nicht, aber Feldwerte. |
| FS-W03 | Eine Lücke in einer Zahlenspalte macht aus `150000` den Rohwert `150000.0`; der Hash hängt damit von anderen Zeilen der Datei ab. | `legacy` wie Original, `text` stabil. | Identität darf nicht vom Dateikontext abhängen; Umstellung ändert Hashes → **HUMAN_DECISION_REQUIRED** pro Consumer. |
| FS-W04 | CSV mit Titelzeilen, die weniger Felder als die Kopfzeile haben, bricht mit `ParserError` ab. | Titelzeilen werden übersprungen. | Typische Transparenzliste; der Abbruch verhinderte jeden Import. |
| FS-W05 | `parse_amount("1.234.567")` ergibt `None`. | Unverändert im Profil; Designer-Variante liest es. | Keine stille Harmonisierung. |
| FS-W06 | Summen-/Leerzeilen zählen als `failed`, jeder übliche Lauf endet `partial`. | Plan und Adapter zählen gleich; Adapter meldet sie als `RecordIssue`. | Sichtbar statt verschluckt. |
| FS-W07 | `full-refresh` zählt überschriebene Zeilen als `inserted`; `smart` legt geänderte Zeilen **zusätzlich** an. | Unverändert und dokumentiert. | Lösch-/Bestandssemantik nicht still ändern. |
| FS-W08 | Eine erste Datenzeile mit ≥ 3 rein numerischen Zellen gilt als zweite Kopfzeile; sie geht verloren und die Spaltenzuordnung zerfällt. | `header_detection="legacy"` wie Original, `"strict"` verlangt Buchstaben in der Zweitkopfzeile. | Nachgewiesener Datenverlust (`erste_zeile_numerisch.csv`). |

Die Modi `smart`, `full-refresh`, `force` und `snapshot` sind kein Parser-
Schalter, sondern ein Bestandsplan (`snapshot.plan_snapshot`). Die Texte
„force-mode: … geloescht“ stammen wörtlich aus dem Original.

## flowsearch

| ID | Beobachtung | Bibliothek |
|---|---|---|
| FS-S01 | Fehlender oder unlesbarer Betrag wird `0.0`. | Unverändert; `record_values` meldet betroffene Felder in `defaulted`. |
| FS-S02 | Identität MD5 über Schlüssel, Name, Titel, Beginn (16 Hex). | Unverändert, eigener Adapter `funding.eu_beneficiaries.flowsearch`. |
| FS-S03 | ZIP-Mitglied wird ohne Größenprüfung gelesen. | Grenze 64 MiB je Tabellendatei. |
| FS-S04 | Leere oder unlesbare Datei ergibt „0 Datensätze“ ohne Fehler (Codebefund, nicht ausgeführt). | Adapter: `ParserError` statt leerem Erfolg. |

## Designer / De-minimis

| ID | Beobachtung | Bibliothek |
|---|---|---|
| FS-G01 | `parse_betrag(True)` wirft `InvalidOperation`. | Im Profil unverändert. |
| FS-D01 | Unerwartete JSON-Form des Registers wird zur leeren Liste („kein Treffer“). | `parse_award_list(strict=True)` wirft; `strict=False` nur für den Legacyvergleich. |
| FS-D02 | `bestandsstand` meldet nach einem fehlgeschlagenen Lauf den letzten erfolgreichen Stand als vollständig, obwohl der Fehllauf Zeilen geschrieben hat. | `inventory_state` meldet den neuesten Lauf; vollständig nur, wenn er `ok` ist (`legacy=True` für das Original). |
| FS-D03 | `stand_am`/`inhaltshash` hängen von der Sortierung nach `started_at` ab (Sekundenauflösung). | Neuester Lauf über eine eindeutige Reihenfolge. |
| FS-D04 | Unvollständige Ernte (Gesamtzahl nicht erreicht oder unbekannt) markiert nichts als verschwunden. | Übernommen; Adapter meldet Teilbestand als `partial`, `snapshot_complete` nur bei erreichter Gesamtzahl. |
| FS-D05 | Negative Beträge verringern die Summe der Kumulierung. | Neuer Vertrag: `unclear`, keine Gegenüberstellung. **HUMAN_DECISION_REQUIRED** (Rückforderung/Korrektur?). |
| FS-D06 | Die Kumulierung summiert alle übergebenen Meldungen einer Referenz. | Unternehmen ausdrücklich als Referenzliste; andere Referenzen `excluded`. |
| FS-D07 | Stichtag „heute“ als Vorgabe (Codebefund). | Stichtag verpflichtend. |

Unverändert übernommen: Höchstbetrag 300 000 EUR nur bei ausschließlich
`GENERAL`, keine Grenze für `AGRI`, Fenster drei Kalenderjahre mit beiden
Randtagen (29.02. → 28.02.), Behördenzuordnung nach sichtbaren Regeln mit
amtlichem Präfix zuerst, Maskierung natürlicher Personen (`***`).

## Offene fachliche Entscheidungen (HUMAN_DECISION_REQUIRED)

1. Kumulierungsprofil `designer.deminimis.cumulation` ist `REVIEW_REQUIRED`:
   Gültigkeitszeitraum (`valid_from`/`valid_to`) nicht festgelegt; Randtage und
   Kalenderjahresregel gegen Art. 3 Abs. 2 VO (EU) 2023/2831 fachlich prüfen;
   Umgang mit Agrar-/Fischerei-Regelungen und negativen Beträgen.
2. FS-W01/W03: Umstellung bestehender Bestände auf `typing="text"` bzw. eine
   Identität mit Quellkontext ändert Hashes und damit Dublettenerkennung.
3. Welche der Varianten (flowworkshop/flowsearch/Designer) künftig führend ist;
   bis dahin keine Zusammenführung.
4. Datenlizenzen und Nutzungsbedingungen je Quelle (Länderlisten, eAidRegister).
