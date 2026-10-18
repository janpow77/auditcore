# @auditcore/sampling-templates-vue

## Zweck

Vue-3-Oberfläche der „Stichprobenvorlagen 2021–2027“ nach DelVO (EU) 2023/67: ein Stichprobenrechner mit Verfahrensauswahl, Rechenblatt, mitlaufender Ergebnisspalte, Arbeitsstand als Datei und Excel-Export.

Für Anwendungen, die den Rechner als Ganzes einhängen (zuerst ECOHESION im
audit_designer), und für eigene Zusammenstellungen aus den Bausteinen. Die
Prüfbehörde gibt ein, lädt Ergebnisse herunter und speichert ihren Arbeitsstand
als Datei; es gibt keinen Server, keine Anmeldung und keine Netzanfragen.
Gerechnet wird in
[`@auditcore/sampling-templates-core`](../sampling-templates-core/README.md).
Stand 0.1.12: Alle Verfahren der Vorlage sind wählbar (MUS, einfaches
Zufallsstichprobenverfahren, nichtstatistische Verfahren, Altvorlagen von
2017), dazu die Arbeitsschritte Grundgesamtheit, Unterstichproben,
Gesamtfehlerquote und Bericht (Druckfassung: leeres Formular und
Beispielwerte auf einer A4-Seite, längere Freitexte laufen auf Folgeseiten
über). Eine
React-Fassung gibt es nicht.

## Installation

Standardweg ist die npm-Registry; npm löst die übrigen `@auditcore`-Pakete
der Abhängigkeitshülle selbst auf:

```sh
npm install @auditcore/sampling-templates-vue
```

Ohne Registry-Zugang (Intranet, offline) bleibt der Tarball aus dem
GitHub-Release von auditcore; dann gehört jedes Paket der Hülle ausdrücklich
in die `package.json`:

```sh
npm install @auditcore/sampling-templates-vue@https://github.com/janpow77/auditcore/releases/download/v<release>/auditcore-sampling-templates-vue-0.1.12.tgz
```

Version 0.1.12 ist noch nicht veröffentlicht. Anleitung mit Integritätsprüfung
und `vendor/`-Ablage:
[frontend-installation.md](../../docs/deployment/frontend-installation.md).

Abhängigkeitshülle: dazu `@auditcore/sampling-templates-core`, `@auditcore/ui`,
`@auditcore/ui-core`, `@auditcore/kanban-core`, `@auditcore/common` sowie
`fflate` und `leaflet` aus der Registry; Peer-Abhängigkeit `vue` ^3.5. Stile:
`@auditcore/ui/style.css` (Designtoken und Basiskomponenten) und
`@auditcore/sampling-templates-vue/style.css`. Wer nur den Rechner braucht,
lädt statt `@auditcore/ui/style.css` die beiden Dateien
`@auditcore/ui-core/styles/tokens.css` und `@auditcore/ui-core/styles/base.css`.

Im auditcore-Repository gehört das Paket zum npm-Workspace (`npm ci` im
Stamm, Bau mit `npm run build -w @auditcore/sampling-templates-vue`, Demo mit
`npm run demo -w @auditcore/sampling-templates-vue`).

## Schnellstart

```ts
import '@auditcore/ui/style.css'
import '@auditcore/sampling-templates-vue/style.css'
import { SamplingCalculator } from '@auditcore/sampling-templates-vue'
import { createApp, h } from 'vue'

createApp({
  render: () =>
    h(SamplingCalculator, {
      draftKey: 'meine-anwendung',
      onSaved: (fileName: string) => console.log('gespeichert', fileName),
    }),
}).mount('#app')
```

## Einbindung

**Vue**, als Ganzes:

```vue
<script setup lang="ts">
import { SamplingCalculator } from '@auditcore/sampling-templates-vue'
</script>

<template>
  <SamplingCalculator :local-draft="false" locale="de" @saved="onSaved" @exported="onExported" />
</template>
```

