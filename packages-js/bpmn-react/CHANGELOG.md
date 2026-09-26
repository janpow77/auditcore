# Changelog – @auditcore/bpmn-react

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
