# Frontend-Pakete in einer Anwendung nutzen (Vue, React, Web Components)

Diese Anleitung beschreibt, wie eine Anwendung außerhalb dieses Repositorys die
npm-Pakete unter `packages-js/` einbindet. Für die Python-Pakete gelten
[package-feed.md](package-feed.md) und [library-installation.md](library-installation.md).

**Bezugswege:**

1. **npm-Registry (Standard):** `npm install @flowaudit/<paket>`. Der
   Workflow `npm-publish` veröffentlicht nach jedem GitHub-Release genau die
   signierten Tarballs dieses Releases auf npmjs.org, mit Herkunftsnachweis
   (npm provenance). Die erste Veröffentlichung folgt mit dem ersten Release
   nach v0.4.1, sobald die Organisation `@flowaudit` auf npm eingerichtet ist
   ([npm-veroeffentlichung.md](npm-veroeffentlichung.md)); bis dahin liefert
   `npm view @flowaudit/ui` noch 404.
2. **Tarball aus dem GitHub-Release (Intranet, offline, ohne Registry):**
   dieselben Dateien als `npm pack`-Tarballs, SHA-256-gebunden und signiert,
   beginnend mit dem ersten Release nach v0.4.1; v0.4.1 und ältere Releases
   enthalten keine Tarballs. Abschnitt
   [Ohne Registry](#ohne-registry-tarballs-aus-dem-release).
3. **Selbst gepackt** für einen unveröffentlichten Stand (Abschnitt
   [Ohne Release](#ohne-release-tarballs-selbst-packen)).

Registry und Release enthalten byte-gleiche Pakete: `dist.integrity` auf npm
ist die `integrity` aus `npm-packages.json`.

## Installation aus der npm-Registry

```bash
npm install @flowaudit/ui vue                     # Vue-Komponenten und Web Components
npm install @flowaudit/ui-react react react-dom   # React 18.3 oder 19, ohne Vue
npm install @flowaudit/bpmn-vue vue               # BPMN-Editor (Vue, Web Component)
npm install @flowaudit/bpmn-react react react-dom # BPMN-Editor (React)
```

npm löst die übrigen `@flowaudit`-Pakete der Hülle (Tabelle unten) selbst auf
und schreibt `resolved` und `integrity` in `package-lock.json`; im Build und in
der CI dann nur `npm ci`. Die internen Abhängigkeiten sind auf genaue
Versionen festgelegt, gemischte Stände entstehen nicht.

Herkunft prüfen (Signatur des Registry-Eintrags und Provenance-Nachweis, der
auf Workflow und Commit in `janpow77/auditcore` verweist):

```bash
npm audit signatures
npm view @flowaudit/ui dist.integrity   # gleich der integrity aus npm-packages.json
```

Vorabversionen (`x.y.z-rc.1` usw.) tragen den dist-tag `next` und kommen nur
mit `npm install @flowaudit/ui@next`; `latest` bleibt die letzte stabile
Version.

## Überblick

| Paket | Wofür | Framework | Laufzeitabhängigkeiten im Scope |
|---|---|---|---|
| `@flowaudit/common` | Hilfsfunktionen: deutsche Formatierung, Zahleneingabe, Fehlertexte, REST, Token, CSV, Sortierung, Prüfziffern | keines | – |
| `@flowaudit/ui-core` | Gemeinsamer Kern der Oberflächen: Texte, REST-Verträge, Zustandsautomaten, Ports, Designtoken und Stile (`style.css`) | keines | `common` |
| `@flowaudit/ui` | Oberflächenkomponenten als Vue-3-Komponenten und als Web Components (`@flowaudit/ui/elements`) | Vue 3.5 | `common`, `ui-core`, `kanban-core` |
| `@flowaudit/ui-react` | Native React-Komponenten (Tabelle, Synopse, VVT, DSFA, Geo-Karte, Risiko-Merkmale, Screening, Stichprobe, Benford, Kanban, Grundbausteine, Hooks) ohne Vue-Laufzeit | React 18.3/19 | `common`, `ui-core`, `kanban-core` |
| `@flowaudit/kanban-core` | Kanban-Logik (Rang, Übergänge, WIP, Filter, Rechte), gleiche Regeln wie `auditcore_kanban` | keines | – |
| `@flowaudit/bpmn-editor` | BPMN-2.0-Zeicheneditor auf Basis von diagram-js | keines | – |
| `@flowaudit/bpmn-flowaudit` | FlowAudit-Fachschicht für BPMN (Schema flowaudit 1.0/1.1, Prüfpfad, Berichte) | keines | (`bpmn-editor` als optionale Peer-Abhängigkeit) |
| `@flowaudit/bpmn-vue` | BPMN-Oberfläche: Vue-Bibliothek, Web Component `<flowaudit-bpmn-editor>`, eigenständige App | Vue 3.5 | `bpmn-editor`, `bpmn-flowaudit`, `ui-core` (dazu transitiv `common`) |
| `@flowaudit/bpmn-react` | Native React-Oberfläche des BPMN-Editors ohne Vue-Laufzeit | React 18.3/19 | `bpmn-editor`, `bpmn-flowaudit`, `ui-core` (dazu transitiv `common`) |

### Ohne Registry: Tarballs aus dem Release

Dieser Weg gilt für Umgebungen ohne Zugang zu npmjs.org und für Anwendungen,
die jeden Frontend-Baustein als Datei im eigenen Repository führen.

Die letzte Spalte ist beim Tarball-Weg entscheidend: **Jedes Paket der
Hülle muss in der Anwendung ausdrücklich mit seiner Tarball-URL stehen.**
npm prüft die internen Versionsangaben (z. B. `"@flowaudit/common": "0.1.0"`
in `@flowaudit/ui`) dann gegen diese Einträge und fragt die Registry nicht. Fehlt ein Eintrag,
sucht npm das Paket auf registry.npmjs.org und mischt so Registry- und
Tarball-Stand oder scheitert ohne Netz. Deshalb gehört beim Tarball-Weg
zusätzlich eine Sperre in die `.npmrc` der Anwendung (beim Registry-Weg
nicht):

```ini
# .npmrc – @flowaudit-Pakete nie aus einer Registry beziehen
@flowaudit:registry=https://npm-registry.invalid/
```

Mit dieser Zeile schlägt ein vergessener Eintrag sofort fehl (`ENOTFOUND`),
statt still aus einer Registry zu laden. Ein `overrides`-Block ist nicht nötig:
npm (ab Version 7) übernimmt die ausdrücklich genannten Tarballs für alle
internen Abhängigkeiten, doppelte Kopien entstehen nicht (geprüft, siehe
[Nachweis](#nachweis)).

## Release-Dateien und Prüfung

Jeder Release mit npm-Paketen enthält:

| Datei | Inhalt |
|---|---|
| `flowaudit-<paket>-<version>.tgz` | Ergebnis von `npm pack` für jedes Paket unter `packages-js/` |
| `npm-packages.json` | je Paket Version, URL, npm-Integrität (`sha512-…`), SHA-256, interne Abhängigkeiten, die vollständige Hülle (`install_closure`) und fertige `package.json`-Einträge (`package_json_dependencies`) |
| `SHA256SUMS`, `SHA256SUMS.asc` | SHA-256 aller Release-Dateien (Wheels, Debian-Pakete, Tarballs, Manifeste) und die abgetrennte Signatur darüber |
| `auditcore-preview-keyring.gpg` | öffentlicher Signaturschlüssel, Fingerprint `E427F95CC37CBFD0876314CA0D1580A6CAE37327` (wie bei den Python-Paketen) |

Die Tarballs entstehen in `scripts/prepare_library_release.py` aus dem
committeten Stand von `packages-js/` (`npm run build`, dann
`npm pack --workspaces`). Das Skript bricht ab, wenn ein Paket fehlt, nicht
MIT-lizenziert oder `private` ist, wenn die gebauten Einstiegspunkte
(`package.json#exports`) im Tarball fehlen, die Integrität nicht der von npm
gemeldeten entspricht oder eine interne Abhängigkeit nicht durch ein Paket
desselben Releases erfüllt wird. `npm pack` ist reproduzierbar: gleicher
Quellstand ergibt dieselbe Integrität.

Der Workflow `npm-publish` veröffentlicht genau diese Tarballs auf npmjs.org,
nachdem er Signatur, SHA-256, Größe und Integrität gegen `npm-packages.json`
geprüft hat; neu gebaut wird dabei nichts
([npm-veroeffentlichung.md](npm-veroeffentlichung.md)).

Prüfung vor der Übernahme (`<release>` durch die Release-Version ersetzen):

```bash
BASE=https://github.com/janpow77/auditcore/releases/download/v<release>
for f in SHA256SUMS SHA256SUMS.asc auditcore-preview-keyring.gpg npm-packages.json; do
  curl -fsSLO "$BASE/$f"
done
gpg --show-keys --with-fingerprint auditcore-preview-keyring.gpg   # Fingerprint abgleichen
gpgv --keyring ./auditcore-preview-keyring.gpg SHA256SUMS.asc SHA256SUMS
sha256sum --check --ignore-missing SHA256SUMS                       # prüft npm-packages.json
```

Die Integrität aus `npm-packages.json` ist genau der Wert, den npm in
`package-lock.json` schreibt; `npm ci` bricht bei jeder Abweichung ab.

## Vue-Anwendung

### Installation

Aus der Registry: `npm install @flowaudit/ui vue` (siehe oben). Ohne Registry
liefert `npm-packages.json` die Einträge für `@flowaudit/ui` samt Hülle:

```bash
deps=$(node -e '
  const m = require("./npm-packages.json")
  const p = m.packages.find((x) => x.name === process.argv[1])
  console.log(Object.entries(p.package_json_dependencies).map(([n, u]) => `${n}@${u}`).join(" "))
' @flowaudit/ui)
npm install $deps vue
```

Das ergibt in `package.json` (Versionen je nach Release):

```json
{
  "dependencies": {
    "@flowaudit/common": "https://github.com/janpow77/auditcore/releases/download/v<release>/flowaudit-common-0.1.0.tgz",
    "@flowaudit/kanban-core": "https://github.com/janpow77/auditcore/releases/download/v<release>/flowaudit-kanban-core-0.2.0.tgz",
    "@flowaudit/ui": "https://github.com/janpow77/auditcore/releases/download/v<release>/flowaudit-ui-0.3.0.tgz",
    "@flowaudit/ui-core": "https://github.com/janpow77/auditcore/releases/download/v<release>/flowaudit-ui-core-0.1.0.tgz",
    "vue": "^3.5.0"
  }
}
```

und in `package-lock.json` je Paket `resolved` (die URL) und `integrity`
(`sha512-…`). Beides wird mit committet; im Build und in der CI nur `npm ci`.

**Alternative: Ablage im Repository (`vendor/`).** Wer beim Bau keinen Zugriff
auf GitHub hat, legt die Tarballs ins Anwendungsrepository, wie regulierung es
für `@flowaudit/common` tut:

```text
frontend/vendor/flowaudit-ui-0.3.0.tgz
frontend/vendor/flowaudit-ui-0.3.0.provenance.json
```

```json
{
  "package": "@flowaudit/ui",
  "version": "0.3.0",
  "file": "flowaudit-ui-0.3.0.tgz",
  "source_repository": "https://github.com/janpow77/auditcore",
  "release": "v<release>",
  "source_commit": "<source_commit aus npm-packages.json>",
  "license": "MIT",
  "sha256": "<sha256 aus npm-packages.json>",
  "npm_integrity": "<integrity aus npm-packages.json>"
}
```

In `package.json` steht dann `"@flowaudit/ui": "file:vendor/flowaudit-ui-0.3.0.tgz"`
(ebenso für jedes Paket der Hülle). npm schreibt die Integrität auch hier in
`package-lock.json`; sie muss mit der Herkunftsdatei übereinstimmen.

### Einbindung

- **Plugin und Komponenten:** `app.use(createFlowauditUi({ locale }))` stellt
  die Sprache app-weit bereit; Komponenten werden direkt importiert
  (`FaTable`, `FaButton`, `FaDialog`, `FaSynopsis`, `FaVvt`, `FaDsfa`,
  `KanbanBoard`, `SamplingPanel`, `BenfordPanel`, `ScreeningReview`,
  `RiskFlags`, `FaGeoMap` …).
- **Stile:** einmal `import '@flowaudit/ui/style.css'`. Farben, Abstände,
  Radien und Schriften sind CSS-Variablen `--fa-*`; die Anwendung überschreibt
  sie bei Bedarf in ihrem eigenen CSS.
- **Hell/Dunkel:** hell ist Standard, dunkel über `data-fa-theme="dark"` am
  `<html>`; ohne Attribut folgt die Darstellung `prefers-color-scheme`.
  `applyTheme('dark' | 'light' | 'system')` oder das Composable `useTheme()`
  (`mode`, `setMode`, `toggle`).
- **Sprache:** `'de'` (vollständig, Standard) oder `'en'`; als `Ref` an das
  Plugin übergeben, damit sie umschaltbar bleibt, oder als Prop `locale` an
  einzelnen Komponenten.

### Minimalbeispiel

Vollständig und in der CI gebaut: [`examples/vue-minimal`](../../examples/vue-minimal).

```ts
// src/main.ts
import { createApp, ref } from 'vue'
import { createFlowauditUi, type Locale } from '@flowaudit/ui'
import '@flowaudit/ui/style.css'
import App from './App.vue'

const locale = ref<Locale>('de')
createApp(App).use(createFlowauditUi({ locale })).mount('#app')
```

```vue
<!-- src/App.vue -->
<script setup lang="ts">
import { FaButton, FaTable, useTheme, type TableColumn } from '@flowaudit/ui'

const columns: TableColumn[] = [
  { key: 'beleg', label: 'Beleg', sortable: true },
  { key: 'betrag', label: 'Betrag (EUR)', align: 'end' },
]
const rows = [{ id: 'r1', beleg: 'R-2026-001', betrag: 1250.5 }]
const theme = useTheme()
</script>

<template>
  <FaButton @click="theme.toggle()">Hell/Dunkel</FaButton>
  <FaTable :columns="columns" :rows="rows" caption="Belege" clickable @row-click="(row) => console.log(row)" />
</template>
```

## React-Anwendung

### Installation

`@flowaudit/ui-react` enthält native React-Komponenten und braucht **kein
Vue**. Hülle: `ui-react`, `ui-core`, `kanban-core`, `common`.

```bash
npm install @flowaudit/ui-react react react-dom   # aus der Registry
```

Ohne Registry:

```bash
deps=$(node -e '
  const m = require("./npm-packages.json")
  const p = m.packages.find((x) => x.name === process.argv[1])
  console.log(Object.entries(p.package_json_dependencies).map(([n, u]) => `${n}@${u}`).join(" "))
' @flowaudit/ui-react)
npm install $deps react react-dom   # React 18.3 oder 19
```

Die `vendor/`-Ablage funktioniert wie bei Vue.

### Einbindung

- **Komponenten:** `FlowauditTable`, `FlowauditSynopsis`, `FlowauditVvt`,
  `FlowauditDsfa`, `FlowauditGeoMap`, `FlowauditRiskFlags`,
  `FlowauditScreeningReview`, `FlowauditSampling`, `FlowauditBenford`,
  `FlowauditKanbanBoard`, `FlowauditKanbanBoards` sowie die Grundbausteine `Button`, `Dialog`, `TextField`,
  `Badge`, `Icon` und Hooks (`useSort`, `useToast` mit `ToastProvider`,
  `useMediaQuery`, `useClickOutside`, `useDebouncedCallback`,
  `useAuthToken`). Gleiche Verträge, Texte und Barrierefreiheit wie die
  Vue-Fassung (Paritätstests: [react-paritaet.md](../ui/react-paritaet.md)).
  Ereignisse sind `onXxx`-Props; was in Vue ein `v-model` ist, ist hier
  gesteuert (`sort`/`onSortChange`) oder ungesteuert (`defaultSort`).
- **Stile:** einmal `import '@flowaudit/ui-core/style.css'` (Designtoken
  `--fa-*` und Komponentenstile).
- **Hell/Dunkel:** wie bei Vue über `data-fa-theme` am `<html>`
  (`document.documentElement.dataset.faTheme = 'dark'`); ohne Attribut gilt
  `prefers-color-scheme`.
- **Sprache:** `LocaleProvider` um den Teilbaum, Prop `locale` an einzelnen
  Komponenten oder `setDefaultLocale('en')`.
- **Datenzugriff:** über Ports aus `@flowaudit/ui-core`
  (z. B. `createSynopsisRestClient`, `createDataProtectionRestPort`); `fetch` und
  Kopfzeilen (Anmeldetoken) gibt die Anwendung vor.
- **BPMN:** `@flowaudit/bpmn-react` ist die native React-Oberfläche des
  BPMN-Editors (ohne Vue) auf demselben Kern wie `@flowaudit/bpmn-vue`; Stile
  aus `@flowaudit/bpmn-react/style.css`.

### Minimalbeispiel

Vollständig und in der CI gebaut: [`examples/react-minimal`](../../examples/react-minimal).

```tsx
import { useState } from 'react'
import { createRoot } from 'react-dom/client'
import { FlowauditTable, LocaleProvider, type Locale, type TableColumn } from '@flowaudit/ui-react'
import '@flowaudit/ui-core/style.css'

const columns: TableColumn[] = [
  { key: 'beleg', label: 'Beleg', sortable: true },
  { key: 'betrag', label: 'Betrag (EUR)', align: 'end' },
]
const rows = [{ id: 'r1', beleg: 'R-2026-001', betrag: 1250.5 }]

function App() {
  const [locale] = useState<Locale>('de')
  return (
    <LocaleProvider locale={locale}>
      <FlowauditTable columns={columns} rows={rows} caption="Belege" clickable onRowClick={(row) => console.log(row)} />
    </LocaleProvider>
  )
}

createRoot(document.getElementById('root')!).render(<App />)
```

## Ohne Framework: Web Components per `<script type="module">`

`@flowaudit/ui/elements` registriert `<flowaudit-table>`,
`<flowaudit-synopsis>`, `<flowaudit-vvt>`, `<flowaudit-dsfa>`,
`<flowaudit-kanban-board>`, `<flowaudit-kanban-boards>`,
`<flowaudit-sampling>`, `<flowaudit-benford>`,
`<flowaudit-screening-review>`, `<flowaudit-risk-flags>` und
`<flowaudit-geo-map>` im Light DOM (Designtoken der Seite gelten). Die Module
importieren `vue`, `@flowaudit/ui-core`, `@flowaudit/common`,
`@flowaudit/kanban-core` und bei der Geo-Karte `leaflet` über Paketnamen;
ohne Bundler bildet eine Import-Map diese Namen auf Dateien ab. Installation
wie bei Vue (Hülle von `@flowaudit/ui` plus `vue`), danach die Dateien aus
`node_modules/` mit dem Webserver ausliefern:

```html
<link rel="stylesheet" href="./node_modules/@flowaudit/ui/dist/ui.css" />
<script type="importmap">
  {
    "imports": {
      "@flowaudit/ui/elements": "./node_modules/@flowaudit/ui/dist/elements.js",
      "@flowaudit/ui-core": "./node_modules/@flowaudit/ui-core/dist/index.js",
      "@flowaudit/common": "./node_modules/@flowaudit/common/dist/index.js",
      "@flowaudit/common/browser": "./node_modules/@flowaudit/common/dist/browser.js",
      "@flowaudit/kanban-core": "./node_modules/@flowaudit/kanban-core/dist/index.js",
      "vue": "./node_modules/vue/dist/vue.esm-browser.prod.js",
      "leaflet": "./node_modules/leaflet/dist/leaflet-src.esm.js"
    }
  }
</script>
<flowaudit-table id="belege"></flowaudit-table>
<script type="module">
  import { defineFlowauditElements } from '@flowaudit/ui/elements'

  defineFlowauditElements({ locale: 'de' })
  const table = document.getElementById('belege')
  table.columns = [{ key: 'beleg', label: 'Beleg' }]   // Objekte als JS-Eigenschaften
  table.rows = [{ id: 'r1', beleg: 'R-2026-001' }]
  table.addEventListener('row-click', (event) => console.log(event.detail[0]))
</script>
```

Ereignisse sind `CustomEvent`s in kebab-case, die Nutzdaten stehen in
`event.detail[0]`. Hell/Dunkel über `data-fa-theme` am `<html>`, Sprache über
`defineFlowauditElements({ locale })`. Beispiel mit Prüfung der Import-Map:
[`examples/webcomponent-minimal`](../../examples/webcomponent-minimal).

Der BPMN-Editor braucht keine Import-Map: `@flowaudit/bpmn-vue/web-component`
(`dist-wc/flowaudit-bpmn-editor.js`) ist ein einzelnes Modul mit Vue, Kern,
Fachschicht, Profilen und CSS:

```html
<script type="module" src="./node_modules/@flowaudit/bpmn-vue/dist-wc/flowaudit-bpmn-editor.js"></script>
<flowaudit-bpmn-editor api-base="/api/bpmn" diagram-id="antragsverfahren" locale="de"></flowaudit-bpmn-editor>
```

## Aktualisieren und Pins prüfen

**Registry-Weg:** alle `@flowaudit`-Pakete gemeinsam anheben, z. B.
`npm install @flowaudit/ui@<version>`; `npm outdated` zeigt neue Versionen.
Danach `npm ci`, Build und Tests. Die Schritte unten gelten für den
Tarball-Weg.

1. Neuen Release wählen, `SHA256SUMS` und `npm-packages.json` wie oben prüfen.
2. Die Einträge aller `@flowaudit`-Pakete gemeinsam auf die URLs des neuen
   Releases umstellen (Befehl aus [Installation](#installation) erneut
   ausführen). Pakete verschiedener Releases nicht mischen: die internen
   Abhängigkeiten sind auf genaue Versionen festgelegt, und die Hülle stimmt
   nur innerhalb eines Releases.
3. Lock gegen das Manifest abgleichen:

   ```bash
   node -e '
     const lock = require("./package-lock.json"), rel = require("./npm-packages.json")
     for (const p of rel.packages) {
       const node = lock.packages["node_modules/" + p.name]
       if (node && node.integrity !== p.integrity) { console.error("Abweichung:", p.name); process.exitCode = 1 }
     }'
   ```

4. `npm ci`, Build und Tests der Anwendung. Änderungen der Komponenten stehen
   im `CHANGELOG.md` des jeweiligen Pakets; eine neue Hauptversion (z. B.
   `@flowaudit/ui-react` 1.0.0) kann die Props ändern.

`npm update` ändert an URL-Einträgen nichts; ein Wechsel geschieht nur
ausdrücklich über neue URLs.

## Gegenstellen: REST-Verträge und Python-Pakete

Die Fachkomponenten sprechen versionierte REST-Verträge. Die Serverseite
liefert jeweils ein Python-Paket, installiert wie in
[package-feed.md](package-feed.md) beschrieben, mit dem genannten Extra
(`web` für Starlette, `fastapi` für einen FastAPI-Router).

| Komponente (Vue / React / Web Component) | Vertrag | Python-Gegenstelle |
|---|---|---|
| `FaSynopsis` / `FlowauditSynopsis` / `<flowaudit-synopsis>` | [synopsis-rest.md](../ui/synopsis-rest.md) | `auditcore_documents.web` (`[web]` oder `[fastapi]`) |
| `FaVvt`, `FaDsfa` / `FlowauditVvt`, `FlowauditDsfa` / `<flowaudit-vvt>`, `<flowaudit-dsfa>` | `dataprotection_ui/1`, [dataprotection-rest.md](../ui/dataprotection-rest.md) | `auditcore_dataprotection.web` (`[web]` oder `[fastapi]`) |
| `SamplingPanel` / `FlowauditSampling` / `<flowaudit-sampling>` | [sampling-rest.md](../ui/sampling-rest.md) | `auditcore_sampling.web` (`[web]`) |
| `BenfordPanel` / `FlowauditBenford` / `<flowaudit-benford>` | [benford-rest.md](../ui/benford-rest.md) | `auditcore_statistics.web` (`[web]`) |
| `ScreeningReview` / `FlowauditScreeningReview` / `<flowaudit-screening-review>` | `screening_review/1`, [screening-rest.md](../ui/screening-rest.md) | `auditcore_registry_sources.web` (`[web]` oder `[fastapi]`) |
| `RiskFlags` / `FlowauditRiskFlags` / `<flowaudit-risk-flags>` | [risk-rest.md](../ui/risk-rest.md) | `auditcore_risk.web` (`[web]` oder `[fastapi]`) |
| `FaGeoMap` / `FlowauditGeoMap` / `<flowaudit-geo-map>` | [geo-rest.md](../ui/geo-rest.md) | `auditcore_geo.web` (`[web]` oder `[fastapi]`) |
| `KanbanBoard`, `KanbanBoardList` / `FlowauditKanbanBoard`, `FlowauditKanbanBoards` / `<flowaudit-kanban-board>` | [kanban/rest-api.md](../kanban/rest-api.md) | `auditcore_kanban.rest` (`[ui]` oder `[fastapi]`) |
| `<flowaudit-bpmn-editor>` (`api-base`) | [bpmn/rest-api.md](../bpmn/rest-api.md) | noch kein Server im Paket; `auditcore_bpmn` liest und prüft dasselbe BPMN (Schema flowaudit 1.1) |

`@flowaudit/common` und `@flowaudit/kanban-core` rechnen mit denselben Regeln
wie `auditcore_common` bzw. `auditcore_kanban` (gemeinsame Fixtures), sodass
Anzeige im Browser und Prüfung auf dem Server übereinstimmen. Maßgeblich bleibt
stets die Prüfung auf dem Server.

## Ohne Release: Tarballs selbst packen

Solange kein Release mit Tarballs vorliegt, oder für einen unveröffentlichten
Stand:

```bash
git clone https://github.com/janpow77/auditcore && cd auditcore
npm ci && npm run build
npm pack --workspaces --json --pack-destination ../vendor   # Integrität steht in der Ausgabe
```

Die Tarballs dann wie bei der `vendor/`-Ablage einbinden und in der
Herkunftsdatei statt des Releases den Commit festhalten.

## Nachweis

`node scripts/js/verify-examples.mjs` installiert die Beispiele unter
`examples/` wie eine fremde Anwendung: frisches Verzeichnis, leere
npm-Konfiguration und leerer Cache, Registry für `@flowaudit` gesperrt,
`npm install`, Abgleich von `package-lock.json` (Version, `resolved`,
Integrität, keine doppelten Kopien) und `npm run build`. Die CI (Workflow
`js-packages`) führt das mit frisch gepackten Tarballs aus. Gegen einen
Release: `node scripts/js/verify-examples.mjs --base-url <Release-Downloadpfad>
--report <datei.json>`.

Vorabnachweis vom 26.09.2026 mit den Assets, die
`scripts/prepare_library_release.py` erzeugt, über HTTP bereitgestellt
(Nachbau des Release-Pfads, noch nicht der öffentliche GitHub-Release):
[npm-tarball-installation-preview.json](../reports/npm-tarball-installation-preview.json).
Vue-, React- und Web-Component-Beispiel: Installation und Build bestanden; die
drei gebauten Seiten wurden zusätzlich im Browser geöffnet (Tabelle,
Zeilenauswahl, Sprach- und Hell/Dunkel-Umschaltung). Der anonyme Test gegen
den öffentlichen Release-Pfad folgt nach dem ersten Upload mit Tarballs.
