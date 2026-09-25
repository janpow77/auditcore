# Parität zum BPMN-Editor im audit_designer

Stand: 25.09.2026. Grundlage ist `origin/main` des audit_designer
(`frontend/src/modules/flowstat/…` und `backend/app/modules/flowstat/…`).
Jede Funktion des bisherigen Editors ist hier einer Stelle in den neuen
Paketen zugeordnet, damit beim Umstieg nichts verloren geht.

Pakete:

- **flowaudit** = `@flowaudit/bpmn-flowaudit` (`packages-js/bpmn-flowaudit`),
  framework-freie Fachschicht
- **vue** = `@flowaudit/bpmn-vue` (`packages-js/bpmn-vue`), Oberfläche
- **Kern** = `@flowaudit/bpmn-editor` (`packages-js/bpmn-editor`), Zeicheneditor
- **App** = die einbindende Anwendung (liefert die Ports)

Status: **übernommen** (Verhalten gleich, Tests portiert), **erweitert**
(übernommen und fachlich ausgebaut), **ersetzt** (gleiche Aufgabe, neuer
Weg, weil der alte Weg auf bpmn-js-Interna beruhte), **App** (bleibt
Aufgabe der Anwendung, Bibliothek bietet den Port), **offen**.

Clean-Room: Übernommen wurde nur FlowAudit-eigener Code des Nutzers.
Alles, was im audit_designer auf `bpmn-js`, `bpmn-js-properties-panel`,
`@bpmn-io/properties-panel` oder `bpmn-font` aufsetzte, ist neu geschrieben
(eigene Panels in Vue, eigene SVG-Symbole, Dienste des eigenen Kerns).

## 1. Fachmodule (`frontend/src/modules/flowstat/bpmn/*.ts`)

| audit_designer | Funktion | Neuer Ort | Status |
|---|---|---|---|
| `flowauditModdle.ts` | moddle-Deskriptor `flowaudit` 1.0 (`Rechtsgrundlage`, `InterneNotiz`, tagAlias lowerCase), `METADATEN_TYPEN` | flowaudit `schema/descriptor.ts` (Schema 1.0 + 1.1 nach `docs/bpmn/flowaudit-schema-1.1.md`), `schema/konstanten.ts` | erweitert |
| `extensionElements.ts` | `leseMetadatum`, `schreibeMetadatum` (ein Undo-Schritt, leerer Text entfernt Eintrag, leeres `extensionElements` fällt weg) | flowaudit `modell/extensionElements.ts` (gleiche Signaturen) + `modell/erweiterungen.ts` (alle 1.1-Typen, Listen) | erweitert |
| `flowauditPropertiesProvider.ts` | Gruppe „Fachliche Angaben“ (Rechtsgrundlage, interne Notiz) im bpmn-js-Properties-Panel | vue `EigenschaftenPanel.vue` mit Registerkarten „Rechtsgrundlagen“ und „Notizen“ (eigene Vue-Felder, kein preact, kein properties-panel) | ersetzt |
| `farbpalette.ts` | Palette validiert/kritisch/systemisch/inaktiv, `normalisiereFarbe`, `findeFarbe` | flowaudit `darstellung/farbpalette.ts` (unverändert) + Feststellungsfarben aus Kennzeichen (`darstellung/feststellungsfarben.ts`) | erweitert |
| `farbContextPad.ts` | Kontextpad-Eintrag „Farbe festlegen“, Ereignis `flowaudit.farbe.oeffnen`, `setzeFarbe` über `modeling.setColor` | flowaudit `darstellung/farbContextPad.ts` (eigenes Symbol, gleiche Ereignisse) + vue `FarbAuswahl.vue` | übernommen |
| `seitenformate.ts` | DIN A4/A3, hoch/quer, `seitenMasse`, `berechneRaster` | flowaudit `layout/seitenformate.ts` + vue `Seitenraster.vue` | übernommen |
| `flussrichtung.ts` | `wendeRichtungAn`, `haltRichtung` (Pools/Bahnen drehen, neue Pools nachdrehen) | flowaudit `layout/flussrichtung.ts` | übernommen |
| `svgAufbereitung.ts` | Titel, Farblegende, Rechtsgrundlagen-Verzeichnis mit Marken, Fußzeile; `leseFuellfarbe`, `sammleFarben` | flowaudit `export/svgAufbereitung.ts`; zusätzlich Kopfzeile (Titel/Untertitel/Farben), Kennzeichen-Legende, strukturierte Rechtsgrundlagen | erweitert |
| `bildExport.ts` | `ladeHerunter`, `dateiname`, `svgNachPng` (2-fache Auflösung, weißer Grund) | flowaudit `export/bildExport.ts` + neu `export/pdf.ts` (PDF im Browser, ohne Server) | erweitert |
| `mystExport.ts` | `base64Utf8`, `diagrammKennung`, `baueMystSchnipsel`, `inZwischenablage` | flowaudit `export/mystExport.ts` + Prozesstabelle als MyST (`berichte/prozesstabelle.ts`) | erweitert |
| `exportTypen.ts` | Formate svg/png/bpmn/excel/pdf/myst, Titel, Legende/Metadaten/Rechtsgrundlagen | flowaudit `export/exportTypen.ts` (zusätzlich csv-Prozesstabelle, RCM, Feststellungsliste, neutral, Seitenformat, Kopfzeile) | erweitert |
| `diagrammBaum.ts` | Gruppierung nach Prozesstyp/Verantwortlichkeit, Filter alle/eigene/geteilt/öffentlich, Suche | flowaudit `sammlung/diagrammBaum.ts` (`baueGruppen` unverändert) + `sammlung/sammlung.ts` (Ordnerbaum, Tags, Reihenfolge) | erweitert |
| `deutschTranslate.ts` | Übersetzungstabelle, `deutschTranslate` mit Platzhaltern, Modul `translate` | Kern `translations` (Grundbegriffe) + flowaudit `i18n/` (de/en für alle Fachbegriffe, `erstelleUebersetzer`, gleiche Platzhalterlogik); Tabelle des audit_designer als `LEGACY_UEBERSETZUNGEN` erhalten | erweitert |
| `__tests__/bpmnErweiterungen.spec.ts` | 20 Tests der Bausteine | flowaudit `test/legacy-paritaet.spec.ts` (alle 20 Fälle portiert) | übernommen |

