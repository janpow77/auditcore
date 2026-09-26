# Changelog @auditcore/ui-react

## 1.1.0 – 2026-09-26 – Release v0.4.2

- **Breaking:** Paketname `@auditcore/ui-react` statt `@flowaudit/ui-react` (npm-Scope einheitlich mit den Python-Paketen `auditcore_*`). Imports, `package.json`-Einträge und Tarball-Namen (`auditcore-ui-react-<version>.tgz`) anpassen; siehe `docs/ui/umbenennung-auditcore.md`. Web-Component-Tags und CSS-Präfixe unverändert.

Erste Veröffentlichung als Release-Datei. Ein früher Stand 1.0.0 (#149) war vor dem Release als Tarball in regulierung eingebunden; seitdem kamen die nativen Komponenten für Risiko-Merkmale, Screening, Stichprobe, Benford, Vergleiche, Kanban, Datenbank-Kanban, Belegerkennung, Kennungen, Tabellenexport und Hochrechnung dazu. Deshalb 1.1.0. Build mit Vite 8 (#169); Abhängigkeiten `@auditcore/common` 0.1.1, `@auditcore/ui-core` 0.2.0, `@auditcore/kanban-core` 0.2.1.

## 1.0.0 – nicht als Release-Datei veröffentlicht

**Breaking:** Das Paket enthält jetzt echte React-Komponenten statt Hüllen um
Vue-Web-Components. Der Haupteinstieg braucht weder Vue noch `@flowaudit/ui`.

- `FlowauditExtrapolation` (nativ, Vertrag `auditcore_extrapolation.web`):
  Hochrechnung mit TER, Fehlerobergrenze, Export und getrennter RER; gleiche
  Props und Ereignisse wie `<flowaudit-extrapolation>` (`onEvaluationCompleted`,
  `onResidualComputed`, `onError`), 4 Paritätsfälle und 2 Interaktionsfolgen.
- Nativ in React 18 (gleiche Props-/Ereignis-Semantik, Texte, ARIA und
  REST-Verträge wie die Vue-Fassung; Logik aus `@flowaudit/ui-core`):
  `FlowauditTable`, `FlowauditSynopsis` (Vertrag `auditcore_documents.web`),
  `FlowauditVvt` und `FlowauditDsfa` (Vertrag `dataprotection_ui/1`),
  `FlowauditGeoMap` (Vertrag `auditcore_geo.web`, Leaflet),
  `FlowauditRiskFlags` mit Teilkomponenten (`auditcore_risk.web`),
  `FlowauditScreeningReview` (`screening_review/1`), `FlowauditSampling`
  (`auditcore_sampling.web`) und `FlowauditBenford`
  (`auditcore_statistics.web`), `FlowauditComparisons` (Dokumentvergleiche:
  Hochladen, Liste, Import, Löschen, eingebettete Synopse; `auditcore_documents.web`,
  `ref` mit `reload`/`open`), dazu
  `Button`, `Badge`, `Icon`, `TextField`, `Dialog` (Fokusfalle aus dem Kern), `LocaleProvider`, `useTranslation`,
  `useStoreState`.
- Ereignisse heißen wie bisher `onXxx`, erhalten aber direkt die Nutzdaten
  (kein `CustomEvent` mehr). Vue-`v-model` wird zu gesteuerten Props mit
  `onXxxChange` bzw. `defaultXxx` (`sort`, `layout`), der Slot `cell-<key>`
  zu `renderCell`, `defineExpose` der Synopse zu `ref`
  (`FlowauditSynopsisHandle`).
- Stile aus `@flowaudit/ui-core/style.css` (statt `@flowaudit/ui/style.css`).
- Entfernt: die Hüllen `FlowauditTable`, `FlowauditSynopsis`,
  `FlowauditVvt`, `FlowauditDsfa`, `FlowauditGeoMap`, `FlowauditRiskFlags`,
  `FlowauditScreeningReview`, `FlowauditSampling`, `FlowauditBenford`
  (ersetzt durch die nativen Fassungen im Haupteinstieg) und
  das Weiterreichen von `defineFlowauditElements` im Haupteinstieg.
- **Entfernt:** der Einstieg `@flowaudit/ui-react/elements` mit den letzten
  Hüllen (`FlowauditKanbanBoard(s)`, `createElementComponent`,
  `eventPayload`, `defineFlowauditElements`); `@flowaudit/ui` und `vue` sind
  keine (optionalen) Peer-Abhängigkeiten mehr. Wer Web Components braucht,
  nutzt `@flowaudit/ui/elements` direkt.
- **Datenbankansicht nativ:** `FlowauditDbKanban` mit `DbKanbanColumn`,
  `DbKanbanCard` und `useDbKanban` (Logik `createDbKanbanController` aus
  `@flowaudit/ui-core`, Gruppierung und `RecordPort` aus
  `@flowaudit/kanban-core`); `port` oder `table`, gesteuertes `groupBy`,
  Rückrufe `onRecordMove`, `onRecordAdd`, `onTableChange`, `onError`.
- **Kanban nativ:** `FlowauditKanbanBoard` und `FlowauditKanbanBoards`
  (gleiche Props, Ereignisse als `onXxx`, `renderCardExtra`, `ref` mit
  `reload()`) sowie die Bausteine `KanbanCard`, `KanbanColumn`,
  `KanbanToolbar`, `KanbanCardDetail`, `KanbanSettingsDialog`,
  `KanbanShareDialog`, `CardAppearance`, `CardChecklistEditor`,
  `CardReferences`, `CardTagsEditor`, `ColumnEditorRow`; Logik aus
  `@flowaudit/kanban-core` (jetzt Laufzeitabhängigkeit).
- `TextField` mit `autoFocus`, `className`, `style`, `inputRef`, `onBlur`;
  `Button` mit `role`, `ariaChecked`, `testId`; `Icon` mit `className`.
- React 18 und 19: Peer-Bereich `^18.3.0 || ^19.0.0`, Tests unter beiden
  Versionen (`npm test`, `npm run test:react19`).
- Paritätsnachweis: dieselben Fälle wie die Vue-Fassung
  (`ui-core/test/parity`), zusätzlich DOM-Vergleich Vue ↔ React nach
  Normalisierung und nach Interaktionen (`test/parity`).

## 0.2.0 – 2026-09-25

- React-Hooks auf Basis von `@flowaudit/common`: `useToast` mit
  `ToastProvider` und `sharedToastQueue`, `useMediaQuery`,
  `useClickOutside`, `useSort`, `useDebouncedCallback`, `useAuthToken`.
- Weiterreichung der framework-freien Teile, die bisher nur in
  `@flowaudit/ui` lagen, unter denselben Namen (`formatDate`,
  `formatNumber`, `formatPercent`, `localeTag`, `requestJson`,
  `requestFile`, `RestError`, `saveFile`, `sortRows`, `nextSort`,
  `parseTable`, `parseNumber` …).
- Neue Peer-Abhängigkeit `@flowaudit/common` ^0.1.0; `@flowaudit/ui` ^0.2.0.

## 0.1.0 – 2026-09-25

Erste Fassung.

- Gerüst (PR #80): `createElementComponent` (Objekte als Eigenschaften,
  Ereignisse als `onXxx`), `eventPayload`, Hülle `FlowauditTable`,
  Weiterreichung von `defineFlowauditElements`.
- Kanban (PR #84): `FlowauditKanbanBoard` und `FlowauditKanbanBoards`.
- Geo-Karte: `FlowauditGeoMap` (`<flowaudit-geo-map>`).
