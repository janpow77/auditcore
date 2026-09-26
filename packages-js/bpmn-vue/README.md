# @flowaudit/bpmn-vue

## Zweck

Vue-3-Oberfläche des FlowAudit-BPMN-Editors mit Eigenschaften-Panel, Sammlung, Prüfansichten und Export – als Vue-Bibliothek, Web Component `<flowaudit-bpmn-editor>` und eigenständige App.

Für Anwendungen, die Prozesse der Verwaltungs- und Kontrollsysteme im Browser
bearbeiten: Werkzeugleiste, Palette, deklaratives Eigenschaften-Panel,
Diagramm-Infos, Rechtsgrundlagen-Erfassung, Sammlung als Ordnerbaum mit
Drag-and-drop, Tags, Filter, Hinweisliste, Durchlauftest, Soll/Ist- und
Versionsvergleich, Exportdialog, Anreicherung, Suche, Tastenkürzel. Alles ist
lokal gebündelt, keine CDN-Abhängigkeit.

## Installation

Anwendungen beziehen das Paket als Tarball aus dem GitHub-Release von
auditcore (noch nicht auf npm veröffentlicht), zusammen mit allen
`@flowaudit`-Paketen seiner Abhängigkeitshülle. Anleitung für Vue, React und
Web Components mit Integritätsprüfung und `vendor/`-Ablage:
[frontend-installation.md](../../docs/deployment/frontend-installation.md).

```sh
npm install @flowaudit/bpmn-vue@https://github.com/janpow77/auditcore/releases/download/v<release>/flowaudit-bpmn-vue-0.2.1.tgz
```

Abhängigkeitshülle: dazu `@flowaudit/bpmn-editor`, `@flowaudit/bpmn-flowaudit`, `@flowaudit/ui-core` und `@flowaudit/common`; Peer-Abhängigkeit `vue` ^3.5. Stile: `@flowaudit/bpmn-vue/style.css`. Drei Ausgaben: Vue-Bibliothek (`dist/`), Web Component (`dist-wc/`, Import `@flowaudit/bpmn-vue/web-component`, ein einzelnes Modul) und eigenständige App (`dist-standalone/`).

Im auditcore-Repository gehört das Paket zum npm-Workspace (`npm ci` im
Stamm, Bau mit `npm run build -w @flowaudit/bpmn-vue`).

## Schnellstart

```ts
import { restPorts } from '@flowaudit/bpmn-vue'
import '@flowaudit/bpmn-vue/style.css'

// Speicher, Rechtsgrundlagen, KA/BK, Profile, Prüfung und ESI über den REST-Vertrag
const ports = restPorts({ baseUrl: '/api/bpmn' })
const storage = ports.storage
```

```vue
<!-- nur Editor -->
<FlowauditEditor v-model:xml="xml" :name="name" :profile="profile" :ports="ports"
  @save="onSave" @selection-change="onSelect" />

<!-- Sammlung (Ordnerbaum, Tags, Filter, Info-Spalte, Gruppenübersicht) + Editor -->
<FlowauditWorkbench :storage="storage" :profile="profile" :ports="ports" author="Prüferin" />
```

## Einbindung

**Vue:** `FlowauditEditor` und `FlowauditWorkbench` aus `@flowaudit/bpmn-vue`
(siehe Schnellstart); Profile aus `@flowaudit/bpmn-flowaudit/profiles`,
Speicher im Browser mit `InMemoryStorage` aus `@flowaudit/bpmn-flowaudit`.

**Web Component:** `@flowaudit/bpmn-vue/web-component` ist ein einzelnes
ES-Modul mit Vue, Kern, Fachschicht, gebündelten Profilen und CSS. Das Element
rendert im Light DOM; der Import registriert es einmal.

```html
<script type="module" src="/static/flowaudit-bpmn-editor.js"></script>
<flowaudit-bpmn-editor api-base="/api/bpmn" diagram-id="antragsverfahren" locale="de"></flowaudit-bpmn-editor>
```

Attribute: `src`, `api-base`, `diagram-id`, `name`, `author`, `locale`,
`theme`, `readonly`, `profile`. Objekt-Eigenschaften: `xml`, `storage`,
`ports`, `profileData`, `comments`. Ereignisse (`CustomEvent`, Nutzdaten in
`detail`): `ready`, `change`, `save`, `selection-change`,
`diagram-info-change`, `error`. Methoden: `getXml()`, `getSvg()`,
`select(id)`, `reload()`.

