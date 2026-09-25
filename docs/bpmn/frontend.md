# BPMN-Frontend: FlowAudit-Fachschicht, Vue-Oberfläche, Web Component, React

Drei Pakete bauen auf dem eigenen Editorkern `@flowaudit/bpmn-editor` auf
(alle MIT, Clean-Room – kein Code, keine Styles, keine Icons aus bpmn-js,
bpmn-js-properties-panel, @bpmn-io/properties-panel oder bpmn-font):

| Paket | Inhalt | Abhängigkeiten |
|---|---|---|
| `@flowaudit/bpmn-flowaudit` (`packages-js/bpmn-flowaudit`) | Fachschicht ohne Framework: moddle-Deskriptor flowaudit 1.0/1.1, Lesen/Schreiben der Erweiterungen, Rollen, Kennzeichen, Prüfbezüge, Prüfpfad, Prüfregeln, Anreicherung, Neutralisierung, Versions- und Soll/Ist-Vergleich, Berichte, Sammlung, Export, diagram-js-Module, Icons, Ports | `bpmn-moddle`; Kern optional |
| `@flowaudit/bpmn-vue` (`packages-js/bpmn-vue`) | Vue-3-Oberfläche, Web Component `<flowaudit-bpmn-editor>`, eigenständige App | Vue 3.5, Kern, Fachschicht |
| `@flowaudit/bpmn-react` (`packages-js/bpmn-react`) | dünner React-Wrapper um die Web Component | React 18.3 oder 19 |

Die Fachschicht greift nie aufs Netz oder eine Datenbank zu. Alles
Anwendungsspezifische kommt über **Ports** herein (`StoragePort`,
`LegalSearchPort`, `CataloguePort`, `ProfilePort`, `ValidationPort`,
`EsiPort`); für Demo und Tests gibt es Implementierungen im Speicher
(`InMemoryStorage`, `StaticProfilePort`, `ProfileCataloguePort`,
`ProfileLegalSearch`), für Server die REST-Ports aus `@flowaudit/bpmn-vue`
(Vertrag: [`rest-api.md`](rest-api.md)). Programmspezifisches (Namen von
Stellen, Förderprogramme) ist nicht eingebaut: Rollen-Aliasse, Profile und
Ersetzungen für die Neutralisierung liefert die Anwendung.

## Begriffe und Datenmodell

Bezeichner im Code sind englisch, deutsch sind nur UI-Texte (i18n-Tabellen)
und die XML-Namen des flowaudit-Schemas. Es gelten dieselben Begriffe wie in
`auditcore_bpmn`:

- `AuditFinding` – Feststellung der Prüfbehörde (`flowaudit:feststellung`),
- `ValidationIssue` – Meldung einer Prüfregel (`BPMN-S…`, `BPMN-F…`, `BPMN-P…`,
  `BPMN-FT…`, `BPMN-K…`), Texte identisch zum Regelkatalog von `auditcore_bpmn`
  (`src/validation/catalogRows.ts` wird mit `scripts/generate_rule_catalog.py`
  erzeugt),
- `DiagramInfo`, `LegalBasis`, `Control`, `Risk`, `Evidence`, `AuditStep`, … –
  gleiche Felder wie die Datenklassen von `auditcore_bpmn`; JSON in `snake_case`
  über `toWire`/`fromWire`.

Profile (Rollen, Fonds, KA/BK, Funktionstrennungsregeln) liegen nur einmal im
Repository, in `packages/auditcore_bpmn/src/auditcore_bpmn/profiles/data/`.
`@flowaudit/bpmn-flowaudit/profiles` liest sie beim Bauen ein
(`bundledProfiles()`, `defaultProfile()`); Tests prüfen Sammlung, Profile und
Prüfbericht gegen die JSON-Schemata von `auditcore_bpmn`.

## Nutzung in Vue

```ts
import { FlowauditEditor, FlowauditWorkbench, restPorts } from '@flowaudit/bpmn-vue'
import '@flowaudit/bpmn-vue/style.css'
import { InMemoryStorage } from '@flowaudit/bpmn-flowaudit'
import { defaultProfile } from '@flowaudit/bpmn-flowaudit/profiles'
```

