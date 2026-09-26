# Changelog @flowaudit/ui

## 0.3.0 – unveröffentlicht

- **Kern ausgelagert:** Texte, Datentypen der REST-Verträge, View-Modelle,
  Zustandsautomaten (Synopse, VVT, DSFA), Ports, Exporte, Symbole und die
  Stile von Basis, Tabelle, Synopse, Datenschutz und Geo-Karte liegen jetzt in
  `@flowaudit/ui-core` (neue Laufzeitabhängigkeit). Die Vue-Komponenten
  binden die Controller über `useStore` an; dieselbe Logik nutzt die native
  React-Fassung `@flowaudit/ui-react` 1.0.0. Öffentliche Namen der
  Kernfunktionen werden unverändert weitergereicht; `ui.css` enthält die
  Kernstile weiterhin.
- **Breaking (Composables):** `useSynopsis`, `useSynopsisNavigation`,
  `useSynopsisExport`, `useVvt` und `useDsfa` liefern jetzt Controller und
  Zustand des Kerns (`controller`, `state`, `view`/`selection`/`derived`)
  statt einzelner Refs; `useVvt`/`useDsfa` erwarten zusätzlich die
  Übersetzungsfunktion. Die Komponenten selbst (Props, Ereignisse, Markup)
  sind unverändert. `useGeoAreas` und `useGeoReference` entfallen; `useGeoMap`
  behält seine Felder (schreibbare berechnete Referenzen auf den Kern-Controller
  `createGeoController`). `focusableWithin`/`wrapTarget` kommen aus dem Kern.
- Synopse: Die unsichtbaren Vorlesetexte „gestrichen:“/„eingefügt:“ und
  „Ende“ sind jetzt durch Leerzeichen vom markierten Text getrennt (vorher
  hat der Vorlagencompiler das Leerzeichen entfernt).
- Kanban: Zustand, Aktionen, Verschieben (Tastatur und Zeiger),
  Boardliste, Spalteneditor und Personensuche kommen aus
  `@flowaudit/kanban-core` 0.2.0; Texte und `kanban.css` aus
  `@flowaudit/ui-core`. Die Composables (`useKanbanBoard`,
  `useKanbanActions`, `useKanbanFilter`, `useMoveController`, …) behalten
  ihre Rückgabe (Refs), `usePointerDrag().drag` ist jetzt eine Ref. Props,
  Ereignisse und Markup der Komponenten sind unverändert; Paritätsfälle in
  `kanban-core/test/parity` (Vue ↔ React).
- Gemeinsame Paritätsfälle (`ui-core/test/parity`) prüfen Synopse, Tabelle,
  VVT und DSFA gegen dieselben Erwartungen wie die React-Fassung.
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
- Geo-Karte: `FaGeoMap` (`<flowaudit-geo-map>`) mit REST-Port
  `createGeoRestPort` auf `auditcore_geo.web` (docs/ui/geo-rest.md):
  Punkte und Flächen auf Leaflet 1.9 (BSD-2-Clause, dynamisch geladen),
  Kachelquelle nur über `tiles` samt Namensnennung (kein fester
  Kachelserver), Bezugspunkt per Klick, Koordinateneingabe oder Punktliste,
  UTM-Anzeige, Umkreissuche mit ausdrücklichem Erdmodell und
  Entfernungsliste, Punkt in Fläche mit Randregel (D2), Randtoleranz und
  Randfall-Anzeige, Douglas-Peucker mit Toleranzregler (Meter/Grad),
  GeoPackage per Datei-Upload oder Serverquelle, Adresssuche nur mit
  `geocoding: true` und aktivem Server-Geocoder.