Die Komponente füllt die Breite ihres Behälters und richtet sich nach ihr
(Container-Abfragen): ab etwa 900 px Formular links und Ergebnisspalte rechts,
darunter eine Spalte mit der Ergebnisspalte oben. Sie trägt eine klebende
Kopfzeile; in einer Anwendung mit eigener Kopfzeile den Abstand über
`.fa-st__bar { top: … }` setzen.

**Bausteine** für eigene Zusammenstellungen: `MethodPicker` (Auswahl als
Filter: Methode als Reiter mit Pfeiltasten, Zeiträume und Schichtung als
Umschalter, daraus genau ein Verfahren), `MethodGlossary` (Kurzerklärungen),
`MethodBar` (nummerierte Schrittleiste), `SheetForm`/`SheetField` (Formular aus der
Methodendefinition), `ResultPanel`/`ErrorGauge`, `WorkspaceMenu`, `NoticeList`,
`VariantTile`, `StrataTable` (Schichtzeilen mit eigenem Rollbereich),
`UnitList` (Listenblatt mit Einfügen aus der Zwischenablage), `MethodGuide`
(Wegweiser), `ImportPreview` (Vorschau der ausgefüllten Vorlage),
`DataTableDialog` (Nachschlagetabelle X1a), `ReportView` (Bericht); Zustand und Dateiaktionen als Composables `useSamplingSession`,
`useFileActions`, `useLocalDraft`, `useUnloadGuard`, `useFileDrop`,
`useAnnouncer`.

Der Excel-Austausch (`@auditcore/sampling-templates-core/workbook`; der Einstieg heißt bewusst nicht „xlsx“, damit Bündelregeln für SheetJS ihn nicht erfassen) wird erst
geladen, wenn exportiert oder eine `.xlsx`-Datei geöffnet wird; der Bündler
der Anwendung legt dafür ein eigenes Teilpaket an.

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Exporte der Einstiegspunkte aus `package.json#exports` (37):