```vue
<!-- nur Editor -->
<FlowauditEditor v-model:xml="xml" :name="name" :profile="profile" :ports="ports"
  @save="onSave" @selection-change="onSelect" />

<!-- Sammlung (Ordnerbaum, Tags, Filter, Info-Spalte, Gruppenübersicht) + Editor -->
<FlowauditWorkbench :storage="storage" :profile="profile" :ports="ports" author="Prüferin" />
```

Wichtige Eigenschaften von `FlowauditEditor`: `xml`, `name`, `diagramId`,
`profile`, `profiles`, `ports` (`legalSearch`, `catalogue`, `esi`,
`validation`), `locale` (`de`/`en`), `theme` (`auto`/`light`/`dark`),
`readonly`, `lockApproved` (freigegebene Stände schreibgeschützt, Standard an),
`comments`, `approvals`, `author`, `compareSources`, `palette`, `roleAliases`,
`replacements`, `hiddenActions`, `editorFactory`. Ereignisse: `update:xml`,
`update:name`, `update:comments`, `save`, `approve`, `new`, `analysis`,
`share`, `export-excel`, `selection-change`, `info-change`, `ready`, `error`.
Über die Komponenten-Referenz: `getXml()`, `getSvg()`, `select(id)`,
`highlightKey(kind, value)`.

Aufbau: kleine Komponenten (Werkzeugleiste, Palette, Zeichenfläche mit
Seitenraster, Statusleiste, Seitenleiste), Logik in Composables
(`useEditorSetup`, `useEditorActions`, `useExport`, `useShortcuts`), je
Bereich ein Store (`editorStore`, `selectionStore`, `validationStore`,
`collectionStore`). Das Eigenschaften-Panel ist deklarativ: Reiter in
`panels/tabs.ts`, Felder und Listen in `panels/descriptors.ts`, gerendert von
`FieldForm`/`ListEditor`.

Funktionsumfang: Eigenschaften-Panel mit den Reitern Allgemein, Rolle,
Rechtsgrundlagen (strukturiert mit Vorschlägen, Altbestand als Freitext mit
„Strukturieren“), Prüfbezug/Schlüssel, Kontrolle & Risiko, Nachweis/Prüfpfad,
Feststellungen, Quelle, Notizen, Farbe; Diagramm-Infos (alle Felder, Profil,
Fonds, Förderperiode, Status, Gültigkeit, Freigabe mit SHA-256,
Vertraulichkeit, Kopfzeile); Hinweisliste mit Sprung zum Element;
Durchlauftest; Versions- und Soll/Ist-Vergleich; Schlüsselfilter;
Exportdialog (SVG, PNG, PDF mit Seitenformat, BPMN, MyST, Prozesstabelle,
Risiko-Kontroll-Matrix, Feststellungsliste, neutral, Kopfzeile, Legenden);
Anreicherung mit Vorschlagsliste; ESI-Abgleich; Suche, Übersichtskarte,
Tastenkürzel (`?`), XML-Ansicht, hell/dunkel, Deutsch/Englisch. Eigene
SVG-Icons (24 px, `currentColor`) in `@flowaudit/bpmn-flowaudit` (`ICONS`).

## Web Component `<flowaudit-bpmn-editor>`

`@flowaudit/bpmn-vue/web-component` (`dist-wc/flowaudit-bpmn-editor.js`) ist ein
einzelnes ES-Modul mit Vue, Kern, Fachschicht, gebündelten Profilen und CSS –
keine CDN-Abhängigkeit. Das Element rendert im Light DOM, die Styles werden
einmal als `<style data-flowaudit-bpmn>` eingefügt.

```html
<script type="module" src="/static/flowaudit-bpmn-editor.js"></script>
<flowaudit-bpmn-editor api-base="/api/bpmn" diagram-id="antragsverfahren" locale="de"></flowaudit-bpmn-editor>
```

| Attribut | Bedeutung |
|---|---|
| `src` | URL einer BPMN-Datei (nur lesen, Speichern über das `save`-Ereignis) |
| `api-base` | Basis-URL des REST-Vertrags; stellt Speicher, Rechtsgrundlagen-Suche, KA/BK, Profile, Serverprüfung, ESI bereit |
| `diagram-id` | Diagramm im Speicher (mit `api-base` oder `storage`), wird dort auch gespeichert |
| `name`, `author` | Anzeigename des Diagramms, Bearbeiter/in |
| `locale` | `de` (Standard) oder `en` |
| `theme` | `auto` (Standard), `light`, `dark` |
| `readonly` | schreibgeschützt (boolesches Attribut) |
| `profile` | Profil-ID (vom Server, sonst gebündelt) |

