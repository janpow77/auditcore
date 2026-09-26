# @flowaudit/bpmn-react

## Zweck

Native React-Oberfläche des FlowAudit-BPMN-Editors für React 18.3 und 19 – ohne Vue-Laufzeit und ohne Web Components, auf demselben framework-freien Kern wie `@flowaudit/bpmn-vue`.

Werkzeugleiste, Palette, Eigenschaften-Panel mit Tabs, Diagramm-Infos,
Rechtsgrundlagen, Sammlung als Ordnerbaum, Hinweisliste, Durchlauftest,
Soll/Ist- und Versionsvergleich, Export, Anreicherung, Suche und Tastenkürzel
sind React-Komponenten. Die Logik (Controller, Deskriptoren, Texte,
REST-Ports, Export) liegt einmal in `@flowaudit/bpmn-flowaudit/ui`; Vue- und
React-Fassung rendern dasselbe Markup und schreiben dasselbe XML.

## Installation

Anwendungen beziehen das Paket als Tarball aus dem GitHub-Release von
auditcore (noch nicht auf npm veröffentlicht), zusammen mit allen
`@flowaudit`-Paketen seiner Abhängigkeitshülle. Anleitung für Vue, React und
Web Components mit Integritätsprüfung und `vendor/`-Ablage:
[frontend-installation.md](../../docs/deployment/frontend-installation.md).

```sh
npm install @flowaudit/bpmn-react@https://github.com/janpow77/auditcore/releases/download/v<release>/flowaudit-bpmn-react-0.2.0.tgz
```

Abhängigkeitshülle: dazu `@flowaudit/bpmn-editor`, `@flowaudit/bpmn-flowaudit`, `@flowaudit/ui-core` und `@flowaudit/common`; Peer-Abhängigkeiten `react` und `react-dom` (18.3 oder 19), kein Vue. Stile: `@flowaudit/bpmn-react/style.css`.

Im auditcore-Repository gehört das Paket zum npm-Workspace (`npm ci` im
Stamm, Bau mit `npm run build -w @flowaudit/bpmn-react`).

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

```tsx
import { useState } from 'react'
import { FlowauditEditor, restPorts } from '@flowaudit/bpmn-react'

const ports = restPorts({ baseUrl: '/api/bpmn' })

export function Editor({ initial }: { initial: string }) {
  const [xml, setXml] = useState(initial)
  return <FlowauditEditor xml={xml} name="Antragsverfahren" ports={ports} onXmlChange={setXml} onSave={({ info }) => console.log(info?.title)} />
}
```

## Einbindung

**React, eingebettet (Vertrag der Web Component):** `FlowauditBpmnEditor` hat
dieselben Props wie die Attribute und Eigenschaften von
`<flowaudit-bpmn-editor>` (`src`, `apiBase`, `diagramId`, `name`, `locale`,
`theme`, `readonly`, `profile`, `author`, `xml`, `storage`, `ports`,
`profileData`, `comments`) und meldet dieselben Ereignisse mit denselben
Nutzdaten (`onReady`, `onChange`, `onSave`, `onSelectionChange`,
`onDiagramInfoChange`, `onError`). Die Referenz bietet `element`, `getXml()`,
`getSvg()`, `select(id)`, `reload()`.

**React, Editor und Werkbank:** `FlowauditEditor` entspricht der Vue-Komponente
gleichen Namens (`v-model:xml` → `xml` + `onXmlChange`, `update:name` →
`onNameChange`, `update:comments` → `onCommentsChange`, übrige Ereignisse als
`onXyz`). `FlowauditWorkbench` verbindet Sammlung und Editor über einen
`StoragePort`. Einzelteile (`PropertiesPanel`, `LegalBasisEditor`,
`IssueList`, `CollectionTree`, `GroupOverview`, `DiagramInfoColumn`) sind
exportiert; sie brauchen den Editorkontext (`EditorContextProvider`) bzw.
eine Sammlung aus `useCollection`.