**React:** `@flowaudit/bpmn-react` ist eine native React-Fassung derselben
Oberfläche (kein Wrapper um die Web Component). Beide rendern aus dem
framework-freien Kern `@flowaudit/bpmn-flowaudit/ui`; Stores und Composables
dieses Pakets binden dessen Controller an Vue.

**Eigenständige App:** `dist-standalone/` spricht den REST-Vertrag
`docs/bpmn/rest-api.md`; die API-Basis kommt aus `window.FLOWAUDIT_CONFIG`,
`<meta name="flowaudit-api-base">` oder `?api=…`.

## API-Überblick

Wichtige Eigenschaften von `FlowauditEditor`: `xml`, `name`, `diagramId`,
`profile`, `profiles`, `ports`, `locale`, `theme`, `readonly`, `lockApproved`
(freigegebene Stände schreibgeschützt, Standard an), `comments`, `approvals`,
`author`, `compareSources`, `palette`, `roleAliases`, `replacements`,
`hiddenActions`, `editorFactory`. Über die Komponenten-Referenz: `getXml()`,
`getSvg()`, `select(id)`, `highlightKey(kind, value)`. Die vollständigen Props
und Ereignisse stehen unten (generiert).

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Exporte der Einstiegspunkte aus `package.json#exports` (52):

| Einstieg | Name | Art | Kurzbeschreibung (erste JSDoc-Zeile) | Modul |
|---|---|---|---|---|
| `@flowaudit/bpmn-vue` | `BaseDialog` | Vue-Komponente | – | `components/base/BaseDialog.vue` |
| `@flowaudit/bpmn-vue` | `CollectionStore` | Typ | – | `stores/collectionStore` |
| `@flowaudit/bpmn-vue` | `CollectionTree` | Vue-Komponente | – | `components/collection/CollectionTree.vue` |
| `@flowaudit/bpmn-vue` | `CompareSource` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-vue` | `CreateEditorOptions` | Re-Export | – | `./editor/defaultFactory` |
| `@flowaudit/bpmn-vue` | `DiagramInfoColumn` | Vue-Komponente | – | `components/collection/DiagramInfoColumn.vue` |
| `@flowaudit/bpmn-vue` | `EditorContext` | Schnittstelle | – | `stores/context` |
| `@flowaudit/bpmn-vue` | `EditorFactory` | Re-Export | – | `./editor/defaultFactory` |
| `@flowaudit/bpmn-vue` | `EditorLike` | Re-Export | – | `./editor/defaultFactory` |
| `@flowaudit/bpmn-vue` | `EditorPorts` | Re-Export | – | `./stores/context` |
| `@flowaudit/bpmn-vue` | `EditorStore` | Typ | – | `stores/editorStore` |
| `@flowaudit/bpmn-vue` | `FaIcon` | Vue-Komponente | – | `components/base/FaIcon.vue` |
| `@flowaudit/bpmn-vue` | `FieldDescriptor` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-vue` | `FlowauditEditor` | Vue-Komponente | – | `components/FlowauditEditor.vue` |
| `@flowaudit/bpmn-vue` | `FlowauditWorkbench` | Vue-Komponente | – | `components/FlowauditWorkbench.vue` |
| `@flowaudit/bpmn-vue` | `GroupOverview` | Vue-Komponente | – | `components/collection/GroupOverview.vue` |
| `@flowaudit/bpmn-vue` | `I18n` | Schnittstelle | – | `i18n/useI18n` |
| `@flowaudit/bpmn-vue` | `IssueList` | Vue-Komponente | – | `components/views/IssueList.vue` |
| `@flowaudit/bpmn-vue` | `LISTS` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-vue` | `LegalBasisEditor` | Vue-Komponente | – | `panels/legal/LegalBasisEditor.vue` |
| `@flowaudit/bpmn-vue` | `ListDescriptor` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-vue` | `Locale` | Re-Export | – | `./i18n/useI18n` |
| `@flowaudit/bpmn-vue` | `MESSAGES_DE` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-vue` | `MESSAGES_EN` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-vue` | `PropertiesPanel` | Vue-Komponente | – | `panels/PropertiesPanel.vue` |
| `@flowaudit/bpmn-vue` | `RestCatalogue` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-vue` | `RestEsi` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-vue` | `RestLegalSearch` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-vue` | `RestOptions` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-vue` | `RestProfiles` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-vue` | `RestStorage` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-vue` | `RestValidation` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-vue` | `SelectionStore` | Typ | – | `stores/selectionStore` |
| `@flowaudit/bpmn-vue` | `TABS` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-vue` | `TabDefinition` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-vue` | `ToolbarAction` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-vue` | `ValidationStore` | Typ | – | `stores/validationStore` |
| `@flowaudit/bpmn-vue` | `bindEditorCore` | Funktion | Vue view of an editor controller: reactive `state` and the instance as computed. | `stores/editorStore` |
| `@flowaudit/bpmn-vue` | `bindSelectionCore` | Funktion | – | `stores/selectionStore` |
| `@flowaudit/bpmn-vue` | `bindValidationCore` | Funktion | – | `stores/validationStore` |
| `@flowaudit/bpmn-vue` | `createCollectionStore` | Funktion | – | `stores/collectionStore` |
| `@flowaudit/bpmn-vue` | `createEditorStore` | Funktion | – | `stores/editorStore` |
| `@flowaudit/bpmn-vue` | `createI18n` | Funktion | – | `i18n/useI18n` |
| `@flowaudit/bpmn-vue` | `createSelectionStore` | Funktion | – | `stores/selectionStore` |
| `@flowaudit/bpmn-vue` | `createValidationStore` | Funktion | – | `stores/validationStore` |
| `@flowaudit/bpmn-vue` | `defaultEditorFactory` | Konstante | – | `editor/defaultFactory` |
| `@flowaudit/bpmn-vue` | `provideEditorContext` | Funktion | – | `stores/context` |
| `@flowaudit/bpmn-vue` | `provideI18n` | Funktion | – | `i18n/useI18n` |
| `@flowaudit/bpmn-vue` | `restPorts` | Re-Export | – | `@flowaudit/bpmn-flowaudit/ui` |
| `@flowaudit/bpmn-vue` | `useEditorContext` | Funktion | – | `stores/context` |
| `@flowaudit/bpmn-vue` | `useI18n` | Funktion | Injected i18n, or a German default when used standalone. | `i18n/useI18n` |
| `@flowaudit/bpmn-vue` | `useStore` | Funktion | – | `composables/useStore` |

