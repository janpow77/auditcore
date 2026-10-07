# Changelog – @auditcore/bpmn-react

## 0.4.0 – 2026-10-07

- **Reiter „Prüfungsmerkmale“** (`PropertiesTab`) wie in `@auditcore/bpmn-vue`
  0.4.0: Merkmale nach `profile.properties`, gespeichert als
  `camunda:property`.

## 0.3.1 – 2026-10-07

- **Ordner umbenennen** wie in `@auditcore/bpmn-vue` 0.3.1: Ordnerkarte mit
  `InlineName` (`onRenameFolder`), Baum per Doppelklick oder F2 mit Dialog,
  `FlowauditWorkbench` speichert über `renameFolder`.

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

Abhängigkeit `@auditcore/bpmn-flowaudit` 0.3.0 (Paritätstests gegen `@auditcore/bpmn-vue` 0.3.0).

## 0.2.2 – 2026-09-29

Exakte UI-Abhängigkeiten auf die neuen Versionen aktualisiert; keine Änderung des BPMN-Verhaltens.
Veröffentlicht mit Release v0.8.1.


## 0.2.1 – 2026-09-26 – Release v0.4.2

- **Breaking:** Paketname `@auditcore/bpmn-react` statt `@flowaudit/bpmn-react` (npm-Scope einheitlich mit den Python-Paketen `auditcore_*`). Imports, `package.json`-Einträge und Tarball-Namen (`auditcore-bpmn-react-<version>.tgz`) anpassen; siehe `docs/ui/umbenennung-auditcore.md`. Web-Component-Tags und CSS-Präfixe unverändert.

Keine Verhaltensänderung. Build mit Vite 8 und vite-plugin-dts 5 (#169); README: Installation als Tarball aus dem GitHub-Release (#157). Abhängigkeiten `@auditcore/bpmn-editor` 0.1.1, `@auditcore/bpmn-flowaudit` 0.2.1, `@auditcore/ui-core` 0.2.0; Pfad-Alias für `@auditcore/kanban-core` im Workspace (#154).

## 0.2.0 – 2026-09-26

- **Breaking:** native React-Oberfläche statt Wrapper um die Web Component –
  keine Vue-Laufzeit, kein Custom Element. `@flowaudit/bpmn-vue` ist keine
  Abhängigkeit mehr; der Unterpfad `./component` entfällt, Stile unter
  `@flowaudit/bpmn-react/style.css`.
- `FlowauditBpmnEditor` behält den Vertrag der Web Component (Props,
  Ereignisse mit denselben Nutzdaten, Ref `element`/`getXml`/`getSvg`/
  `select`, neu `reload`); gerendert wird ein `div.flowaudit-bpmn-editor`.
- Neu: `FlowauditEditor`, `FlowauditWorkbench`, `PropertiesPanel`,
  `LegalBasisEditor`, `IssueList`, `CollectionTree`, `GroupOverview`,
  `DiagramInfoColumn`, `EditorContextProvider`, `I18nProvider`,
  `useEditorSession`, `useCollection` auf dem Kern
  `@flowaudit/bpmn-flowaudit/ui`.
- Parität mit der Vue-Fassung über gemeinsame Fälle (DOM, Formularzustand,
  XML); Tests unter React 19 und React 18.3 (`npm run test:react18`).

## 0.1.0 – 2026-09-25

- Erste Fassung (#90): typisierter React-Wrapper `FlowauditBpmnEditor` um
  die Web Component `<flowaudit-bpmn-editor>` für React 18.3 und 19.
