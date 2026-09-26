# @auditcore/bpmn-react

## Zweck

Native React-Oberfläche des FlowAudit-BPMN-Editors für React 18.3 und 19 – ohne Vue-Laufzeit und ohne Web Components, auf demselben framework-freien Kern wie `@auditcore/bpmn-vue`.

Werkzeugleiste, Palette, Eigenschaften-Panel mit Tabs, Diagramm-Infos,
Rechtsgrundlagen, Sammlung als Ordnerbaum, Hinweisliste, Durchlauftest,
Soll/Ist- und Versionsvergleich, Export, Anreicherung, Suche und Tastenkürzel
sind React-Komponenten. Die Logik (Controller, Deskriptoren, Texte,
REST-Ports, Export) liegt einmal in `@auditcore/bpmn-flowaudit/ui`; Vue- und
React-Fassung rendern dasselbe Markup und schreiben dasselbe XML.

## Installation

Standardweg ist die npm-Registry; npm löst die übrigen `@auditcore`-Pakete
der Abhängigkeitshülle selbst auf:

```sh
npm install @auditcore/bpmn-react
```

Ohne Registry-Zugang (Intranet, offline) bleibt der signierte Tarball aus
dem GitHub-Release von auditcore; dann gehört jedes Paket der Hülle
ausdrücklich in die `package.json`:

```sh
npm install @auditcore/bpmn-react@https://github.com/janpow77/auditcore/releases/download/v<release>/auditcore-bpmn-react-0.2.0.tgz
```

Anleitung für Vue, React und Web Components mit Integritätsprüfung und
`vendor/`-Ablage:
[frontend-installation.md](../../docs/deployment/frontend-installation.md).

Abhängigkeitshülle: dazu `@auditcore/bpmn-editor`, `@auditcore/bpmn-flowaudit`, `@auditcore/ui-core` und `@auditcore/common`; Peer-Abhängigkeiten `react` und `react-dom` (18.3 oder 19), kein Vue. Stile: `@auditcore/bpmn-react/style.css`.

Im auditcore-Repository gehört das Paket zum npm-Workspace (`npm ci` im
Stamm, Bau mit `npm run build -w @auditcore/bpmn-react`).

## Schnellstart