### Props und Ereignisse der Vue-Komponenten

#### `BaseDialog`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `open` | `boolean` | ja | – | – |
| `title` | `string` | ja | – | – |
| `width` | `string` | nein | `'640px'` | – |
| `subtitle` | `string` | nein | `''` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `update:open` | `[value: boolean]` | – |
| `close` | `[]` | – |

#### `CollectionTree`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `store` | `CollectionStore` | ja | – | – |
| `selectedDiagram` | `string \| null` | ja | – | – |
| `openDiagram` | `string \| null` | ja | – | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `select-diagram` | `[id: string \| null]` | – |
| `open-diagram` | `[id: string]` | – |

#### `DiagramInfoColumn`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `store` | `CollectionStore` | ja | – | – |
| `entry` | `DiagramEntry` | ja | – | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `open` | `[id: string]` | – |
| `deleted` | `[]` | – |

#### `FaIcon`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `name` | `string` | ja | – | – |
| `size` | `number` | nein | `18` | – |
| `label` | `string` | nein | `''` | – |

#### `FlowauditEditor`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `xml` | `string` | ja | – | – |
| `name` | `string` | nein | `''` | – |
| `diagramId` | `string` | nein | `undefined` | – |
| `profile` | `ProfileData \| null` | nein | `null` | – |
| `profiles` | `ProfileSummary[]` | nein | `() => []` | – |
| `ports` | `EditorPorts & { validation?: ValidationPort }` | nein | `() => ({})` | – |
| `locale` | `Locale` | nein | `'de'` | – |
| `readonly` | `boolean` | nein | – | – |
| `lockApproved` | `boolean` | nein | `true` | – |
| `comments` | `Comment[]` | nein | `() => []` | – |
| `approvals` | `Approval[]` | nein | `() => []` | – |
| `author` | `string` | nein | `''` | – |
| `compareSources` | `CompareSource[]` | nein | `() => []` | – |
| `palette` | `readonly PaletteColor[]` | nein | `undefined` | – |
| `roleAliases` | `RoleAlias[]` | nein | `() => []` | – |
| `replacements` | `Record<string, string>` | nein | `() => ({})` | – |
| `hiddenActions` | `ToolbarAction[]` | nein | `() => []` | – |
| `saving` | `boolean` | nein | – | – |
| `editorFactory` | `EditorFactory` | nein | `undefined` | – |
| `theme` | `'auto' \| 'light' \| 'dark'` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `update:xml` | `[xml: string]` | – |
| `update:name` | `[name: string]` | – |
| `update:comments` | `[comments: Comment[]]` | – |
| `save` | `[payload: { xml: string; info: DiagramInfo \| null }]` | – |
| `new` | `[]` | – |
| `analysis` | `[]` | – |
| `share` | `[]` | – |
| `export-excel` | `[]` | – |
| `approve` | `[payload: { xml: string; info: DiagramInfo }]` | – |
| `selection-change` | `[elementId: string \| null]` | – |
| `error` | `[message: string]` | – |
| `ready` | `[]` | – |
| `info-change` | `[info: DiagramInfo \| null]` | – |