| Einstieg | Name | Art | Kurzbeschreibung (erste JSDoc-Zeile) | Modul |
|---|---|---|---|---|
| `@auditcore/sampling-templates-vue` | `CellControl` | Vue-Komponente | – | `components/CellControl.vue` |
| `@auditcore/sampling-templates-vue` | `DataTableDialog` | Vue-Komponente | – | `components/DataTableDialog.vue` |
| `@auditcore/sampling-templates-vue` | `DraftMode` | Typ | Stufe des Zwischenstands im Web Storage: `off` – nichts wird abgelegt; `session` – nur für diese Sitzung (`sessionStorage`); `device` – auf diesem Gerät behalten (`localStorage`). | `types` |
| `@auditcore/sampling-templates-vue` | `ErrorGauge` | Vue-Komponente | – | `components/ErrorGauge.vue` |
| `@auditcore/sampling-templates-vue` | `FileActionOptions` | Schnittstelle | – | `composables/useFileActions` |
| `@auditcore/sampling-templates-vue` | `FileActions` | Schnittstelle | – | `composables/useFileActions` |
| `@auditcore/sampling-templates-vue` | `FileDrop` | Schnittstelle | – | `composables/useBrowserGuards` |
| `@auditcore/sampling-templates-vue` | `ImportPreview` | Vue-Komponente | – | `components/ImportPreview.vue` |
| `@auditcore/sampling-templates-vue` | `ImportPreviewData` | Vue-Komponente | – | `components/ImportPreview.vue` |
| `@auditcore/sampling-templates-vue` | `LocalDraftOptions` | Schnittstelle | – | `composables/useLocalDraft` |
| `@auditcore/sampling-templates-vue` | `MenuAction` | Typ | Einträge des Menüs „Arbeitsstand“. | `types` |
| `@auditcore/sampling-templates-vue` | `MethodBar` | Vue-Komponente | – | `components/MethodBar.vue` |
| `@auditcore/sampling-templates-vue` | `MethodGlossary` | Vue-Komponente | – | `components/MethodGlossary.vue` |
| `@auditcore/sampling-templates-vue` | `MethodGuide` | Vue-Komponente | – | `components/MethodGuide.vue` |
| `@auditcore/sampling-templates-vue` | `MethodPicker` | Vue-Komponente | – | `components/MethodPicker.vue` |
| `@auditcore/sampling-templates-vue` | `NoticeList` | Vue-Komponente | – | `components/NoticeList.vue` |
| `@auditcore/sampling-templates-vue` | `NoticeTone` | Typ | – | `composables/useSamplingSession` |
| `@auditcore/sampling-templates-vue` | `ReportView` | Vue-Komponente | – | `components/ReportView.vue` |
| `@auditcore/sampling-templates-vue` | `ResultPanel` | Vue-Komponente | – | `components/ResultPanel.vue` |
| `@auditcore/sampling-templates-vue` | `SamplingCalculator` | Vue-Komponente | – | `SamplingCalculator.vue` |
| `@auditcore/sampling-templates-vue` | `SamplingSession` | Schnittstelle | – | `composables/useSamplingSession` |
| `@auditcore/sampling-templates-vue` | `SessionMeta` | Schnittstelle | – | `composables/useSamplingSession` |
| `@auditcore/sampling-templates-vue` | `SessionNotice` | Schnittstelle | – | `composables/useSamplingSession` |
| `@auditcore/sampling-templates-vue` | `SessionOptions` | Schnittstelle | – | `composables/useSamplingSession` |
| `@auditcore/sampling-templates-vue` | `SheetField` | Vue-Komponente | – | `components/SheetField.vue` |
| `@auditcore/sampling-templates-vue` | `SheetForm` | Vue-Komponente | – | `components/SheetForm.vue` |
| `@auditcore/sampling-templates-vue` | `StepId` | Typ | – | `composables/sessionView` |
| `@auditcore/sampling-templates-vue` | `StrataTable` | Vue-Komponente | – | `components/StrataTable.vue` |
| `@auditcore/sampling-templates-vue` | `UnitList` | Vue-Komponente | – | `components/UnitList.vue` |
| `@auditcore/sampling-templates-vue` | `VariantTile` | Vue-Komponente | – | `components/VariantTile.vue` |
| `@auditcore/sampling-templates-vue` | `WorkspaceMenu` | Vue-Komponente | – | `components/WorkspaceMenu.vue` |
| `@auditcore/sampling-templates-vue` | `useAnnouncer` | Funktion | Text für einen `aria-live`-Bereich, höchstens alle `ms` aktualisiert. | `composables/useBrowserGuards` |
| `@auditcore/sampling-templates-vue` | `useFileActions` | Funktion | – | `composables/useFileActions` |
| `@auditcore/sampling-templates-vue` | `useFileDrop` | Funktion | Ziehen und Ablegen einer Datei auf die Komponente. | `composables/useBrowserGuards` |
| `@auditcore/sampling-templates-vue` | `useLocalDraft` | Funktion | – | `composables/useLocalDraft` |
| `@auditcore/sampling-templates-vue` | `useSamplingSession` | Funktion | – | `composables/useSamplingSession` |
| `@auditcore/sampling-templates-vue` | `useUnloadGuard` | Funktion | Browser-Warnung beim Verlassen der Seite, solange `active()` gilt. | `composables/useBrowserGuards` |

### Props und Ereignisse der Vue-Komponenten

#### `CellControl`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `row` | `RowView` | ja | – | – |
| `cell` | `CellView` | ja | – | – |
| `id` | `string` | ja | – | – |
| `t` | `Translate` | ja | – | – |
| `label` | `string` | nein | – | – |
| `describedBy` | `string` | nein | – | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `update` | `[cell: CellAddress, value: CellValue]` | – |

#### `DataTableDialog`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `table` | `DataTable \| null` | ja | – | – |
| `t` | `Translate` | ja | – | – |
| `locale` | `Locale` | nein | – | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `close` | `[]` | – |

