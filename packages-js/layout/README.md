# @auditcore/layout

## Zweck

Wiederverwendbare Seitenlayouts und Oberflächenelemente für FlowAudit-Anwendungen mit Vue, Web Components, Hell-/Dunkelmodus, Login-Animationen und Exportaktionen.

Das Paket vereinheitlicht App-Kopfzeilen, Login-Seiten, Theme-Schalter,
Seitenübergänge und Save-/PDF-/JPG-Aktionen. Es übernimmt weder Routing,
Authentifizierung, Kontodaten noch die eigentliche Erzeugung von Exportdateien.

## Installation

```sh
npm install @auditcore/layout @auditcore/ui
```

Im auditcore-Repository: `npm ci` im Stammverzeichnis. Das Paket wird im
Workspace gebaut mit `npm run build -w @auditcore/layout`.

## Schnellstart

```ts
import { createApp, h } from 'vue'
import { FaAppLayout } from '@auditcore/layout'
import '@auditcore/layout/style.css'
import '@auditcore/ui/style.css'

const app = createApp({
  render: () => h(FaAppLayout, {
    brand: 'FlowAudit', logo: '/logo.svg', accountName: 'Ada Beispiel', accountImage: '/ada.jpg',
  }, {
    navigation: () => h('a', { href: '/pruefungen' }, 'Prüfungen'),
    default: () => h('h1', 'Übersicht'),
  }),
})
app.mount('#app')
```

## Einbindung

- **Vue:** `FaAppLayout` ordnet Marke links, Navigations- und Aktionsslots in der
  Kopfzeile und das optionale Benutzerbild rechts an. `FaLoginLayout` bietet
  Login-Slots und einen animierten Fisch; `fishImage` nimmt ein bestehendes
  Fischbild auf. `FaThemeSwitch` speichert die Wahl und synchronisiert
  `data-fa-theme`; mit `target="data-theme"` oder `target="class"` kann es den
  Selektor vorhandener Apps mitführen. `FaPageTransition` animiert den Wechsel
  von Vue-Router-Ansichten. `FaExportActions` emittiert `save` und `export`
  (`pdf`/`jpg`); die Anwendung führt die Aktionen aus.
- **Web Component:** `defineFlowauditLayoutElements()` aus
  `@auditcore/layout/elements` registriert im Light DOM die Tags
  `<flowaudit-app-layout>`, `<flowaudit-login-layout>`,
  `<flowaudit-page-transition>`, `<flowaudit-theme-switch>` und
  `<flowaudit-export-actions>`. Die Komponenten verwenden die Stile der Seite;
  `@auditcore/layout/style.css` und `@auditcore/ui/style.css` einbinden.
- **React und HTML:** Die Web Components lassen sich ohne Vue-Komponenten-Syntax
  in React und statischen HTML-Seiten verwenden. `vue` bleibt eine Peer-
  Abhängigkeit der Laufzeit. Slot-Inhalte werden über benannte HTML-Slots
  eingesetzt.

```ts
import { defineFlowauditLayoutElements } from '@auditcore/layout/elements'
import '@auditcore/layout/style.css'
import '@auditcore/ui/style.css'

defineFlowauditLayoutElements()
```

```html
<flowaudit-app-layout brand="FlowAudit" account-name="Ada Beispiel" account-image="/ada.jpg">
  <a slot="navigation" href="/pruefungen">Prüfungen</a>
  <main><h1>Übersicht</h1></main>
</flowaudit-app-layout>
```

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Exporte der Einstiegspunkte aus `package.json#exports` (10):

| Einstieg | Name | Art | Kurzbeschreibung (erste JSDoc-Zeile) | Modul |
|---|---|---|---|---|
| `@auditcore/layout` | `ExportFormat` | Typ | – | `types` |
| `@auditcore/layout` | `FaAppLayout` | Vue-Komponente | – | `FaAppLayout.vue` |
| `@auditcore/layout` | `FaExportActions` | Vue-Komponente | – | `FaExportActions.vue` |
| `@auditcore/layout` | `FaLoginLayout` | Vue-Komponente | – | `FaLoginLayout.vue` |
| `@auditcore/layout` | `FaPageTransition` | Vue-Komponente | – | `FaPageTransition.vue` |
| `@auditcore/layout` | `FaThemeSwitch` | Vue-Komponente | – | `FaThemeSwitch.vue` |
| `@auditcore/layout` | `LAYOUT_ELEMENTS` | Konstante | – | `elements` |
| `@auditcore/layout` | `defineFlowauditLayoutElements` | Funktion | Registriert die Layout-Web-Components im Light DOM, ohne vorhandene Tags zu überschreiben. | `elements` |
| `@auditcore/layout/elements` | `LAYOUT_ELEMENTS` | Konstante | – | `elements` |
| `@auditcore/layout/elements` | `defineFlowauditLayoutElements` | Funktion | Registriert die Layout-Web-Components im Light DOM, ohne vorhandene Tags zu überschreiben. | `elements` |