#### `FlowauditWorkbench`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `storage` | `StoragePort` | ja | – | – |
| `profile` | `ProfileData \| null` | nein | `null` | – |
| `profiles` | `ProfileSummary[]` | nein | `() => []` | – |
| `ports` | `EditorPorts & { validation?: ValidationPort }` | nein | `() => ({})` | – |
| `locale` | `Locale` | nein | `'de'` | – |
| `author` | `string` | nein | `''` | – |
| `roleAliases` | `RoleAlias[]` | nein | `() => []` | – |
| `editorFactory` | `EditorFactory` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `open` | `[id: string]` | – |
| `error` | `[message: string]` | – |

#### `GroupOverview`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `overview` | `Overview` | ja | – | – |
| `profile` | `ProfileData \| null` | ja | – | – |
| `issues` | `ValidationIssue[]` | ja | – | – |
| `title` | `string` | ja | – | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `open` | `[id: string]` | – |

#### `IssueList`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `issues` | `ValidationIssue[]` | ja | – | – |
| `running` | `boolean` | nein | – | – |
| `error` | `string \| null` | nein | – | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `jump` | `[elementId: string]` | – |

#### `LegalBasisEditor`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `items` | `LegalBasis[]` | ja | – | – |
| `port` | `LegalSearchPort` | nein | – | – |
| `profileId` | `string` | nein | – | – |
| `disabled` | `boolean` | nein | – | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `update` | `[items: LegalBasis[]]` | – |

#### `PropertiesPanel`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `comments` | `Comment[]` | ja | – | – |
| `author` | `string` | ja | – | – |
| `palette` | `readonly PaletteColor[]` | nein | – | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `update:comments` | `[value: Comment[]]` | – |
<!-- api-overview:end -->

## Konfiguration

Sprache `locale` (`de`/`en`, `createI18n`, `MESSAGES_DE`/`MESSAGES_EN`),
Farbschema `theme` (`auto`/`light`/`dark`), Ports (`legalSearch`, `catalogue`,
`esi`, `validation`, Speicher) – über REST mit `restPorts` bzw. `RestStorage`,
`RestLegalSearch`, `RestCatalogue`, `RestProfiles`, `RestValidation`, `RestEsi`
oder eigene Implementierungen. Das Eigenschaften-Panel ist deklarativ: Reiter
in `TABS`, Felder und Listen in `LISTS`.

## Herkunft und Charakterisierung

Neuimplementierung im Clean-Room; portiert wurde nur FlowAudit-eigener Code aus
dem audit_designer (Paritätsinventar `docs/bpmn/paritaet-audit-designer.md`).
Tests mit Vitest und `@vue/test-utils`, Ende-zu-Ende mit Playwright gegen die
Demo (`npm run test:e2e`). Dokumentation: `docs/bpmn/frontend.md`.

## Abhängigkeiten

`@flowaudit/bpmn-editor@0.1.1`, `@flowaudit/bpmn-flowaudit@0.2.1` (Fachschicht und UI-Kern `./ui`), `@flowaudit/ui-core@0.2.0` (Fokusfalle der Dialoge); Peer
`vue@^3.5.0`. Die Web Component bündelt Vue mit.

## Sicherheit und Datenschutz

Netzwerkzugriffe nur über die konfigurierten Ports (REST gegen `api-base`
bzw. die Callbacks eines eigenen `storage`); keine CDN- oder Fremdaufrufe.
Diagramme, Kommentare und Freigaben liegen beim Speicher der Anwendung; die
Demo speichert im Browser. Freigegebene Stände sind standardmäßig
schreibgeschützt (`lockApproved`).

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