#### `ErrorGauge`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `gauge` | `GaugeView` | ja | – | – |
| `t` | `Translate` | ja | – | – |

#### `ImportPreview`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `preview` | `ImportPreviewData \| null` | ja | – | – |
| `t` | `Translate` | ja | – | – |
| `locale` | `Locale` | nein | – | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `apply` | `[]` | – |
| `cancel` | `[]` | – |

#### `ImportPreviewData`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `preview` | `ImportPreviewData \| null` | ja | – | – |
| `t` | `Translate` | ja | – | – |
| `locale` | `Locale` | nein | – | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `apply` | `[]` | – |
| `cancel` | `[]` | – |

#### `MethodBar`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `definition` | `MethodDefinition \| null` | ja | – | – |
| `step` | `WorkflowStep['id']` | ja | – | – |
| `sheets` | `readonly SheetModule[]` | ja | – | – |
| `t` | `Translate` | ja | – | – |
| `choosing` | `boolean` | nein | `false` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `change` | `[]` | – |
| `step` | `[id: WorkflowStep['id']]` | – |
| `table` | `[sheet: string]` | – |

#### `MethodGlossary`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `t` | `Translate` | ja | – | – |

#### `MethodGuide`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `guide` | `GuideView` | ja | – | – |
| `t` | `Translate` | ja | – | – |

#### `MethodPicker`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `families` | `readonly Family[]` | ja | – | – |
| `sheets` | `readonly SheetModule[]` | ja | – | – |
| `t` | `Translate` | ja | – | – |
| `current` | `string \| null` | nein | – | – |
| `guide` | `GuideView \| null` | nein | – | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `select` | `[sheet: string]` | – |
| `table` | `[sheet: string]` | – |

#### `NoticeList`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `notices` | `readonly SessionNotice[]` | ja | – | – |
| `sample` | `boolean` | ja | – | – |
| `t` | `Translate` | ja | – | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `dismiss` | `[id: number]` | – |
| `clear` | `[]` | – |

#### `ReportView`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `report` | `ReportPage` | ja | – | – |
| `t` | `Translate` | ja | – | – |
| `checksum` | `string` | nein | `''` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `update` | `[cell: CellAddress, value: CellValue]` | – |
| `print` | `[]` | – |

#### `ResultPanel`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `summary` | `SummaryView` | ja | – | – |
| `t` | `Translate` | ja | – | – |

#### `SamplingCalculator`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `sheets` | `readonly SheetModule[]` | nein | `() => SHEETS` | Blätter mit und ohne Rechenkern (Standard: Register des Kerns). |
| `families` | `readonly Family[]` | nein | `() => FAMILIES` | Verfahrensfamilien der Auswahl (Standard: Katalog nach Blatt 00). |
| `locale` | `Locale` | nein | `undefined` | – |
| `messages` | `{ de?: Partial<Record<MessageKey, string>>; en?: Partial<Record<MessageKey, string>> }` | nein | `undefined` | Überschriebene bzw. englische Texte der Oberfläche. |
| `draft` | `DraftMode` | nein | `'off'` | Zwischenstand im Web Storage dieses Browsers: `off` (Vorgabe), `session` (nur diese Sitzung) oder `device` (auf diesem Gerät behalten). |
| `localDraft` | `boolean` | nein | `false` | Veraltet: `true` entspricht `draft="device"`. |
| `draftKey` | `string` | nein | `'entwurf'` | Schlüssel des lokalen Entwurfs; je Anwendung verschieden wählen. |
| `guardUnload` | `boolean` | nein | `true` | Browser-Warnung bei ungespeicherten Änderungen. |
| `initialState` | `WorkspaceState` | nein | `undefined` | – |
| `filePrefix` | `string` | nein | `undefined` | Vorsatz der Dateinamen von Arbeitsstand und Export (Standard: „Stichprobe“). |
| `dataMark` | `string` | nein | `undefined` | Datenmarke der Anwendung als Text neben dem Titel; mehr Gestaltung über den Slot `mark`. |
| `saveFile` | `(file: DownloadFile) => void \| Promise<void>` | nein | `undefined` | Eigene Übergabe von Dateien an den Browser (Standard: Download über Blob). |
| `workspaceMenu` | `boolean` | nein | `true` | Menü „Arbeitsstand“ im Rechner; `false` bei eigenem Menü der Anwendung (`runAction()`, `openFile()`). |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `change` | `[state: WorkspaceState]` | – |
| `saved` | `[fileName: string]` | – |
| `opened` | `[fileName: string]` | – |
| `exported` | `[fileName: string]` | – |
| `draft` | `[status: { mode: DraftMode; stored: boolean }]` | – |
| `dirty` | `[dirty: boolean]` | – |