## 2. Komponenten (`frontend/src/modules/flowstat/components/bpmn/*`)

| audit_designer | Funktion | Neuer Ort | Status |
|---|---|---|---|
| `BpmnCanvas.vue` | bpmn-js-Modeler, Import/Export, XML-Modus (CodeMirror) | vue `FlowauditEditor.vue` (Kern `BpmnEditor`), XML-Ansicht als schlichte Textfläche mit Übernahme | ersetzt |
| `BpmnCanvas.vue` | Seitenansicht (Raster der Seitenumbrüche) | vue `Seitenraster.vue` + `Werkzeugleiste.vue` | übernommen |
| `BpmnCanvas.vue` | Flussrichtung waagerecht/senkrecht | vue `Werkzeugleiste.vue` → flowaudit `flussrichtung` | übernommen |
| `BpmnCanvas.vue` | Zoom +/−/Einpassen | vue `Werkzeugleiste.vue`, Tastenkürzel | übernommen |
| `BpmnCanvas.vue` | Bildlaufleisten (Tastatur/Maus ohne Ziehen) | vue `Bildlauf.vue` | übernommen |
| `BpmnCanvas.vue` | Farbwahl am Element (Popover) | vue `FarbAuswahl.vue`, ausgelöst über `flowaudit.farbe.oeffnen` | übernommen |
| `BpmnCanvas.vue` | gespiegelte Palette in linker Spalte | vue `Palette.vue` (eigene Einträge und Symbole, inkl. „Bahn: VB/ZGS/…“) | ersetzt |
| `BpmnCanvas.vue` | `selectElement` (Sprung zum Element) | vue `FlowauditEditor` → `springeZu(id)` | übernommen |
| `BpmnCanvas.vue` | `leseExportDaten` (verwendete Farben, Rechtsgrundlagen mit Position) | flowaudit `export/exportDaten.ts` | übernommen |
| `BpmnCanvas.vue` | `faerbeAuswahl` | flowaudit `darstellung/farbContextPad.ts` `setzeFarbe` + vue Werkzeugleiste | übernommen |
| `BpmnCanvas.vue` | Dark Mode der Zeichenfläche | vue Theming über CSS-Variablen, `theme="auto|hell|dunkel"` | erweitert |
| `BpmnToolbar.vue` | Name, „ungespeichert“, BVA-Status, Speichern/Neu/Import/Export, Farbe, Prüfen-Menü (Validierung, Prozessanalyse, ESI, Teilen), Spalten ein/aus | vue `Werkzeugleiste.vue` (alle Aktionen; „Teilen“ und „Prozessanalyse“ als Ereignisse an die App) | übernommen |
| `BpmnExportDialog.vue` | Titel, Legende, Metadaten, Rechtsgrundlagen, Formate SVG/PNG/BPMN/Excel/PDF/MyST | vue `ExportDialog.vue` (+ CSV-Prozesstabelle, RCM, Feststellungsliste, neutral, Seitenformat, Kopfzeile; Excel als Ereignis an die App) | erweitert |
| `BpmnPropertiesPanel.vue` | Beschreibung, Prozessverantwortlicher, Prozesstyp; FlowStat-Aufgabenfelder (Dauer, Kosten, Frequenz, Personal, Ressource); BVA-Validierung | vue `DiagrammInfoDialog.vue` (Diagrammfelder), `EigenschaftenPanel.vue` Registerkarte „Allgemein“ (FlowStat-Felder, Altattribute kanonisch schreiben), `HinweisListe.vue` (Validierung) | erweitert |
| `BpmnDiagramTree.vue` | Suche, Filter, Gruppierung, Löschen mit Bestätigung, Status/Version/Datum | vue `DiagrammSammlung.vue` (Ordnerbaum mit Drag-and-drop, Tags, Info-Spalte, beide Gruppierungen des Altbaums) | erweitert |
| `EsiRequirementsDialog.vue` | Anforderungen je Element, Zusammenfassung erfüllt/unklar/fehlend, Sprung zum Element | vue `EsiAnforderungenDialog.vue` + flowaudit `esi/esiAnforderungen.ts` (Normalisierung aller Antwortformen, Status-Ableitung, Gruppierung) | übernommen |

