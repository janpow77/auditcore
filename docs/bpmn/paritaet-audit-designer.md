# Parität zum BPMN-Editor im audit_designer

Stand: 25.09.2026. Grundlage ist `origin/main` des audit_designer
(`frontend/src/modules/flowstat/…` und `backend/app/modules/flowstat/…`).
Jede Funktion des bisherigen Editors ist hier einer Stelle in den neuen
Paketen zugeordnet, damit beim Umstieg nichts verloren geht.

Pakete:

- **flowaudit** = `@auditcore/bpmn-flowaudit` (`packages-js/bpmn-flowaudit`),
  framework-freie Fachschicht
- **vue** = `@auditcore/bpmn-vue` (`packages-js/bpmn-vue`), Oberfläche
- **Kern** = `@auditcore/bpmn-editor` (`packages-js/bpmn-editor`), Zeicheneditor
- **App** = die einbindende Anwendung (liefert die Ports)

Status: **übernommen** (Verhalten gleich, Tests portiert), **erweitert**
(übernommen und fachlich ausgebaut), **ersetzt** (gleiche Aufgabe, neuer
Weg, weil der alte Weg auf bpmn-js-Interna beruhte), **App** (bleibt
Aufgabe der Anwendung, Bibliothek bietet den Port), **offen**.

Clean-Room: Übernommen wurde nur FlowAudit-eigener Code des Nutzers.
Alles, was im audit_designer auf `bpmn-js`, `bpmn-js-properties-panel`,
`@bpmn-io/properties-panel` oder `bpmn-font` aufsetzte, ist neu geschrieben
(eigene Panels in Vue, eigene SVG-Symbole, Dienste des eigenen Kerns).

Pfade: flowaudit = `packages-js/bpmn-flowaudit/src/…`, vue = `packages-js/bpmn-vue/src/…`.

## 1. Fachmodule (`frontend/src/modules/flowstat/bpmn/*.ts`)

| audit_designer | Funktion | Neuer Ort | Status |
|---|---|---|---|
| `flowauditModdle.ts` | moddle-Deskriptor `flowaudit` 1.0 (`Rechtsgrundlage`, `InterneNotiz`, tagAlias lowerCase), `METADATEN_TYPEN` | flowaudit `schema/descriptor.ts` + `schema/spec.ts` (Schema 1.0 + 1.1, eine Tabelle für alle Typen), `METADATA_TYPES` | erweitert |
| `extensionElements.ts` | `leseMetadatum`, `schreibeMetadatum` (ein Undo-Schritt, leerer Text entfernt Eintrag, leeres `extensionElements` fällt weg) | flowaudit `model/legacyMetadata.ts` (`readMetadata`, `writeMetadata`) + `model/extensions.ts` (alle 1.1-Typen, Listen) | erweitert |
| `flowauditPropertiesProvider.ts` | Gruppe „Fachliche Angaben“ (Rechtsgrundlage, interne Notiz) im bpmn-js-Properties-Panel | vue `panels/PropertiesPanel.vue` mit Reitern „Rechtsgrundlagen“ (`panels/legal/*`) und „Notizen“ (`panels/tabs/NotesTab.vue`); eigene Vue-Felder, kein preact, kein properties-panel | ersetzt |
| `farbpalette.ts` | Palette validiert/kritisch/systemisch/inaktiv, `normalisiereFarbe`, `findeFarbe` | flowaudit `export/colorPalette.ts` (`PALETTE_COLORS`, `normalizeColor`, `findPaletteColor`) + Farben aus Kennzeichen (`colorsFromMarkers`, `MARKER_COLORS`) | erweitert |
| `farbContextPad.ts` | Kontextpad-Eintrag „Farbe festlegen“, Ereignis `flowaudit.farbe.oeffnen`, `setzeFarbe` | flowaudit `diagram/colorContextPad.ts` (`COLOR_PICKER_EVENT`, `setColor`; Ereignisname unverändert) + vue `components/base/ColorSwatches.vue` im `CanvasPopover` | übernommen |
| `seitenformate.ts` | DIN A4/A3, hoch/quer, `seitenMasse`, `berechneRaster` | flowaudit `layout/pageFormats.ts` (`PAGE_FORMATS`, `computePageGrid`) + vue `components/canvas/PageGrid.vue` | übernommen |
| `flussrichtung.ts` | `wendeRichtungAn`, `haltRichtung` | flowaudit `layout/flowDirection.ts` (`applyDirection`, `keepDirection`) | übernommen |
| `svgAufbereitung.ts` | Titel, Farblegende, Rechtsgrundlagen-Verzeichnis mit Marken, Fußzeile | flowaudit `export/svgPostProcessing.ts` (`prepareSvg`) + `export/svgBlocks.ts`; zusätzlich Kopfzeile, Kennzeichen-Legende, strukturierte Rechtsgrundlagen | erweitert |
| `bildExport.ts` | `ladeHerunter`, `dateiname`, `svgNachPng` | flowaudit `export/imageExport.ts` (`download`, `fileName`, `svgToPng`, `svgToJpeg`) + `export/pdf.ts` (PDF im Browser, ohne Server) | erweitert |
| `mystExport.ts` | `base64Utf8`, `diagrammKennung`, `baueMystSchnipsel`, `inZwischenablage` | flowaudit `export/myst.ts` (`buildMystSnippet`, `copyToClipboard`) + Prozesstabelle als MyST (`reports/tables.ts`) | erweitert |
| `exportTypen.ts` | Formate svg/png/bpmn/excel/pdf/myst, Optionen | flowaudit `export/exportTypes.ts` (zusätzlich CSV-Prozesstabelle, RCM, Feststellungsliste, neutral, Seitenformat, Kopfzeile) | erweitert |
| `diagrammBaum.ts` | Gruppierung nach Prozesstyp/Verantwortlichkeit, Filter, Suche | flowaudit `collection/legacyTree.ts` (`buildGroups`) + `collection/collection.ts` (Ordnerbaum, Tags, Reihenfolge) | erweitert |
| `deutschTranslate.ts` | Übersetzungstabelle mit Platzhaltern, Modul `translate` | Kern `translations` + flowaudit `i18n/translate.ts`, `messagesDe.ts`/`messagesEn.ts`; Tabelle des audit_designer als `i18n/legacyTranslations.ts` erhalten | erweitert |
| `__tests__/bpmnErweiterungen.spec.ts` | 20 Tests der Bausteine | flowaudit `test/legacyParity.spec.ts` (alle Fälle portiert) | übernommen |

