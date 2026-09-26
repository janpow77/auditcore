# Changelog @auditcore/common

## 0.1.1 – 2026-09-26 – Release v0.4.2

- **Breaking:** Paketname `@auditcore/common` statt `@flowaudit/common` (npm-Scope einheitlich mit den Python-Paketen `auditcore_*`). Imports, `package.json`-Einträge und Tarball-Namen (`auditcore-common-<version>.tgz`) anpassen; siehe `docs/ui/umbenennung-auditcore.md`. Web-Component-Tags und CSS-Präfixe unverändert.

Keine Verhaltensänderung. Build mit Vite 8 und vite-plugin-dts 5 (#169); README: Installation als Tarball aus dem GitHub-Release (#157). Der Stand 0.1.0 wurde vor dem Release als Tarball in Anwendungen eingebunden; 0.1.1 ist der erste als Release-Datei veröffentlichte Stand.

## 0.1.0 – 2026-09-25

Erste Fassung.

- Anzeigeformatierer `formatDate`, `formatDateTime`, `formatTime`,
  `toIsoDate`, `formatNumber`, `formatInt`, `formatPercent`, `formatEur`,
  `formatEurCompact`, `formatBytes`, `formatDuration`, `formatUptime`,
  `formatRelativeTime` mit den Festlegungen aus
  `contracts/common-cases/decisions.json` (Ersatzwert „—“, Europe/Berlin,
  reine Datumswerte ohne Verschiebung, Beträge half-up, Basis 1024).
- Strikte Zahleneingabe `parseDecimal`, `parseDecimalString`,
  `parseDecimalResult` (Modi `strict-de`, `strict-en`, `auto`; Gründe
  `empty`, `ambiguous`, `invalid`, `negative`).
- `errorMessage`/`httpStatus` (Axios, FastAPI-`detail` inkl. 422-Liste,
  auditcore-Hülle), `TokenStore`, `escapeHtml`/`truncate`/`initials`/
  `slugify`, CSV (`toCsv`, `escapeCsvCell`, `recordsToCsv`, `parseCsv`,
  `csvBlob`), `debounce`/`throttle`/`keyedDebounce`/`poll`, Prüfziffern
  (`mod97`, `isValidIban`, `isValidLei`, `isValidLeitwegId`), `newId`,
  Toast-Warteschlange; Unterpfad `@flowaudit/common/browser` mit
  `saveFile`, `downloadBlob`, `copyText`, `safeStorage`,
  `subscribeMediaQuery`, `onClickOutside`.
- Aus `@flowaudit/ui` 0.1.0 verschoben (dort weiter exportiert): Intl-
  Formatierer (`intlFormatDate`, `intlFormatNumber`, `intlFormatPercent`,
  `localeTag`), REST-Client (`requestJson`, `requestFile`, `RestError`),
  Tabellensortierung, Tabellen-Einlesen (`parseTable`, `parseNumber` …),
  `saveFile`. Abwärtskompatible Erweiterungen: `nextSort` mit Option
  `cycle: 'bi'`; `RestError` übernimmt FastAPI-`detail`, wenn die Antwort
  keine auditcore-Hülle hat (bisher „HTTP 422“); `requestFile` liest
  `filename*=UTF-8''…` (`contentDispositionFilename`); `saveFile` gibt die
  Objekt-URL erst nach 1 s frei (bisher sofort, zu früh für manche Browser).
- Besteht alle TypeScript-Fälle der Vertragsdateien
  `contracts/common-cases/*.json` (Test liest die Dateien direkt, Lauf in
  `America/New_York`).