```tsx
import { useRef } from 'react'
import { FlowauditBpmnEditor, type FlowauditBpmnEditorHandle } from '@auditcore/bpmn-react'

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
import { FlowauditEditor, restPorts } from '@auditcore/bpmn-react'

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
| `@auditcore/bpmn-react` | `ATTRIBUTE_PROPS` | Konstante | Mapping of the React props of `FlowauditBpmnEditor` to the attributes and events of the web component `<flowaudit-bpmn-editor>` (the contract both implementations share; see `ELEME … | `element/contract` |
| `@auditcore/bpmn-react` | `BaseDialog` | Funktion | – | `base/BaseDialog` |
| `@auditcore/bpmn-react` | `CollectionBinding` | Typ | What the collection components (`CollectionTree`, `DiagramInfoColumn`) receive as `store`. | `useCollection` |
| `@auditcore/bpmn-react` | `CollectionTree` | Funktion | – | `collection/CollectionTree` |
| `@auditcore/bpmn-react` | `CompareSource` | Re-Export | – | `@auditcore/bpmn-flowaudit/ui` |
| `@auditcore/bpmn-react` | `CreateEditorOptions` | Re-Export | – | `@auditcore/bpmn-flowaudit/ui` |
| `@auditcore/bpmn-react` | `DiagramInfoColumn` | Funktion | – | `collection/DiagramInfoColumn` |
| `@auditcore/bpmn-react` | `EVENT_PROPS` | Konstante | – | `element/contract` |
| `@auditcore/bpmn-react` | `EditorContext` | Schnittstelle | – | `context` |
| `@auditcore/bpmn-react` | `EditorContextProvider` | Funktion | Provides the context; `null` before the session exists (consumers render only afterwards). | `context` |
| `@auditcore/bpmn-react` | `EditorFactory` | Re-Export | – | `@auditcore/bpmn-flowaudit/ui` |
| `@auditcore/bpmn-react` | `EditorLike` | Re-Export | – | `@auditcore/bpmn-flowaudit/ui` |
| `@auditcore/bpmn-react` | `EditorPorts` | Re-Export | – | `@auditcore/bpmn-flowaudit/ui` |
| `@auditcore/bpmn-react` | `EditorRuntime` | Schnittstelle | – | `useEditorSession` |
| `@auditcore/bpmn-react` | `FaIcon` | Funktion | – | `base/FaIcon` |
| `@auditcore/bpmn-react` | `FieldDescriptor` | Re-Export | – | `@auditcore/bpmn-flowaudit/ui` |
| `@auditcore/bpmn-react` | `FlowauditBpmnEditor` | Konstante | – | `element/FlowauditBpmnEditor` |
| `@auditcore/bpmn-react` | `FlowauditBpmnEditorHandle` | Schnittstelle | Methods available through the ref (as on the web component). | `element/FlowauditBpmnEditor` |
| `@auditcore/bpmn-react` | `FlowauditBpmnEditorProps` | Schnittstelle | – | `element/FlowauditBpmnEditor` |
| `@auditcore/bpmn-react` | `FlowauditEditor` | Konstante | – | `FlowauditEditor` |
| `@auditcore/bpmn-react` | `FlowauditEditorHandle` | Schnittstelle | Methods available through the ref (Vue: `defineExpose`). | `editorProps` |
| `@auditcore/bpmn-react` | `FlowauditEditorProps` | Schnittstelle | – | `editorProps` |
| `@auditcore/bpmn-react` | `FlowauditWorkbench` | Funktion | – | `FlowauditWorkbench` |
| `@auditcore/bpmn-react` | `GroupOverview` | Funktion | – | `collection/GroupOverview` |
| `@auditcore/bpmn-react` | `I18n` | Schnittstelle | – | `i18n` |
| `@auditcore/bpmn-react` | `I18nProvider` | Funktion | – | `i18n` |
| `@auditcore/bpmn-react` | `IssueList` | Funktion | – | `views/IssueList` |
| `@auditcore/bpmn-react` | `LISTS` | Re-Export | – | `@auditcore/bpmn-flowaudit/ui` |
| `@auditcore/bpmn-react` | `LegalBasisEditor` | Funktion | – | `panels/legal/LegalBasisEditor` |
| `@auditcore/bpmn-react` | `ListDescriptor` | Re-Export | – | `@auditcore/bpmn-flowaudit/ui` |
| `@auditcore/bpmn-react` | `Locale` | Re-Export | – | `@auditcore/bpmn-flowaudit/ui` |
| `@auditcore/bpmn-react` | `MESSAGES_DE` | Re-Export | – | `@auditcore/bpmn-flowaudit/ui` |
| `@auditcore/bpmn-react` | `MESSAGES_EN` | Re-Export | – | `@auditcore/bpmn-flowaudit/ui` |
| `@auditcore/bpmn-react` | `PropertiesPanel` | Funktion | – | `panels/PropertiesPanel` |
| `@auditcore/bpmn-react` | `RestCatalogue` | Re-Export | – | `@auditcore/bpmn-flowaudit/ui` |
| `@auditcore/bpmn-react` | `RestEsi` | Re-Export | – | `@auditcore/bpmn-flowaudit/ui` |
| `@auditcore/bpmn-react` | `RestLegalSearch` | Re-Export | – | `@auditcore/bpmn-flowaudit/ui` |
| `@auditcore/bpmn-react` | `RestOptions` | Re-Export | – | `@auditcore/bpmn-flowaudit/ui` |
| `@auditcore/bpmn-react` | `RestProfiles` | Re-Export | – | `@auditcore/bpmn-flowaudit/ui` |
| `@auditcore/bpmn-react` | `RestStorage` | Re-Export | – | `@auditcore/bpmn-flowaudit/ui` |
| `@auditcore/bpmn-react` | `RestValidation` | Re-Export | – | `@auditcore/bpmn-flowaudit/ui` |
| `@auditcore/bpmn-react` | `TABS` | Re-Export | – | `@auditcore/bpmn-flowaudit/ui` |
| `@auditcore/bpmn-react` | `TabDefinition` | Re-Export | – | `@auditcore/bpmn-flowaudit/ui` |
| `@auditcore/bpmn-react` | `ToolbarAction` | Re-Export | – | `@auditcore/bpmn-flowaudit/ui` |
| `@auditcore/bpmn-react` | `createI18n` | Funktion | – | `i18n` |
| `@auditcore/bpmn-react` | `defaultEditorFactory` | Konstante | – | `editorFactory` |
| `@auditcore/bpmn-react` | `restPorts` | Re-Export | – | `@auditcore/bpmn-flowaudit/ui` |
| `@auditcore/bpmn-react` | `useCollection` | Funktion | Creates a controller for the storage port, loads it once and binds it. | `useCollection` |
| `@auditcore/bpmn-react` | `useCollectionBinding` | Funktion | Binds an existing controller (e.g. created and filled outside React). | `useCollection` |
| `@auditcore/bpmn-react` | `useEditorContext` | Funktion | – | `context` |
| `@auditcore/bpmn-react` | `useEditorSession` | Funktion | – | `useEditorSession` |
| `@auditcore/bpmn-react` | `useEditorState` | Funktion | – | `context` |
| `@auditcore/bpmn-react` | `useElementId` | Funktion | Stable, CSS-safe id per instance for aria references. | `hooks` |
| `@auditcore/bpmn-react` | `useI18n` | Funktion | Provided i18n, or German when used standalone. | `i18n` |
| `@auditcore/bpmn-react` | `useSelectionState` | Funktion | – | `context` |
| `@auditcore/bpmn-react` | `useStoreState` | Funktion | State of a core controller (`@auditcore/bpmn-flowaudit/ui`) as React state. | `hooks` |
| `@auditcore/bpmn-react` | `useValidationView` | Funktion | – | `context` |
<!-- api-overview:end -->

