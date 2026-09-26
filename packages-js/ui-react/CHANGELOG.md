# Changelog @flowaudit/ui-react

## 1.0.0 – unveröffentlicht (Veröffentlichung nach auditcore v0.4.1)

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
  (`auditcore_statistics.web`), dazu
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
- **Veraltet:** Die übrigen Hüllen (`FlowauditKanbanBoard(s)`,
  `createElementComponent`, `eventPayload`,
  `defineFlowauditElements`) stehen nur noch unter `@flowaudit/ui-react/elements`;
  `@flowaudit/ui`, `@flowaudit/kanban-core` und `vue` sind dafür optionale
  Peer-Abhängigkeiten.
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
