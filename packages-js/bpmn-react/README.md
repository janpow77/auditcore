# @flowaudit/bpmn-react

## Zweck

Dünner, typisierter React-Wrapper um die Web Component `<flowaudit-bpmn-editor>` aus `@flowaudit/bpmn-vue` – für React 18.3 und 19.

Keine eigene Oberfläche: Zeichenketten werden Attribute, Objekte (XML, Ports,
Profil) Eigenschaften, Ereignisse werden an `onReady`, `onChange`, `onSave`,
`onSelectionChange`, `onDiagramInfoChange` und `onError` gebunden.

## Installation

Im Repository gehört das Paket zum npm-Workspace (`npm ci` im
Repository-Stamm, Bau mit `npm run build -w @flowaudit/bpmn-react`). In einer Anwendung:

```bash
npm install @flowaudit/bpmn-react
```

Das Paket ist noch in keiner npm-Registry veröffentlicht; bis dahin Bezug über
den Workspace oder ein mit `npm pack -w @flowaudit/bpmn-react` erzeugtes Tarball.

Peer-Abhängigkeiten: `react` und `react-dom` (18.3 oder 19).

## Schnellstart

```tsx
import { useRef } from 'react'
import { FlowauditBpmnEditor, type FlowauditBpmnEditorHandle } from '@flowaudit/bpmn-react'

export function Prozess({ xml }: { xml: string }) {
  const editor = useRef<FlowauditBpmnEditorHandle>(null)
  return (
    <FlowauditBpmnEditor
      ref={editor}
      xml={xml}
      locale="de"
      onSave={({ xml: saved }) => console.log(saved.length)}
      onError={({ message }) => console.error(message)}
      style={{ height: '80vh' }}
    />
  )
}
```

## Einbindung

**React:** Der Import von `@flowaudit/bpmn-react` registriert das Element;
wer das Bündel der Web Component selbst lädt, importiert nur
`@flowaudit/bpmn-react/component`. Unter React 18.3 und 19 verhält sich der
Wrapper gleich, weil Objekte per `ref` als Eigenschaften gesetzt und Ereignisse
per `addEventListener` gebunden werden.

Props: `src`, `apiBase`, `diagramId`, `name`, `locale`, `theme`, `readonly`,
`profile`, `author` (Attribute); `xml`, `storage`, `ports`, `profileData`,
`comments` (Eigenschaften); `onReady`, `onChange`, `onSave`,
`onSelectionChange`, `onDiagramInfoChange`, `onError`; `className`, `style`.
Die Referenz bietet `element`, `getXml()`, `getSvg()`, `select(id)`.

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Exporte der Einstiegspunkte aus `package.json#exports` (11):

| Einstieg | Name | Art | Kurzbeschreibung (erste JSDoc-Zeile) | Modul |
|---|---|---|---|---|
| `@flowaudit/bpmn-react` | `ATTRIBUTE_PROPS` | Konstante | – | `contract` |
| `@flowaudit/bpmn-react` | `ELEMENT_NAME` | Konstante | Mapping of React props to the attributes and events of `<flowaudit-bpmn-editor>` (see `@flowaudit/bpmn-vue/web-component`). | `contract` |
| `@flowaudit/bpmn-react` | `EVENT_PROPS` | Konstante | – | `contract` |
| `@flowaudit/bpmn-react` | `EditorPorts` | Schnittstelle | Application ports of the editor (same as `EditorPorts` of | `FlowauditBpmnEditor` |
| `@flowaudit/bpmn-react` | `FlowauditBpmnEditor` | Konstante | – | `FlowauditBpmnEditor` |
| `@flowaudit/bpmn-react` | `FlowauditBpmnEditorHandle` | Schnittstelle | Methods of the element, available through the ref. | `FlowauditBpmnEditor` |
| `@flowaudit/bpmn-react` | `FlowauditBpmnEditorProps` | Schnittstelle | – | `FlowauditBpmnEditor` |
| `@flowaudit/bpmn-react/component` | `EditorPorts` | Schnittstelle | Application ports of the editor (same as `EditorPorts` of | `FlowauditBpmnEditor` |
| `@flowaudit/bpmn-react/component` | `FlowauditBpmnEditor` | Konstante | – | `FlowauditBpmnEditor` |
| `@flowaudit/bpmn-react/component` | `FlowauditBpmnEditorHandle` | Schnittstelle | Methods of the element, available through the ref. | `FlowauditBpmnEditor` |
| `@flowaudit/bpmn-react/component` | `FlowauditBpmnEditorProps` | Schnittstelle | – | `FlowauditBpmnEditor` |
<!-- api-overview:end -->

## Konfiguration

Die Abbildung der Props auf Attribute und Ereignisse steht in
`ATTRIBUTE_PROPS` und `EVENT_PROPS` (`src/contract.ts`); alles Weitere
(Profile, Ports, Sprache, Farbschema) konfiguriert die Web Component, siehe
`@flowaudit/bpmn-vue`.

## Herkunft und Charakterisierung

Neuimplementierung. Die Tests laufen mit React 18.3; mit
`REACT_DIR=<Ordner mit React 19>` laufen dieselben Tests gegen React 19.
Dokumentation: Abschnitt „Nutzung in React-Projekten“ in
`docs/bpmn/frontend.md`.

## Abhängigkeiten

`@flowaudit/bpmn-flowaudit@0.1.0`, `@flowaudit/bpmn-vue@0.1.0`; Peers
`react` und `react-dom` (`^18.3.0 || ^19.0.0`).

## Sicherheit und Datenschutz

Der Wrapper selbst hat keinen Netzwerkzugriff und speichert nichts; Speicher
und REST-Zugriffe (`apiBase`, `storage`, `ports`) bestimmt die Anwendung über
die Web Component.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Clean-Room-Erklärung: Dieses Paket enthält keinen Code,
keine Styles und keine Icons aus bpmn-js, bpmn-js-properties-panel,
@bpmn-io/properties-panel oder bpmn-font. Genutzt werden nur diagram-js und
bpmn-moddle (MIT) über den eigenen Kern `@flowaudit/bpmn-editor`. Portiert
wurde ausschließlich FlowAudit-eigener Code aus dem audit_designer
(Paritätsinventar: `docs/bpmn/paritaet-audit-designer.md`). Die Icons sind
eigene SVG-Pfade (24 px, `currentColor`).

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