#### `SheetField`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `row` | `RowView` | ja | – | – |
| `t` | `Translate` | ja | – | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `update` | `[cell: CellAddress, value: CellValue]` | – |

#### `SheetForm`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `sections` | `readonly SectionView[]` | ja | – | – |
| `t` | `Translate` | ja | – | – |
| `strata` | `number` | nein | `0` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `update` | `[cell: CellAddress, value: CellValue]` | – |
| `addStratum` | `[]` | – |
| `removeStratum` | `[]` | – |

#### `StrataTable`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `rows` | `readonly RowView[]` | ja | – | – |
| `count` | `number` | ja | – | – |
| `t` | `Translate` | ja | – | – |
| `controls` | `boolean` | nein | `true` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `update` | `[cell: CellAddress, value: CellValue]` | – |
| `add` | `[]` | – |
| `remove` | `[]` | – |

#### `UnitList`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `view` | `ListView` | ja | – | – |
| `selected` | `number` | ja | – | – |
| `methodNumber` | `string` | ja | – | – |
| `pasteColumns` | `string` | ja | – | – |
| `t` | `Translate` | ja | – | – |
| `locale` | `Locale` | nein | – | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `select` | `[index: number]` | – |
| `add` | `[]` | – |
| `remove` | `[index: number]` | – |
| `paste` | `[text: string]` | – |
| `transfer` | `[]` | – |

#### `VariantTile`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `variant` | `Variant` | ja | – | – |
| `available` | `boolean` | ja | – | – |
| `t` | `Translate` | ja | – | – |
| `table` | `boolean` | nein | `false` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `select` | `[sheet: string]` | – |
| `table` | `[sheet: string]` | – |

#### `WorkspaceMenu`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `t` | `Translate` | ja | – | – |
| `draft` | `boolean` | ja | – | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `action` | `[action: MenuAction]` | – |
<!-- api-overview:end -->

## Konfiguration

| Prop | Standard | Bedeutung |
|---|---|---|
| `draft` | `'off'` | Zwischenstand im Web Storage dieses Browsers: `'off'` (nichts wird abgelegt, der Menüpunkt entfällt), `'session'` (nur diese Sitzung, `sessionStorage`) oder `'device'` (auf diesem Gerät behalten, `localStorage`). Beim Wechsel der Stufe zieht der Zwischenstand um, bei `'off'` und bei „Neu“ werden beide Ablagen geleert. Ein übergebener `initialState` geht dem Zwischenstand vor. Die frühere Prop `localDraft` entspricht `draft="device"` |
| Slot `draft`, Ereignis `draft` | – | Den Umschalter „auf diesem Gerät behalten“ bietet die Anwendung an: Der Slot (in der Fußzeile, Props `mode`, `stored`, `clear`) nimmt ihn auf, das Ereignis meldet `{ mode, stored }`, sobald ein Zwischenstand abgelegt oder entfernt ist |
| `draftKey` | `entwurf` | Schlüssel des Entwurfs (`auditcore-sampling-templates:<draftKey>`), je Anwendung verschieden wählen |
| `guardUnload` | `true` | Browser-Warnung beim Verlassen mit ungespeicherten Änderungen |
| `locale`, `messages` | Deutsch | Sprache (`de`, `en`) und überschriebene Texte (`{ de: {…}, en: {…} }`, Schlüssel `MessageKey` des Kerns); ohne `locale` gilt die von `@auditcore/ui` bereitgestellte Sprache |
| `filePrefix` | `Stichprobe` | Vorsatz der Dateinamen: `<Vorsatz>_<Blatt>_<Geschäftsjahr>_Arbeitsstand.json` bzw. `_Ergebnis.xlsx` |
| `dataMark`, Slot `mark` | – | Datenmarke der Anwendung in der Kopfzeile: als Text oder als eigener Baustein im Slot |
| `saveFile` | Download über Blob | eigene Übergabe von Dateien an den Browser |
| `sheets`, `families` | Register und Katalog des Kerns | andere Blattauswahl |
| `initialState` | leer | Arbeitsstand beim Start |