Objekt-Eigenschaften (per JavaScript): `xml`, `storage` (eigener `StoragePort`
mit JS-Callbacks statt REST), `ports`, `profileData`, `comments`.

Ereignisse (`CustomEvent`, `bubbles` und `composed`, Nutzdaten in `detail`):
`ready` `{ diagramId }`, `change` `{ xml }`, `save` `{ xml, info }`,
`selection-change` `{ elementId }`, `diagram-info-change` `{ info }`,
`error` `{ message }`. Methoden: `getXml()`, `getSvg()`, `select(id)`,
`reload()`.

```js
const editor = document.querySelector('flowaudit-bpmn-editor')
editor.storage = {
  loadCollection: async () => null, saveCollection: async () => {},
  loadDiagram: async (id) => (await fetch(`/eigene/api/${id}`)).text(),
  saveDiagram: async (id, xml) => { await fetch(`/eigene/api/${id}`, { method: 'PUT', body: xml }) },
  deleteDiagram: async () => {},
}
editor.setAttribute('diagram-id', 'd1')
editor.addEventListener('save', (event) => console.log(event.detail.info))
```

## Eigenständige App

`dist-standalone/` (Ordner `packages-js/bpmn-vue/dist-standalone`) enthält die
fertige Single-Page-App aus Sammlung und Editor als statische Dateien mit
relativen Pfaden. Sie spricht den REST-Vertrag an; die API-Basis kommt aus
`window.FLOWAUDIT_CONFIG`, `<meta name="flowaudit-api-base">` oder `?api=…`
(Details in [`rest-api.md`](rest-api.md)). Vorgesehen ist, sie später im
Python-Paket mitzuliefern.

## Nutzung in React-Projekten

`@flowaudit/bpmn-react` baut keine Oberfläche nach, sondern kapselt die Web
Component typisiert. Zeichenketten werden Attribute, Objekte werden per `ref`
als Eigenschaften gesetzt, Ereignisse per `addEventListener` an die
`onXyz`-Props gebunden. Dadurch verhält sich der Wrapper unter React 18.3 und
19 gleich. Die Tests laufen mit React 18.3; mit `REACT_DIR=<Ordner mit React 19>`
laufen dieselben Tests gegen React 19 (lokal beide geprüft).

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
      profile="foerderperiode-2021-2027"
      onSave={({ xml, info }) => speichern(xml, info)}
      onSelectionChange={({ elementId }) => console.log(elementId)}
      onError={({ message }) => alert(message)}
      style={{ height: '80vh' }}
    />
  )
}
```

Props: `src`, `apiBase`, `diagramId`, `name`, `locale`, `theme`, `readonly`,
`profile`, `author` (Attribute); `xml`, `storage`, `ports`, `profileData`,
`comments` (Eigenschaften); `onReady`, `onChange`, `onSave`,
`onSelectionChange`, `onDiagramInfoChange`, `onError`; `className`, `style`.
Die Referenz bietet `element`, `getXml()`, `getSvg()`, `select(id)`. Der
Import von `@flowaudit/bpmn-react` registriert das Element; wer das Bündel
selbst lädt, importiert nur `@flowaudit/bpmn-react/component`.

## Entwicklung

```bash
npm ci
npm run test -w packages-js/bpmn-flowaudit      # Vitest (happy-dom)
npm run test -w packages-js/bpmn-vue            # Komponenten, Stores, Web Component
npm run test -w packages-js/bpmn-react          # @testing-library/react
npm run demo -w packages-js/bpmn-vue            # Demo mit synthetischen Diagrammen
npm run test:e2e -w packages-js/bpmn-vue        # Playwright gegen die Demo
BPMN_LOCAL_FIXTURES=/pfad/zu/diagrammen npm run test -w packages-js/bpmn-flowaudit
```

Die Demo nutzt nur synthetische Diagramme: die Vorlagen von `auditcore_bpmn`
und die Test-Fixtures. Eigene Diagramme gehören nicht ins Repository; der
Paritätstest `localParity.spec.ts` liest sie nur über `BPMN_LOCAL_FIXTURES`
und wird ohne die Variable übersprungen.

Paritätsinventar zum audit_designer: [`paritaet-audit-designer.md`](paritaet-audit-designer.md).
