# Paritätsinventur „Synopse / Versionsvergleich“

Stand: 25.09.2026. Gegenstand: wiederverwendbare Oberfläche `<flowaudit-synopsis>`
(`@flowaudit/ui`, Vue 3 + Web Component, React-Wrapper in `@flowaudit/ui-react`)
und REST-Anbindung `auditcore_documents.web` (0.3.0). Vertrag:
[`synopsis-rest.md`](synopsis-rest.md).

## Vorbilder

| Kürzel | Quelle | Stand |
|---|---|---|
| AD | `janpow77/audit_designer` `frontend/src/views/DocumentComparisonView.vue`, `backend/app/api/document_comparisons.py` | `2c726f3c` |
| ECO | `janpow77/audit_designer` `frontend/src/ecohesion/views/DocumentComparisonView.vue`, `backend/app/modules/ecohesion/comparisons/api.py` | `2c726f3c` |
| AD-V | `audit_designer` `frontend/src/components/editor/VersionCompareModal.vue`, `TreeVersionDiffModal.vue` (Knoten-/Baumversionen einer Checkliste) | `2c726f3c` |
| AD-W | `audit_designer` `frontend/src/components/vpai/pdf-tools/WordDiff.vue` (Wortvergleich zweier Dateien mit Filter) | `2c726f3c` |
| REG | `janpow77/regulierung` `frontend/src/components/kraftstoff/RulebookVersionDiffModal.tsx`, `frontend/src/lib/textDiff.ts` (Regelwerksversionen, wortweiser LCS-Vergleich) | `ce76e48c` |

Kein Code wurde übernommen; Beschriftungen, Grenzen und Meldungen folgen den
Vorbildern, damit Nutzer beider Anwendungen dieselben Begriffe sehen.

## Legende

**R** = REST-Anbindung 0.3.0 (dieser Stand, getestet) · **U** = Oberfläche
`@flowaudit/ui` (eigener PR, sobald `packages-js/ui` in main ist) ·
**A** = bleibt bewusst Sache der Anwendung · **–** = nicht übernommen (Grund)

## Inventar

### Auftrag anlegen

| Funktion | Vorbild | Status | Bemerkung |
|---|---|---|---|
| Zwei Dateien hochladen (DOCX, DOCM, PDF), Drag-and-drop | AD, ECO | R, U | Endung und Größe serverseitig geprüft (415/413) |
| Größengrenze je Datei | AD 100 MB, ECO 10 MB | R | `ServiceSettings.max_upload_bytes`, Vorgabe 20 MiB |
| Fassungen tauschen | AD | U | reine Oberflächenfunktion |
| Titel, aus Dateinamen vorbelegt („Vergleich von … mit …“) | AD, ECO | R, U | gleiche Vorbelegung serverseitig |
| Anwendungsfall: zwei Fassungen / Artikelgesetz auf Stammgesetz | AD | R, U | `comparison_type` |
| Dokumentart automatisch / Checkliste / Fließtext | AD, ECO | R, U | `mode` |
| Ähnlichkeitsschwelle 70–100 | AD, ECO | R, U | `threshold` |
| Inhalte: Antworten/Bemerkungen, Hinweise, redaktionelle Unterschiede, Wörter hervorheben | AD, ECO (redaktionell) | R, U | `include_*`, `highlight_words` |
| Auszugebende Abschnitte | AD | R, U | `output_sections` |
| Vergleichsprofil wählen | – (neu) | R, U | `GET /profiles`; Legacy-Profile nur, wenn freigegeben |
| Bezeichnungen der Fassungen frei wählen („Alte/Neue Fassung“) | AD | U | Anzeige; Gesetzessynopse liefert „Geltende Fassung“/„Fassung nach dem Entwurf“ aus `metadata` |
| PDF-Hinweis (Fließtext, keine nachverfolgten Änderungen) | AD, ECO | R, U | `metadata.pdf_notice` |
| Dokumente aus dem Vorhabenbestand wählen | AD | A | Bestand und Rechte gehören der Anwendung; sie übergibt Dateien oder importiert Ergebnisse |
| Hintergrundauftrag mit Fortschritt und Abfrage alle 1,5 s | AD, ECO | A | REST vergleicht synchron im Worker-Thread; lange Läufe steuert die Anwendung und legt das Ergebnis per `POST /comparisons/import` ab. Die Oberfläche zeigt einen Ladezustand |
| Begründungsvorschläge über FlowAgent, Modellwahl | AD | A | Port `ReasonProvider`/`apply_reasons_worker` im Kern; Anzeige von `reason_source`, `reason_verified`, `reason_warning` ist **U** |
| Persönliche/Referatsvorgaben, Voreinstellungen, Layout des Vermerks (Briefkopf, Schrift, Farbe, Gliederung) | AD | A | Einstellungsspeicher und Rechte gehören der Anwendung; `auditcore_documents.settings` bietet Laden/Speichern/Bereinigen |

### Ergebnis ansehen