## API-Überblick

Wichtig: `FlowauditBpmnEditor`, `FlowauditEditor` (Ref: `getXml`, `getSvg`,
`select`, `highlightKey`), `FlowauditWorkbench`, `I18nProvider`/`useI18n`,
`useEditorSession`, `restPorts`. Die vollständige Liste steht unten
(generiert).

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Exporte der Einstiegspunkte aus `package.json#exports` (57):

| Einstieg | Name | Art | Kurzbeschreibung (erste JSDoc-Zeile) | Modul |
|---|---|---|---|---|
| `@flowaudit/bpmn-react` | `ATTRIBUTE_PROPS` | Konstante | Mapping of the React props of `FlowauditBpmnEditor` to the attributes and events of the web component `<flowaudit-bpmn-editor>` (the contract both implementations share; see `ELEME … | `element/contract` |
| `@flowaudit/bpmn-react` | `BaseDialog` | Funktion | – | `base/BaseDialog` |
| `@flowaudit/bpmn-react` | `CollectionBinding` | Typ | What the collection components (`CollectionTree`, `DiagramInfoColumn`) receive as `store`. | `useCollection` |
| `@flowaudit/bpmn-react` | `CollectionTree` | Funktion | – | `collection/CollectionTree` |
| `@flowaudit/bpmn-react` | `CompareSource` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-react` | `CreateEditorOptions` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-react` | `DiagramInfoColumn` | Funktion | – | `collection/DiagramInfoColumn` |
| `@flowaudit/bpmn-react` | `EVENT_PROPS` | Konstante | – | `element/contract` |
| `@flowaudit/bpmn-react` | `EditorContext` | Schnittstelle | – | `context` |
| `@flowaudit/bpmn-react` | `EditorContextProvider` | Funktion | Provides the context; `null` before the session exists (consumers render only afterwards). | `context` |
| `@flowaudit/bpmn-react` | `EditorFactory` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-react` | `EditorLike` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-react` | `EditorPorts` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-react` | `EditorRuntime` | Schnittstelle | – | `useEditorSession` |
| `@flowaudit/bpmn-react` | `FaIcon` | Funktion | – | `base/FaIcon` |
| `@flowaudit/bpmn-react` | `FieldDescriptor` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-react` | `FlowauditBpmnEditor` | Konstante | – | `element/FlowauditBpmnEditor` |
| `@flowaudit/bpmn-react` | `FlowauditBpmnEditorHandle` | Schnittstelle | Methods available through the ref (as on the web component). | `element/FlowauditBpmnEditor` |
| `@flowaudit/bpmn-react` | `FlowauditBpmnEditorProps` | Schnittstelle | – | `element/FlowauditBpmnEditor` |
| `@flowaudit/bpmn-react` | `FlowauditEditor` | Konstante | – | `FlowauditEditor` |
| `@flowaudit/bpmn-react` | `FlowauditEditorHandle` | Schnittstelle | Methods available through the ref (Vue: `defineExpose`). | `editorProps` |
| `@flowaudit/bpmn-react` | `FlowauditEditorProps` | Schnittstelle | – | `editorProps` |
| `@flowaudit/bpmn-react` | `FlowauditWorkbench` | Funktion | – | `FlowauditWorkbench` |
| `@flowaudit/bpmn-react` | `GroupOverview` | Funktion | – | `collection/GroupOverview` |
| `@flowaudit/bpmn-react` | `I18n` | Schnittstelle | – | `i18n` |
| `@flowaudit/bpmn-react` | `I18nProvider` | Funktion | – | `i18n` |
| `@flowaudit/bpmn-react` | `IssueList` | Funktion | – | `views/IssueList` |
| `@flowaudit/bpmn-react` | `LISTS` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-react` | `LegalBasisEditor` | Funktion | – | `panels/legal/LegalBasisEditor` |
| `@flowaudit/bpmn-react` | `ListDescriptor` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-react` | `Locale` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-react` | `MESSAGES_DE` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-react` | `MESSAGES_EN` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-react` | `PropertiesPanel` | Funktion | – | `panels/PropertiesPanel` |
| `@flowaudit/bpmn-react` | `RestCatalogue` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-react` | `RestEsi` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-react` | `RestLegalSearch` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-react` | `RestOptions` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-react` | `RestProfiles` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-react` | `RestStorage` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-react` | `RestValidation` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-react` | `TABS` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-react` | `TabDefinition` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-react` | `ToolbarAction` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-react` | `createI18n` | Funktion | – | `i18n` |
| `@flowaudit/bpmn-react` | `defaultEditorFactory` | Konstante | – | `editorFactory` |
| `@flowaudit/bpmn-react` | `restPorts` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-react` | `useCollection` | Funktion | Creates a controller for the storage port, loads it once and binds it. | `useCollection` |
| `@flowaudit/bpmn-react` | `useCollectionBinding` | Funktion | Binds an existing controller (e.g. created and filled outside React). | `useCollection` |
| `@flowaudit/bpmn-react` | `useEditorContext` | Funktion | – | `context` |
| `@flowaudit/bpmn-react` | `useEditorSession` | Funktion | – | `useEditorSession` |
| `@flowaudit/bpmn-react` | `useEditorState` | Funktion | – | `context` |
| `@flowaudit/bpmn-react` | `useElementId` | Funktion | Stable, CSS-safe id per instance for aria references. | `hooks` |
| `@flowaudit/bpmn-react` | `useI18n` | Funktion | Provided i18n, or German when used standalone. | `i18n` |
| `@flowaudit/bpmn-react` | `useSelectionState` | Funktion | – | `context` |
| `@flowaudit/bpmn-react` | `useStoreState` | Funktion | State of a core controller (`@flowaudit/bpmn-flowaudit/ui`) as React state. | `hooks` |
| `@flowaudit/bpmn-react` | `useValidationView` | Funktion | – | `context` |
<!-- api-overview:end -->

## Konfiguration

Profile, Ports, Sprache (`de`, `en`), Farbschema (`auto`, `light`, `dark`),
Palette und ausgeblendete Werkzeugleisten-Aktionen wie bei
`@flowaudit/bpmn-vue`. Texte und Deskriptoren kommen aus
`@flowaudit/bpmn-flowaudit/ui` (`MESSAGES_DE`, `MESSAGES_EN`, `LISTS`,
`TABS`); eigene Texte über `I18nProvider overrides`.

## Herkunft und Charakterisierung

Neuimplementierung in React; ersetzt den früheren Wrapper um die Web
Component (0.1.0). Parität mit der Vue-Fassung: gemeinsame Fälle in
`packages-js/bpmn-flowaudit/test/parity/cases-*.ts`, verglichen werden
normalisiertes DOM, Formularzustand und XML (Laden, Speichern, Export,
erneuter Import) – siehe `docs/ui/react-paritaet.md`. Die Tests laufen mit
React 19 (`npm test`) und mit React 18.3 (`npm run test:react18`).

## Abhängigkeiten

`@flowaudit/bpmn-editor@0.1.0`, `@flowaudit/bpmn-flowaudit@0.2.0`,
`@flowaudit/ui-core@0.1.0` (Fokusfalle der Dialoge); Peers `react` und
`react-dom` (`^18.3.0 || ^19.0.0`).

## Sicherheit und Datenschutz

Die Bibliothek speichert nichts selbst. Netzwerkzugriffe entstehen nur über
die Ports der Anwendung (`storage`, `ports`, `apiBase` mit dem REST-Vertrag
`docs/bpmn/rest-api.md`) oder `src`. Vertrauliche Diagramme lassen sich
neutralisiert exportieren (Exportdialog, Vorschlag bei `vs_nfd`).

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
