# Changelog @flowaudit/ui

## 0.3.0 – unveröffentlicht

- **Hochrechnung und Fehlerquoten:** `ExtrapolationPanel`
  (`<flowaudit-extrapolation>`) für `auditcore_extrapolation.web`: Methode,
  Konfidenzniveau und Faktorprofil wählen, Schichten und geprüfte Einheiten mit
  zufälligen, systemischen und anomalen Fehlern erfassen, Gesamtfehlerquote
  (TER) mit Präzision, Fehlerobergrenze, Ergebnis nach KOM-Leitfaden,
  Erläuterung und Herleitung, CSV/JSON-Export; getrennt davon die
  Restfehlerquote (RER) nach der Vorlage CPRE_23-0013-01 Annex 3. Logik im
  Kern (`createExtrapolationController`), Paritätsfälle für React, Demo-Seite
  „Hochrechnung (TER/RER)“ und Browserprüfung `extrapolation.api-e2e.ts`.
- **Dokumentvergleiche:** `FaComparisons` (`<flowaudit-comparisons>`) mit
  `ComparisonForm` und `ComparisonList` verwaltet Vergleiche über
  `auditcore_documents.web`: Hochladen zweier Fassungen (DOCX, DOCM, PDF) mit
  Vergleichsart, Dokumentart, Schwelle, Einbeziehen, Ausgabeabschnitten und
  Profil, Prüfung vor dem Hochladen, Suche, Öffnen mit eingebetteter Synopse,
  Löschen mit Bestätigung und Import fertiger Ergebnisse (JSON). Logik im
  Kern (`createComparisonsController`), Paritätsfälle für die React-Fassung.
- **Kern ausgelagert:** Texte, Datentypen der REST-Verträge, View-Modelle,
  Zustandsautomaten (Synopse, VVT, DSFA), Ports, Exporte, Symbole und die
  Stile von Basis, Tabelle, Synopse, Datenschutz und Geo-Karte liegen jetzt in
  `@flowaudit/ui-core` (neue Laufzeitabhängigkeit). Die Vue-Komponenten
  binden die Controller über `useStore` an; dieselbe Logik nutzt die native
  React-Fassung `@flowaudit/ui-react` 1.0.0. Öffentliche Namen der
  Kernfunktionen werden unverändert weitergereicht; `ui.css` enthält die
  Kernstile weiterhin.
- **Risiko-Merkmale, Screening, Stichprobe, Benford, Datei-Import:** Kern
  (Verträge, Ports, View-Logik, Zustandsautomaten, Stile) ebenfalls in
  `@flowaudit/ui-core`; `RiskFlags`, `ScreeningReview`, `SamplingPanel`,
  `BenfordPanel` und `TableImport` sind in Props, Ereignissen und Markup
  unverändert und haben jetzt native Gegenstücke in `@flowaudit/ui-react`.
  Die Stildatei `screening.css` liegt jetzt in `@flowaudit/ui-core/styles`.
- **Breaking (Composables, Risiko bis Datei-Import):** `useSampling`,
  `useBenford` und `useTableImport` liefern `{ controller, state, … }` statt
  einzelner Refs; `useScreeningReview` hat statt beschreibbarer `filter`/
  `selectedHitId` die Aktionen `setFilter` und `select`; `useRiskFlags`
  liefert `filter` als beschreibbares `computed` und `selectedIndex` nur
  lesbar (Auswahl über `select`), zusätzlich `controller`.
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