| Funktion | Vorbild | Status | Bemerkung |
|---|---|---|---|
| Kopf: Dateien, Zählwerte (geändert, entfallen, neu, verschoben, zugeordnet), Dokumentart, Modulversion | AD, ECO | R, U | aus `ComparisonResult` |
| Seiten-an-Seite-Ansicht (alt links, neu rechts) | AD (Tabelle), ECO (Karten), AD-V, REG | U | beide Spalten mit Überschrift je Fassung |
| Inline-Ansicht (Streichungen und Einfügungen in einem Text) | AD-W | U | neu gegenüber AD/ECO |
| Wortweise Hervorhebung (gestrichen/neu) | ECO, AD-V, REG | U | aus `row.diff` (ndiff); fehlt sie (Gesetzessynopse), LCS über Wörter wie REG mit Obergrenze |
| Antworten, Bemerkungen, Hinweise je Seite | AD, ECO | U | mit eigener Wortdifferenz je Feld |
| Status je Zeile mit deutschem Namen | AD, ECO | U | „Geändert“, „Neu“, „Entfallen“, „Verschoben“, „Unverändert“ |
| Filter nach Änderungsart, „Alle Änderungen“ | ECO, AD-W, REG | U | Mehrfachauswahl |
| Volltextsuche in Fundstelle und Text | ECO | U | |
| Navigation zur vorigen/nächsten Änderung (Tasten, Zähler „3 von 12“) | – (neu) | U | Fokus und Scrollen zur Zeile |
| Artikel-/Paragraphen-Synopse: alte Fassung, neue Fassung, Änderungsbefehl | AD | R, U | `reason` mit `metadata.reason_label` |
| Erkannte und offene Änderungsbefehle mit Grund | AD | R, U | `recognised_commands`, `open_commands` |
| Konsolidierte Arbeitsfassung | Kern (`consolidated_text`) | U | in AD nur im DOCX |
| Hinweis „Arbeitshilfe, keine Prüfungsentscheidung“ | AD, Kern | U | fester Hinweis plus `work_aid_notice` |
| Leerer Zustand („Keine passenden Unterschiede …“) | ECO | U | |

### Vorschau bearbeiten und ausgeben

| Funktion | Vorbild | Status | Bemerkung |
|---|---|---|---|
| Zeilen für die Ausgabe an-/abwählen | AD | R, U | `PATCH …/rows` (`selected`) |
| Grund je Zeile bearbeiten | AD | R, U | `PATCH …/rows` (`reason`, ≤ 4000 Zeichen) |
| DOCX-Ausgabe (Vermerk/Text) | AD, ECO | R, U | Extra `docx-render`; Layoutwerte bleiben Sache der Anwendung |
| PDF-Ausgabe | ECO | R, U | Extra `pdf-render`; neutrale Kopfzeile „Synopse“ statt ECOHESION |
| JSON-Ausgabe | ECO | R, U | |
| Markdown-Ausgabe | – (neu) | R, U | serverseitig und in der Oberfläche |
| HTML-Ausgabe und Druckansicht | – (neu) | U | eigenständiges HTML mit Druck-CSS aus dem View-Model |
| „Geprüftes DOCX erzeugen“ mit Löschen der Uploads | AD | – | REST speichert keine Uploads; das Ergebnis ist jederzeit ausgebbar |
| Verlauf mit Öffnen und Löschen, Bestätigung vor dem Löschen | AD, ECO | R, U | nur eigene Vergleiche |
| Aufbewahrungsfrist, „Löschung steht bevor“, Protokolleintrag bleibt | AD | A | Aufbewahrung und Protokoll gehören zur Persistenz der Anwendung |
| Zeilen-/Feldvergleich von Checklistenknoten mit Wiederherstellen | AD-V | – | anderer Gegenstand (Baumknoten); die Oberfläche kann Knotenversionen als `ComparisonResult` anzeigen, Wiederherstellen bleibt dort |

### Querschnitt

| Anforderung | Status | Umsetzung |
|---|---|---|
| Deutsche Texte mit echten Umlauten | R, U | Textkatalog in einer Datei; Fehlermeldungen des Servers deutsch |
| Barrierearm | U | Tabellen- bzw. Artikel-Semantik, Überschriften je Spalte, Status nicht nur über Farbe (Text und Unter-/Durchstreichung), `aria-live` für Navigation und Ladezustand, Tastatur („n“/„p“, „j“/„k“), sichtbarer Fokus, reduzierte Bewegung |
| Dark Mode | U | CSS-Variablen, `prefers-color-scheme` und Attribut `theme` |
| Framework-freie Anzeige-Logik | U | View-Model (`buildSynopsisView`, Wortdifferenz, Navigation, Export) ohne Vue |
| Web Component und React | U | `<flowaudit-synopsis>`, `FlowauditSynopsis` in `@flowaudit/ui-react` |
| Mandantentrennung | R | `identify` je Anfrage, 404 für fremde Vergleiche |
| Keine Datenbank, kein Celery im Paket | R | Port `ComparisonStore` |
