# Changelog – @auditcore/bpmn-vue

## 0.5.0 – 2026-10-07

- **Ordnerübersicht in voller Breite mit drei Ansichten** (`GroupOverview`):
  Kacheln, Liste (Name, Status, Beschreibung, Aktivitäten, Anteil mit
  Rechtsgrundlage, Datum) und Vorschaubilder, umgeschaltet in einem Menü im
  Kopf und je Browser gemerkt. Karten mit vielen Diagrammen nehmen die ganze
  Zeile ein, lange Namen brechen um. Neue Prop `thumbnails`; ohne sie wird
  „Vorschaubilder“ nicht angeboten. Neue Komponente `OverviewThumbnail`
  (lädt erst beim Sichtbarwerden, zeigt ein Bild, nie Inline-SVG).
- **`PanelResizer`**: Trennlinie zwischen Seitenbereich und Hauptbereich –
  ziehen, Pfeiltasten und Pos1/Ende, Doppelklick setzt die Standardbreite,
  kleine Schaltfläche klappt ein; eingeklappt bleibt eine schmale Leiste zum
  Aufklappen. `FlowauditEditor` nutzt sie für die Eigenschaften (Breite und
  Zustand je Browser), `FlowauditWorkbench` für die Diagrammsammlung.
- `FlowauditWorkbench` erzeugt Vorschaubilder im Browser und verwirft sie
  beim Speichern; `createCollectionStore(storage, options)` reicht
  `onDiagramSaved` durch.
- Pools lassen sich in der Fläche (auf der Bahn) greifen und verschieben
  (`@auditcore/bpmn-editor` 0.1.2).

## 0.4.0 – 2026-10-07

- **Reiter „Prüfungsmerkmale“** (`PropertiesTab`): Merkmale nach
  `profile.properties` als Auswahl, Mehrfachauswahl, Ja/Nein oder Freitext,
  gespeichert als `camunda:property` (im Camunda Modeler lesbar). Erscheint
  nur, wenn das Profil Merkmale für den Elementtyp definiert; Bedingungen
  (`depends_on`) blenden Felder sichtbar ab statt sie zu verstecken; Werte, die
  das Profil nicht kennt, bleiben sichtbar und erhalten.
- Demo mit Beispielkatalog der Systemprüfungen (`demo/demoProperties.ts`) und
  einem Camunda-Modell; Playwright-Demo prüft Bearbeiten, Speichern und
  erneutes Öffnen.

## 0.3.1 – 2026-10-07

- **Ordner umbenennen:** auf der Ordnerkarte (`GroupOverview`) ist der Name
  direkt bearbeitbar (neu `InlineName`, Ereignis `rename-folder`); im Baum
  (`CollectionTree`) per Doppelklick oder F2 auf den Ordnernamen mit Dialog
  „Ordner umbenennen“. `FlowauditWorkbench` speichert über `renameFolder`.
  Leerraum wird getrimmt, ein leerer Name nicht übernommen.

## 0.3.0 – 2026-10-06

- **Übersicht der obersten Ebene** (`GroupOverview`): Ordnerkarten mit Name,
  Beschreibung, Anzahl und den enthaltenen Diagrammen (klickbar); Beschreibungen
  von Ordnern und Diagrammen sind inline bearbeitbar, ohne Text steht „Keine
  Beschreibung“. Rechtsgrundlagen-Abdeckung, abgelaufene Gültigkeiten und
  Sammlungshinweise liegen im eingeklappten Bereich „Prüfhinweise (n)“.
  Kernanforderungs-Kacheln und Status-Verteilung entfallen dort; `groupOverview`
  liefert die Werte unverändert. Neue Props `cards`, `topLevel`, `readonly`,
  `folderActions`; neue Ereignisse `describe-folder`/`describe-diagram`/
  `folder-action` (React: `onDescribeFolder`, `onDescribeDiagram`,
  `onFolderAction`). Ohne `cards` zeigt die Übersicht nur die Prüfhinweise –
  Hosts mit eigener Werkbank müssen `cards` übergeben.