## 2. Komponenten (`frontend/src/modules/flowstat/components/bpmn/*`)

| audit_designer | Funktion | Neuer Ort | Status |
|---|---|---|---|
| `BpmnCanvas.vue` | bpmn-js-Modeler, Import/Export, XML-Modus (CodeMirror) | vue `components/FlowauditEditor.vue` (Kern `BpmnEditor` über `editor/createEditor.ts`), XML-Ansicht `components/dialogs/XmlDialog.vue` | ersetzt |
| `BpmnCanvas.vue` | Seitenansicht (Raster der Seitenumbrüche) | vue `components/canvas/PageGrid.vue`, Auswahl in `components/toolbar/EditorToolbar.vue` | übernommen |
| `BpmnCanvas.vue` | Flussrichtung waagerecht/senkrecht | vue Werkzeugleiste → flowaudit `layout/flowDirection.ts` | übernommen |
| `BpmnCanvas.vue` | Zoom +/−/Einpassen | vue Werkzeugleiste, Tastenkürzel des Kerns, Zoomanzeige in `components/canvas/StatusBar.vue` | übernommen |
| `BpmnCanvas.vue` | Bildlaufleisten | Hand-Werkzeug, Verschieben per Tastatur (Kern), Übersichtskarte (Kern `minimap`); eigene Bildlaufleisten nicht übernommen | ersetzt |
| `BpmnCanvas.vue` | Farbwahl am Element (Popover) | vue `components/canvas/CanvasPopover.vue` + `ColorSwatches.vue`, ausgelöst über `flowaudit.farbe.oeffnen` | übernommen |
| `BpmnCanvas.vue` | gespiegelte Palette in linker Spalte | vue `components/palette/ToolPalette.vue` (eigene Symbole, Kern-Einträge über `paletteEntries.ts`) + „Pool mit Rolle“ aus flowaudit `diagram/rolePalette.ts` | ersetzt |
| `BpmnCanvas.vue` | `selectElement` (Sprung zum Element) | `FlowauditEditor` → `select(id)` (auch Web Component und React-Ref) | übernommen |
| `BpmnCanvas.vue` | `leseExportDaten` | flowaudit `export/exportData.ts` (`collectExportData`) | übernommen |
| `BpmnCanvas.vue` | `faerbeAuswahl` | flowaudit `setColor` + vue Werkzeugleiste (Farbe der Auswahl) | übernommen |
| `BpmnCanvas.vue` | Dark Mode der Zeichenfläche | vue `styles/theme.css` (CSS-Variablen), `theme="auto|light|dark"` | erweitert |
| `BpmnToolbar.vue` | Name, „ungespeichert“, Status, Speichern/Neu/Import/Export, Farbe, Prüfen-Menü (Validierung, Prozessanalyse, ESI, Teilen), Spalten ein/aus | vue `components/toolbar/EditorToolbar.vue` + `toolbarActions.ts` (deklarativ; „Teilen“, „Prozessanalyse“, Excel als Ereignisse an die App) | übernommen |
| `BpmnExportDialog.vue` | Titel, Legende, Metadaten, Rechtsgrundlagen, Formate | vue `components/dialogs/ExportDialog.vue` + `composables/useExport.ts` (+ CSV/MyST-Prozesstabelle, RCM, Feststellungsliste, neutral, Seitenformat, Kopfzeile) | erweitert |
| `BpmnPropertiesPanel.vue` | Beschreibung, Prozessverantwortlicher, Prozesstyp; FlowStat-Aufgabenfelder; Validierung | vue `components/dialogs/DiagramInfoDialog.vue` + `infoFields.ts` (Diagrammfelder), `panels/tabs/GeneralTab.vue` (FlowStat-Felder, Altattribute kanonisch schreiben), `components/views/IssueList.vue` | erweitert |
| `BpmnDiagramTree.vue` | Suche, Filter, Gruppierung, Löschen mit Bestätigung, Status/Version/Datum | vue `components/collection/CollectionTree.vue`, `TreeFolder.vue` (Ordnerbaum mit Drag-and-drop, Tags, Status-/Tag-Filter), `DiagramInfoColumn.vue`, `GroupOverview.vue` | erweitert |
| `EsiRequirementsDialog.vue` | Anforderungen je Element, Zusammenfassung, Sprung zum Element | vue `components/dialogs/EsiDialog.vue` + flowaudit `esi/esiRequirements.ts` | übernommen |

