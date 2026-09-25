# Changelog @flowaudit/ui

## Unveröffentlicht

- VVT und DSFA: `FaVvt` (`<flowaudit-vvt>`) und `FaDsfa` (`<flowaudit-dsfa>`)
  mit REST-Port `createDataProtectionRestPort` auf `auditcore_dataprotection.web`
  (Vertrag `dataprotection_ui/1`, `docs/ui/dataprotection-rest.md`).
  Pflichtangaben nach Art. 30 DSGVO, Vollständigkeitsprüfung der Bibliothek
  beim Tippen, Entwurf/Vier-Augen-Freigabe/Versionen, Druckansicht, Markdown
  und CSV mit Formelschutz (Verträge `csv-cell`/`csv-document`);
  Schwellwertanalyse, Risikoszenarien mit Vorschau der Bibliothek,
  Entscheidung, DSB-Einholung, Freigabe, Bericht. View-Logik ohne Vue
  (`registerView`, `dsfaView`, `exporters`). Parität:
  `docs/ui/dataprotection-paritaet.md`.

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