## 3. Composables und Ansicht

| audit_designer | Funktion | Neuer Ort | Status |
|---|---|---|---|
| `useBpmnApi.ts` | REST-Aufrufe `/api/flowstat/bpmn/*`, `extractErrorMessage`, `downloadBlob` | flowaudit `ports.ts` (`SpeicherPort`) + vue `rest/restSpeicherPort.ts` (REST-Vertrag `docs/bpmn/rest-api.md`); Fehlertext-Aufbereitung `fehlertext()` | ersetzt |
| `useBpmnEditor.ts` | `EMPTY_BPMN_XML`, Listen-/Ladezustand, dirty-Kennzeichen, Validierung und Analyse verfallen bei Änderung | vue `useEditorZustand.ts` | übernommen |
| `useBpmnEditor.ts` | `parseTasks`, `updateTaskProperties` (Altattribute lesen, kanonisch schreiben) | flowaudit `modell/flowstatAttribute.ts` | übernommen |
| `useEsiRequirements.ts` | Normalisierung, `deriveStatus` | flowaudit `esi/esiAnforderungen.ts` | übernommen |
| `views/BpmnEditor.vue` | Dreispalten-Layout, Reiter Diagramme/Eigenschaften, Meldungen, Rückfrage bei ungespeicherten Änderungen, Import aus Datei | vue `FlowauditArbeitsplatz.vue` (Sammlung + Editor) und Standalone-App | übernommen |
| `useBpmnEditor.spec.ts` | Altattribute lesen/kanonisch schreiben | flowaudit `test/flowstatAttribute.spec.ts` | übernommen |

## 4. Backend (`backend/app/modules/flowstat/…`)

| audit_designer | Funktion | Neuer Ort | Status |
|---|---|---|---|
| `models/bpmn_diagram.py` | Spalten `header_title`, `header_subtitle`, `header_color`, `header_text_color` | `flowaudit:diagrammInfo` (`titel`, `untertitel`, `kopfzeilenfarbe`, `kopfzeilenTextfarbe`) + Callback `@diagramm-info` an die App | erweitert |
| `models/bpmn_diagram.py` | `color_scheme` (JSON) | Farbpalette ist Teil der Bibliothek; App kann über Prop `farbpalette` eigene Paletten einspeisen | erweitert |
| `models/bpmn_diagram.py` | `comments` (elementId, text, author, resolved) | vue Registerkarte „Notizen“: Kommentare je Element über den Speicher-Port (`kommentare`), interne Notiz im XML | erweitert |
| `models/bpmn_diagram.py` | `process_owner`, `process_type`, `version`, `is_archived` | `diagrammInfo.prozessverantwortlich/prozesstyp/version/status=archiviert` | erweitert |
| `schemas/bpmn.py` | Validierungsergebnis `valid/errors/warnings` | flowaudit `regeln/` (`Hinweis` mit Code, Schwere, Element) + vue `HinweisListe.vue` | erweitert |
| `api/bpmn.py` | CRUD, Validierung, Archiv, Kopfzeile, Farbschema, Kommentare, ESI | REST-Vertrag `docs/bpmn/rest-api.md` (Serverseite = App bzw. `auditcore_bpmn`) | App |
| `api/bpmn_export.py` | Analyse, Excel, PDF (501) | Analyse/Excel: App (Ereignis `analyse`/`export-excel`); PDF jetzt im Browser (flowaudit `export/pdf.ts`) | erweitert |
| `services/bpmn_analyzer.py`, `services/bpmn_export.py` | Kennzahlen, Excel-Export | `auditcore_bpmn` (Python) | App |

## 5. Offene Punkte

- CodeMirror-XML-Editor mit Syntaxhervorhebung: ersetzt durch eine schlichte
  XML-Ansicht (Textfläche, Übernehmen-Knopf). Grund: keine schwere
  Abhängigkeit in der Bibliothek. Die App kann einen eigenen XML-Editor über
  den Slot `xml-ansicht` einsetzen.
- Teilen-Dialog (`ShareResourceDialog`) gehört zur App; die Werkzeugleiste
  sendet nur das Ereignis `teilen`.