Englisch ist eine gekennzeichnete Arbeitsübersetzung: Texte der Oberfläche
und Bezeichnungen, Fundstellen und Prüfhinweise aller Blätter, Fachbegriffe
nach der englischen Fassung der DelVO (EU) 2023/67; maßgeblich ist der deutsche
Wortlaut der Vorlage. Gespeicherte Werte
bleiben deutsch.

**Methoden der Komponente** (über `ref`): `loadSample(blatt?)` lädt die
Beispielwerte – mit Blattname (z. B. `'03_MUS_1Z'`) öffnet es dieses Verfahren,
ohne Angabe bleiben gewähltes Verfahren und Arbeitsschritt stehen; `reset()`
leert das Formular und den Zwischenstand; `open(file)`, `save()`,
`exportResult()`, `clearDraft()`; `state` ist der Arbeitsstand; `isDirty()`
und der reaktive Wert `dirty` sagen, ob es ungesicherte Änderungen gibt.
Für ein eigenes Menü der Anwendung (`workspace-menu="false"`): `runAction(aktion)`
mit `'save' | 'open' | 'new' | 'sample' | 'clearDraft'` und `openFile(datei)` –
beide mit derselben Rückfrage bei ungesicherten Änderungen wie das eingebaute Menü.

In schmalen Behältern (unter 56rem) klebt über dem Formular eine kompakte
Kennzahlenleiste (Hauptgröße, hervorgehobene Kennzahlen, Ampel). Ihren Abstand
nach oben setzt die Anwendung über `--fa-st-sticky-top` (Standard `0`).

**Routenwächter der Anwendung:** Die Komponente warnt selbst nur beim
Schließen oder Neuladen der Seite (`beforeunload`). Verlässt die Nutzerin den
Rechner über die Navigation der Anwendung, fragt die Anwendung nach – mit dem
Ereignis `dirty` oder der Methode `isDirty()`:

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { SamplingCalculator } from '@auditcore/sampling-templates-vue'

const dirty = ref(false)
onBeforeRouteLeave(() => !dirty.value || window.confirm('Der Arbeitsstand enthält ungespeicherte Änderungen. Seite trotzdem verlassen?'))
</script>

<template>
  <SamplingCalculator @dirty="dirty = $event" />
</template>
```

```vue
<SamplingCalculator ref="calculator" :draft="keep ? 'device' : 'session'">
  <template #draft="{ stored }">
    <label><input v-model="keep" type="checkbox" /> auf diesem Gerät behalten</label>
    <span v-if="stored">Zwischenstand abgelegt</span>
  </template>
