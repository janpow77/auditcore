# @flowaudit/bpmn-react

Dünner, typisierter React-Wrapper um die Web Component
`<flowaudit-bpmn-editor>` aus `@flowaudit/bpmn-vue`. Keine eigene
Oberfläche: Zeichenketten werden Attribute, Objekte (XML, Ports, Profil)
Eigenschaften, Ereignisse werden an `onReady`, `onChange`, `onSave`,
`onSelectionChange`, `onDiagramInfoChange` und `onError` gebunden.
React 18.3 und 19.

```tsx
import { FlowauditBpmnEditor } from '@flowaudit/bpmn-react'

<FlowauditBpmnEditor apiBase="/api/bpmn" diagramId="antragsverfahren" onSave={({ xml }) => console.log(xml)} />
```

Dokumentation: Abschnitt „Nutzung in React-Projekten“ in `docs/bpmn/frontend.md`.

## Lizenz und Herkunft

MIT (siehe `LICENSE`). Clean-Room-Erklärung: Dieses Paket enthält keinen Code,
keine Styles und keine Icons aus bpmn-js, bpmn-js-properties-panel,
@bpmn-io/properties-panel oder bpmn-font. Genutzt werden nur diagram-js und
bpmn-moddle (MIT) über den eigenen Kern `@flowaudit/bpmn-editor`. Portiert
wurde ausschließlich FlowAudit-eigener Code aus dem audit_designer
(Paritätsinventar: `docs/bpmn/paritaet-audit-designer.md`). Die Icons sind
eigene SVG-Pfade (24 px, `currentColor`).