- **Palette:** „Elemente“ und „Pool mit Rolle“ wahlweise als Symbole, große
  Kacheln (mit Rollenkürzel) oder Liste (Kürzel und Langbezeichnung aus dem
  Rollenkatalog). Umschaltung über ein Menü im Palettenkopf, die Wahl bleibt je
  Browser erhalten (`localStorage`, Schlüssel `auditcore.bpmn.paletteView`).
- **Rollenkacheln** im Reiter „Rolle“: lange Bezeichnungen brechen innerhalb der
  Kachel um (`overflow-wrap: anywhere`, Silbentrennung), keine Überlappung mehr.
- **Linienauswahl:** Die Bibliotheks-CSS (`style.css`) enthält jetzt die
  Grundstile von diagram-js aus `@auditcore/bpmn-editor`. Fehlten sie, zeichnete
  der Browser Segment-Anfasser und Knickpunkte als schwarze Balken und Punkte.
  Gewählte Sequenzflüsse behalten ihre Strichstärke und erhalten einen dezenten
  Schein in der Akzentfarbe; Knickpunkte sind kleine helle Kreise mit farbigem
  Rand.
- **Host-Aktionen:** `FlowauditEditor` nimmt `hostActions` entgegen
  (`{ id, label, group?: 'export' }`); Einträge erscheinen im Menü „Prüfen“
  bzw. mit `group: 'export'` im Exportdialog und melden `host-action` (React:
  `onHostAction`) mit der Kennung. `FlowauditWorkbench` reicht `hostActions`
  und `folderActions` durch.

Abhängigkeit `@auditcore/bpmn-flowaudit` 0.3.0.

## 0.2.2 – 2026-09-29

Exakten ui-core-Pin auf 0.3.0 aktualisiert; keine Änderung des BPMN-Verhaltens.
Veröffentlicht mit Release v0.8.1.


## 0.2.1 – 2026-09-26 – Release v0.4.2

- **Breaking:** Paketname `@auditcore/bpmn-vue` statt `@flowaudit/bpmn-vue` (npm-Scope einheitlich mit den Python-Paketen `auditcore_*`). Imports, `package.json`-Einträge und Tarball-Namen (`auditcore-bpmn-vue-<version>.tgz`) anpassen; siehe `docs/ui/umbenennung-auditcore.md`. Web-Component-Tags und CSS-Präfixe unverändert.

Keine Verhaltensänderung. Build mit Vite 8 und vite-plugin-dts 5 (#169); README: Installation als Tarball aus dem GitHub-Release (#157). Abhängigkeiten `@auditcore/bpmn-editor` 0.1.1, `@auditcore/bpmn-flowaudit` 0.2.1, `@auditcore/ui-core` 0.2.0; Pfad-Alias für `@auditcore/kanban-core` im Workspace (#154).

## 0.2.0 – 2026-09-26

- Die Logik liegt im framework-freien Kern `@flowaudit/bpmn-flowaudit/ui`
  (geteilt mit der nativen React-Fassung `@flowaudit/bpmn-react`). Stores und
  Composables binden die Kern-Controller an Vue; Props, Ereignisse, Markup und
  Web Component bleiben unverändert.
- Neu exportiert: `bindEditorCore`, `bindSelectionCore`, `bindValidationCore`,
  `useStore`.
- Stile kommen aus `@flowaudit/bpmn-flowaudit/ui.css` und sind weiter in
  `style.css`, der Web Component und der eigenständigen App enthalten.
- Dialoge nutzen die Fokusfalle aus `@flowaudit/ui-core`.
- `LegalSearch` setzt `aria-controls` nur noch, solange die Trefferliste
  sichtbar ist (vorher Verweis auf ein nicht vorhandenes Element).

## 0.1.0 – 2026-09-25

- Erste Fassung (#90): Vue-3-Oberfläche des FlowAudit-BPMN-Editors
  (`FlowauditEditor`, `FlowauditWorkbench`, Eigenschaften-Panel, Sammlung,
  Hinweisliste, Durchlauftest, Vergleiche, Exportdialog, Stores, REST-Ports),
  Web Component `<flowaudit-bpmn-editor>` und eigenständige App.