</SamplingCalculator>
```

**Bericht:** Kopf- und Fußzeile nennen das Programm und die Prüfbehörde, die
im Schritt „Bericht“ bei den Steuerfeldern angegeben sind; das Paket enthält
keinen festen Namen. Die Druckseite ist als benannte Seite (`@page
fa-st-report`) gesetzt und ändert den Druck anderer Seiten der Anwendung nicht.

In der Fußzeile stehen immer der Hinweis des Fachrahmens und der Stand der
Vorlage (Arbeitsentwurf, Fassung 4, Stand Oktober 2026, keine amtliche
Fassung); beide stehen auch im Kopf des Excel-Exports.

### Theming

Die Stile lesen ausschließlich die FlowAudit-Designtoken `--fa-*` aus
`@auditcore/ui-core` (Hell als Standard, Dunkel über `data-fa-theme="dark"`
oder `prefers-color-scheme`). Eine Anwendung mit eigenen Tokens ordnet ihre
Variablen an einem umschließenden Element zu; gelesen werden:

| Token | Verwendung |
|---|---|
| `--fa-color-bg`, `--fa-color-surface`, `--fa-color-surface-raised`, `--fa-color-surface-sunken` | Seitengrund, Karten und Kopfzeile, Eingabefelder, abgesetzte Flächen |
| `--fa-color-text`, `--fa-color-text-muted` | Text, Nebentext |
| `--fa-color-border`, `--fa-color-border-strong` | Linien |
| `--fa-color-accent`, `--fa-color-accent-hover`, `--fa-color-accent-contrast`, `--fa-color-accent-soft` | Bedienelemente und gewählter Zustand |
| `--fa-color-success`, `--fa-color-warning`, `--fa-color-danger` je mit `-soft` | nur Prüfhinweise und Meldungen |
| `--fa-color-overlay`, `--fa-shadow-sm`, `--fa-shadow-lg`, `--fa-focus-ring` | Dialog, Menü, Fokusring |
| `--fa-font-sans`, `--fa-font-mono`, `--fa-font-size-xs/sm/md/lg`, `--fa-line-height` | Schrift (Zahlen in `--fa-font-mono`) |
| `--fa-space-1` … `--fa-space-5`, `--fa-radius-sm`, `--fa-radius`, `--fa-radius-lg`, `--fa-transition` | Abstände, Rundungen, Übergänge |

`FaDialog` verlegt seinen Inhalt nach `<body>`. Eine Zuordnung an einem
umschließenden Element erreicht den Dialog deshalb nicht; steht die Anwendung
allein in ihrem Dokument, gehört der Block auf `:root`. Beispiel für
ECOHESION (Tokens `--eco-*`); weil nur auf die Tokens der Anwendung verwiesen
wird, folgen Hell und Dunkel deren Werten:

```css
:root {
  --fa-color-bg: var(--eco-bg);
  --fa-color-surface: var(--eco-surface);
  --fa-color-surface-raised: var(--eco-bg-elevated);
  --fa-color-surface-sunken: var(--eco-bg-sunken);
  --fa-color-text: var(--eco-text);
  --fa-color-text-muted: var(--eco-text-muted);
  --fa-color-border: var(--eco-border);
  --fa-color-border-strong: var(--eco-border-strong);
  --fa-color-accent: var(--eco-accent);
  --fa-color-accent-hover: var(--eco-accent-hover);
  --fa-color-accent-contrast: var(--eco-text-inverse);
  --fa-color-accent-soft: var(--eco-accent-soft);
  --fa-color-success: var(--eco-status-ok-text);
  --fa-color-success-soft: color-mix(in srgb, var(--eco-status-ok-text) 12%, var(--eco-surface));
  --fa-color-warning: var(--eco-status-warn-text);
  --fa-color-warning-soft: color-mix(in srgb, var(--eco-status-warn-text) 12%, var(--eco-surface));
  --fa-color-danger: var(--eco-status-bad-text);
  --fa-color-danger-soft: color-mix(in srgb, var(--eco-status-bad-text) 12%, var(--eco-surface));
  --fa-focus-ring: 0 0 0 3px color-mix(in srgb, var(--eco-focus) 45%, transparent);
  --fa-font-sans: var(--eco-font);
  --fa-font-mono: var(--eco-font-mono);
  --fa-font-size-xs: var(--eco-text-xs);
  --fa-font-size-sm: var(--eco-text-sm);
  --fa-font-size-md: var(--eco-text-base);
  --fa-font-size-lg: var(--eco-text-lg);
}
```

Nicht zugeordnete Token behalten die FlowAudit-Werte. Nach jeder Zuordnung den
Kontrast prüfen: Der Browsertest nimmt mit `SAMPLING_APP_TOKENS` und
`SAMPLING_APP_BRIDGE` die Token- und die Zuordnungsdatei einer Anwendung und
prüft Hell und Dunkel mit axe-core; die Demo zeigt ein Beispiel unter
`?tokens=app`.

## Herkunft und Charakterisierung

Neu geschrieben. Aufbau des Rechenblatts (Formular links, mitlaufende
Ergebnisspalte, Prüfhinweise als Marken) nach dem Gestaltungsprototyp des
Ausgangsmaterials; dessen Drehtrommel und Farbsystem wurden nicht übernommen.
Geprüft mit 69 Komponententests und 31 Browsertests (Chromium, gebaute Demo mit
`Content-Security-Policy: default-src 'self'`): jedes Verfahren wählbar und
mit Beispielwerten gerechnet, Rundlauf Speichern → Neu → Öffnen, Excel-Export
→ Öffnen, Prüfsummenhinweis, Kontextfluss aus Blatt 02, Schichttabelle (auch
der Altvorlage X3), Unterstichproben mit Übernahme je Schicht,
Gesamtfehlerquote, Bericht mit Druckansicht (PDF mit Seitenzahl: leeres
Formular und Beispielwerte je eine A4-Seite, im mitgelieferten Chromium und im
installierten Google Chrome; lange Freitexte auf Folgeseiten), Bericht und
Menü bei 390 px, Datentabelle
X1a, Vorschau der ausgefüllten Vorlage, fehlende Angaben, keine Anfrage an
fremde Hosts, Tokens einer Anwendung; je Blattart hell und dunkel, 1280 px und
390 px ohne waagerechtes Scrollen, axe-core (WCAG 2.1 A/AA) ohne Verstöße.

## Abhängigkeiten

`@auditcore/sampling-templates-core@0.1.12` (Rechenkerne, Arbeitsstand, Stile),
`@auditcore/ui` ab 0.4.0 (`FaButton`, `FaBadge`, `FaDialog`, Sprache),
`@auditcore/ui-core` ab 0.3.0 (Designtoken, Basisstile), `@auditcore/common@0.1.1`
(Download, Web Storage, Zeitsteuerung); Peer `vue@^3.5.0`. Verwendet werden nur
Bausteine, die zwischen `@auditcore/ui` 0.4.0 und 0.5.0 bzw. `ui-core` 0.3.0
und 0.4.0 unverändert sind; deshalb sind beide Fassungen zugelassen.

## Sicherheit und Datenschutz

Keine Netzwerkzugriffe (`fetch`, CDN, Telemetrie) – der Browsertest prüft es.
Alle Ausgaben laufen über Vue-Templates (maskiert, kein `v-html`); die Demo
läuft unter `default-src 'self'`. Dateien werden vom Kern streng geprüft,
bevor sie übernommen werden. Gespeichert wird nur, was die Nutzerin oder der
Nutzer als Datei speichert. Der Zwischenstand ist ausgeschaltet, solange die
Anwendung keine Stufe wählt (`draft`); dann hält er den Arbeitsstand für die
Sitzung oder auf dem Gerät im Web Storage dieses Browsers (über das Menü löschbar, in der Oberfläche als Bequemlichkeit
bezeichnet). Die Eingaben können Angaben
zu Programmen und Vorhaben enthalten; die Anwendung entscheidet, ob der
Entwurf auf gemeinsam genutzten Rechnern zulässig ist.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Die angezeigten Bezeichnungen, Fundstellen und Prüfhinweise
stammen aus dem Kern und sind aus dem Arbeitsentwurf einer Behörde abgeleitet;
siehe `PROVENANCE.md` des Kerns zu den offenen Punkten vor einer
Veröffentlichung.

## Änderungen

[CHANGELOG.md](CHANGELOG.md)
