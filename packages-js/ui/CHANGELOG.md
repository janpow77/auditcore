# Changelog @flowaudit/ui

## Unveröffentlicht

- VVT und DSFA: `FaVvt` (`<flowaudit-vvt>`) und `FaDsfa` (`<flowaudit-dsfa>`)
  mit REST-Port `createDataProtectionRestPort` auf `auditcore_dataprotection.web`
  (Vertrag `dataprotection_ui/1`, `docs/ui/dataprotection-rest.md`).
  Pflichtangaben nach Art. 30 DSGVO, Vollständigkeitsprüfung der Bibliothek
  beim Tippen, Entwurf/Vier-Augen-Freigabe/Versionen, Druckansicht, Markdown
  und CSV mit Formelschutz (`csvDocument` aus `@flowaudit/common`);
  Schwellwertanalyse, Risikoszenarien mit Vorschau der Bibliothek,
  Entscheidung, DSB-Einholung, Freigabe, Bericht. View-Logik ohne Vue
  (`registerView`, `dsfaView`, `exporters`). Parität:
  `docs/ui/dataprotection-paritaet.md`.

## 0.2.0 – 2026-09-25

- Framework-freie Module nach `@flowaudit/common` 0.1.0 verschoben und unter
  denselben Namen weitergereicht (keine Breaking Changes): `formatDate`,
  `formatNumber`, `formatPercent`, `localeTag`, `requestJson`,
  `requestFile`, `RestError`, `saveFile`, `compareValues`, `sortRows`,
  `nextSort`, `ariaSort`, `parseTable`, `parseNumber`, `detectDecimal` u. a.
  Neue Laufzeitabhängigkeit `@flowaudit/common`.
- Mitgenommene Verbesserungen aus `@flowaudit/common`: `RestError` zeigt
  FastAPI-`detail` (auch 422-Listen) statt „HTTP 422“, wenn die Antwort keine
  auditcore-Hülle hat; `requestFile` liest `filename*=UTF-8''…`; `saveFile`
  gibt die Objekt-URL erst nach 1 s frei; `nextSort` kennt `cycle: 'bi'`.
- Neue Composables auf Basis von `@flowaudit/common`: `useToast`
  (`sharedToastQueue`), `useMediaQuery`, `useClickOutside`, `useSort`,
  `useDebouncedFn`, `useDebouncedRef`, `useThrottledFn`, `useAuthToken`.

## 0.1.0 – 2026-09-25

Erste Fassung.

- Gerüst (PR #80): Vue-3-Bibliothek mit Web-Component-Einstieg
  `@flowaudit/ui/elements` (Namen `flowaudit-<name>`, Light DOM),
  Designtoken `--fa-*` mit Hell-/Dunkelmodus, i18n (Deutsch vollständig,
  Englisch vorbereitet, Formatierer), Basiskomponenten `FaButton`, `FaIcon`,
  `FaDialog`, `FaTable` (`<flowaudit-table>`), `FaBadge`, `FaTextField`,
  REST-Hilfen `requestJson`, `requestFile`, `createRunner`, `saveFile`,
  Demo-App mit Playwright-Prüfung.
- Kanban (PR #84): `KanbanBoard`, `KanbanBoardList`, Karten, Spalten,
  Detailansicht, Einstellungen, Teilen; Web Components
  `<flowaudit-kanban-board>` und `<flowaudit-kanban-boards>`; Ziehen per
  Pointer Events, Tastaturbedienung mit Ansagen, optimistische Änderungen mit
  Rücknahme.