## Konfiguration

Profile, Ports, Sprache (`de`, `en`), Farbschema (`auto`, `light`, `dark`),
Palette und ausgeblendete Werkzeugleisten-Aktionen wie bei
`@auditcore/bpmn-vue`. Texte und Deskriptoren kommen aus
`@auditcore/bpmn-flowaudit/ui` (`MESSAGES_DE`, `MESSAGES_EN`, `LISTS`,
`TABS`); eigene Texte über `I18nProvider overrides`.

## Herkunft und Charakterisierung

Neuimplementierung in React; ersetzt den früheren Wrapper um die Web
Component (0.1.0). Parität mit der Vue-Fassung: gemeinsame Fälle in
`packages-js/bpmn-flowaudit/test/parity/cases-*.ts`, verglichen werden
normalisiertes DOM, Formularzustand und XML (Laden, Speichern, Export,
erneuter Import) – siehe `docs/ui/react-paritaet.md`. Die Tests laufen mit
React 19 (`npm test`) und mit React 18.3 (`npm run test:react18`).

## Abhängigkeiten

`@auditcore/bpmn-editor@0.1.0`, `@auditcore/bpmn-flowaudit@0.2.0`,
`@auditcore/ui-core@0.1.0` (Fokusfalle der Dialoge); Peers `react` und
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
bpmn-moddle (MIT) über den eigenen Kern `@auditcore/bpmn-editor`. Portiert
wurde ausschließlich FlowAudit-eigener Code aus dem audit_designer
(Paritätsinventar: `docs/bpmn/paritaet-audit-designer.md`). Die Icons sind
eigene SVG-Pfade (24 px, `currentColor`).

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
