# Changelog – @flowaudit/bpmn-react

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
