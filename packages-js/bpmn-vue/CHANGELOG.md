# Changelog – @auditcore/bpmn-vue

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