Web Components:

| Element | Vue-Komponente | Definiert in |
|---|---|---|
| `<flowaudit-app-layout>` | `FaAppLayout` | `elements.ts` |
| `<flowaudit-export-actions>` | `FaExportActions` | `elements.ts` |
| `<flowaudit-login-layout>` | `FaLoginLayout` | `elements.ts` |
| `<flowaudit-page-transition>` | `FaPageTransition` | `elements.ts` |
| `<flowaudit-theme-switch>` | `FaThemeSwitch` | `elements.ts` |

### Props und Ereignisse der Vue-Komponenten

#### `FaAppLayout`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `brand` | `string` | nein | `'FlowAudit'` | – |
| `logo` | `string` | nein | `''` | – |
| `logoAlt` | `string` | nein | `'Logo'` | – |
| `accountName` | `string` | nein | `''` | – |
| `accountImage` | `string` | nein | `''` | – |
| `accountHref` | `string` | nein | `''` | – |

#### `FaExportActions`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `saving` | `boolean` | nein | `false` | – |
| `disabled` | `boolean` | nein | `false` | – |
| `saveLabel` | `string` | nein | `'Speichern'` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `save` | `[]` | – |
| `export` | `[format: ExportFormat]` | – |

#### `FaLoginLayout`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `brand` | `string` | nein | `'FlowAudit'` | – |
| `logo` | `string` | nein | `''` | – |
| `logoAlt` | `string` | nein | `'Logo'` | – |
| `fishImage` | `string` | nein | `''` | – |
| `title` | `string` | nein | `'Willkommen zurück'` | – |
| `subtitle` | `string` | nein | `'Melden Sie sich an, um fortzufahren.'` | – |

#### `FaPageTransition`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `name` | `string` | nein | `'fa-page'` | – |
| `mode` | `'in-out' \| 'out-in' \| 'default'` | nein | `'out-in'` | – |
| `appear` | `boolean` | nein | `true` | – |

#### `FaThemeSwitch`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `storageKey` | `string` | nein | `'fa-theme'` | – |
| `label` | `string` | nein | `'Farbschema wechseln'` | – |
| `target` | `ThemeTarget` | nein | `'auditcore'` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `change` | `[mode: 'light' \| 'dark']` | – |
<!-- api-overview:end -->

## Konfiguration

- `FaAppLayout`: `brand`, `logo`, `logoAlt`, `accountName`, `accountImage`,
  `accountHref`; Slots `navigation`, `actions`, `account` und Inhalt.
- `FaLoginLayout`: Marken- und Titeltexte, optional `logo` und `fishImage`;
  Login-Formular im Inhaltsslot, eigener Theme-Schalter im `theme`-Slot.
- `FaThemeSwitch`: `storageKey`, `label` und `target` (`auditcore`, `data-theme`
  oder `class`). Ohne gespeicherte Wahl folgt er der Systemeinstellung.
- `FaPageTransition`: Vue-Transition-Optionen `name`, `mode` und `appear`.
- `FaExportActions`: `saving`, `disabled` und `saveLabel`; Ereignisse `save` und
  `export` mit `pdf` oder `jpg`.
- Animationen beachten `prefers-reduced-motion`.

## Herkunft und Charakterisierung

Die Paketgrenze und Interaktionsmuster wurden mit vorhandenen Vue-, React- und
HTML-Oberflächen in den FlowAudit-Repositories abgeglichen. Das Paket ist eine
neue Komponentenbibliothek; die Fisch-SVG-Illustration ist eigens dafür erstellt.
Die bestehenden Apps bleiben getrennt und können schrittweise migrieren.

Die repositoryweite Bestandsaufnahme und empfohlene Einbindung stehen in
[`docs/ui/layout-uebernahmeplanung.md`](../../docs/ui/layout-uebernahmeplanung.md).

## Abhängigkeiten

- `@auditcore/ui@0.4.0` für Designtoken, Icons und Light-DOM-Web-Component-Helfer.
- `vue@^3.5.0` als Peer-Abhängigkeit.
- Keine API- oder Dateisystemzugriffe. Speicher- und Exportlogik verbleibt in
  der Host-Anwendung.

## Sicherheit und Datenschutz

Das Paket verarbeitet keine Anmeldedaten und sendet keine Anfragen. Ein
`accountImage`- oder `fishImage`-Pfad wird vom Browser der Host-Anwendung geladen.
Der Theme-Schalter speichert ausschließlich den Wert `light` oder `dark` unter
dem konfigurierten Schlüssel in `localStorage`.

## Lizenz und Herkunftsnachweis

MIT-Lizenz, siehe [LICENSE](LICENSE). Paketursprung und Einordnung stehen in
[`provenance.json`](provenance.json); Komponentenbeschreibungen stammen aus dem
öffentlichen TypeScript-/Vue-API-Vertrag.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