## 3. Composables und Ansicht

| audit_designer | Funktion | Neuer Ort | Status |
|---|---|---|---|
| `useBpmnApi.ts` | REST-Aufrufe, `extractErrorMessage`, `downloadBlob` | flowaudit `ports.ts` (`StoragePort` u. a.) + vue `rest/restPorts.ts` (REST-Vertrag `docs/bpmn/rest-api.md`, Fehlertexte aus `detail`/`message`) | ersetzt |
| `useBpmnEditor.ts` | leeres Diagramm, Lade-/dirty-Zustand, Validierung verfällt bei Änderung | flowaudit `model/load.ts` (`EMPTY_DIAGRAM`) + vue `stores/editorStore.ts`, `stores/validationStore.ts` (Prüfung nach Änderung neu) | übernommen |
| `useBpmnEditor.ts` | `parseTasks`, `updateTaskProperties` (Altattribute lesen, kanonisch schreiben) | flowaudit `model/flowstatAttributes.ts` | übernommen |
| `useEsiRequirements.ts` | Normalisierung, `deriveStatus` | flowaudit `esi/esiRequirements.ts` | übernommen |
| `views/BpmnEditor.vue` | Dreispalten-Layout, Diagramme/Eigenschaften, Rückfrage bei ungespeicherten Änderungen, Import aus Datei | vue `components/FlowauditWorkbench.vue` (Sammlung + Editor), eigenständige App `src/standalone/`, Web Component `src/web-component/` | übernommen |
| `useBpmnEditor.spec.ts` | Altattribute lesen/kanonisch schreiben | flowaudit `test/legacyParity.spec.ts` | übernommen |

## 4. Backend (`backend/app/modules/flowstat/…`)

| audit_designer | Funktion | Neuer Ort | Status |
|---|---|---|---|
| `models/bpmn_diagram.py` | `header_title`, `header_subtitle`, `header_color`, `header_text_color` | `flowaudit:diagrammInfo` (`titel`, `untertitel`, `kopfzeilenfarbe`, `kopfzeilenTextfarbe`); Ereignis `info-change` bzw. `diagram-info-change` an die App | erweitert |
| `models/bpmn_diagram.py` | `color_scheme` (JSON) | Palette in der Bibliothek; eigene Palette über Prop `palette` | erweitert |
| `models/bpmn_diagram.py` | `comments` (elementId, text, author, resolved) | vue Reiter „Notizen“; Kommentare über `StoragePort.loadComments/saveComments`, interne Notiz im XML | erweitert |
| `models/bpmn_diagram.py` | `process_owner`, `process_type`, `version`, `is_archived` | `diagrammInfo` (`prozessverantwortlich`, `prozesstyp`, `version`, `status="archiviert"`) | erweitert |
| `schemas/bpmn.py` | Validierungsergebnis `valid/errors/warnings` | flowaudit `validation/` (`ValidationIssue` mit Regel-ID, Schwere, Element; Katalog wie `auditcore_bpmn`) + vue `IssueList.vue` | erweitert |
| `api/bpmn.py` | CRUD, Validierung, Archiv, Kopfzeile, Farbschema, Kommentare, ESI | REST-Vertrag `docs/bpmn/rest-api.md` (Serverseite = App bzw. `auditcore_bpmn`) | App |
| `api/bpmn_export.py` | Analyse, Excel, PDF (501) | Analyse/Excel: App (Ereignisse `analysis`/`export-excel`); PDF im Browser (flowaudit `export/pdf.ts`) | erweitert |
| `services/bpmn_analyzer.py`, `services/bpmn_export.py` | Kennzahlen, Excel-Export | `auditcore_bpmn` (Python) | App |

## 5. Offene Punkte und Abweichungen

- XML-Ansicht ohne Syntaxhervorhebung (CodeMirror entfällt, keine schwere
  Abhängigkeit in der Bibliothek).
- Eigene Bildlaufleisten entfallen; Navigation über Hand-Werkzeug, Tastatur
  und Übersichtskarte des Kerns.
- Teilen-Dialog (`ShareResourceDialog`) gehört zur App; die Werkzeugleiste
  sendet nur das Ereignis `share`.
- Ergebnis des lokalen Paritätslaufs (Rundreise, Anreicherung, Prüfung,
  Neutralisierung über die Nutzerdiagramme via `BPMN_LOCAL_FIXTURES`): alle
  Diagramme fehlerfrei; die Diagramme selbst liegen nicht im Repository.
