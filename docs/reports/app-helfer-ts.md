# Hilfsfunktionen der App-Frontends (TypeScript/JavaScript) – Inventur und Zuschnitt

Stand: 25.09.2026 · Gegenstück zur Python-Inventur (`app-helfer-python.*`) · Maschinenlesbar: [`app-helfer-ts.json`](app-helfer-ts.json)

## Kurzfassung

- **18 970 Funktionen in 2 634 Dateien** aus 12 App-Frontends (6 × Vue, 6 × React) wurden per TypeScript-Compiler-API extrahiert, typbereinigt normalisiert und über Rumpf-Hashes sowie 29 Hilfskategorien gruppiert. `e-invoice-preparer` ist dasselbe Repository wie `rechnung` (gleiches Remote, gleicher Commit) und wurde nur einmal gezählt.
- **Formatierung ist der größte generische Block:** 140 Datums-, 64 Betrags-, 48 Zahl-/Prozent-, 45 Dateigrößen- und 31 Dauer-Formatierer, fast alle als lokale Einzeiler in Komponenten. Allein `audit_designer` hat 92 Datumsformatierer und 37 Dateigrößen-Funktionen.
- **Fachlich riskant ist die Zahleneingabe:** `1.234,56` wird in `BeleglisteGrid.parseDecimal` (flowinvoice, audit-portal) zu `1.234`, also um den Faktor 1000 zu klein. `1.5` ergibt je nach App `1.5` oder `15`. Die Python-Seite ist genauso uneinheitlich (Ausführungsmatrix in Abschnitt 4). Das ist der wichtigste Grund für gemeinsame Testfälle von Frontend und Backend.
- **Vieles liegt in `@auditcore/ui` schon vor, aber am falschen Ort:** `formatDate/formatNumber/formatPercent`, `sortRows/nextSort`, `requestJson/requestFile/saveFile` und `tabular.parseNumber` sind framework-frei, stecken aber im Vue-Paket (`packages-js/ui`, seit #84 in `main`; `tabular.parseNumber` bisher nur in `feat/ui-sampling-benford-js`). React-Apps können sie so nicht ohne Vue nutzen. Vorschlag: diese Module nach **`@auditcore/common`** verschieben und aus `@auditcore/ui` weiter exportieren.
- **Drei fachliche Cluster statt Hilfsfunktionen:** (1) `audit-portal` ist in den Modulen fraud-report/company-report/risk-wheel/belegliste ein Fork von `flowinvoice` (576 wortgleiche Funktionen = 59 % der flowinvoice-Funktionen); (2) der FlowStat-Custom-Node-Kern (1 354 Zeilen, framework-frei) steht wortgleich in `audit_designer` und `audit-portal`; (3) `usePdfTools` mit 18 identischen PDF-Operationen in `pdf-editor` und `audit_designer`. Dazu kommt das eGPU-Monitor-Widget in drei React-Apps.

## 1. Umfang und Methode

| App | Framework | Stand | Dateien/Funktionen im Frontend |
|---|---|---|---|
| audit_designer | Vue | `origin/main 4b629dd9` | 1053 / 8509 |
| riskanalysis | Vue | `origin/main dace0f6` | 71 / 345 |
| flowsearch | Vue | `origin/master 9ac5e0d` | 15 / 60 |
| cockpit | Vue | `origin/master df203d4` | 76 / 376 |
| ai-router | Vue | `origin/main 426cd78` | 51 / 172 |
| pdf-editor | Vue | `origin/main ce34413` | 100 / 525 |
| flowinvoice | React | `origin/main 5d5d8c5` | 245 / 1767 |
| regulierung | React | `origin/main ce76e48` | 153 / 1244 |
| audit-portal | React | `origin/main 72cc4b1` | 500 / 4396 |
| qaaudit | React | `origin/main c78be5c` | 47 / 138 |
| versteigerung | React (Next.js) | `origin/main 729f9a1` | 36 / 142 |
| rechnung | React | `origin/main b3d6445` | 15 / 73 |

Vergleichsbasis in auditcore: `packages-js/bpmn-editor`, `packages-js/ui`, `ui-react` und `kanban-core` (origin/main, seit #84 `ccb73cb`; bei der Analyse aus den Branches `feat/ui-base`, `feat/ui-risk-js`, `feat/ui-sampling-benford-js`, `feat/ui-screening-js` und dem Worktree `kanban-ui` gelesen, inhaltlich gleich für die hier genutzten Module) sowie die Fachmodule risk/sampling/screening aus ihren Branches.

**Vorgehen**

1. *Extraktion:* TypeScript-Compiler-API über alle `.ts/.tsx/.js/.jsx/.mjs` und die `<script>`-Blöcke der `.vue`-Dateien des Standardzweigs (`git archive`, keine `-wt`-Worktrees); Tests, Demos, `dist`, `.d.ts` ausgenommen. Erfasst werden Funktionsdeklarationen, Pfeil- und Funktionsausdrücke sowie Methoden.
2. *Normalisierung:* Typen per `transpileModule` entfernt, Token-Strom mit alpha-umbenannten Bezeichnern (Eigenschaftsnamen und Browser-Globals bleiben), Stringliterale neutralisiert, SHA-1 über den Strom. Zwei Funktionen mit gleichem Hash sind bis auf Namen, Typen und Texte identisch.
3. *Gruppierung:* (a) Rumpf-Hash-Gleichheit über Apps (≥ 30 Token), (b) Namens- und Rumpfmuster je Hilfskategorie, (c) Merkmalsextraktion je Variante (Locale, Ersatzwert, Nachkommastellen, Zeitzone …), (d) für die Zahleneingabe **tatsächliche Ausführung** aller Varianten auf denselben Eingaben.
4. *Aufrufer:* graphify-Graphen (`<repo>/graphify-out/graph.json`, Stand 25.09.) direkt gelesen, weil der graphify-MCP-Server nicht erreichbar war. `Graph` = eingehende `calls/references/uses`-Kanten. graphify erkennt nur rund 45 % der Hilfsfunktionen (1 688 von 3 763) und keine Aufrufe aus Vue-Templates. Deshalb gibt es zusätzlich `Text` = Vorkommen des Bezeichners im Repo außerhalb der Definition. Das ist eine obere Schranke und bei generischen Namen wie `datum` oder `error` deutlich überhöht.

**Klassen:** (a) existiert in auditcore-JS → nutzen · (b) generisches Duplikat in ≥ 2 Apps → `@auditcore/common` (+ Composable/Hook) · (c) fachlicher Cluster → eigene Bibliothek · (d) app-spezifisch → bleibt.

## 2. Top-20-Gruppen

| Rang | Gruppe | Klasse | Apps | Def. | Var. | Aufrufer Graph / Text | Ziel |
|---:|---|---|---:|---:|---:|---:|---|
| 1 | **G01** Datum/Uhrzeit formatieren (de-DE) | (b) @auditcore/common | 9 | 140 | 98 | 63 / 14795 | @auditcore/common: format/date (formatDate, formatDateTime, formatTime, parseIsoDate) |
| 2 | **X2** Betrugs-/Firmenbericht-Export (Word/PDF/Text/HTML, Abschnitts-Builder, Kennzahlen) | (c) neue Bibliothek | 2 | 576 | – | – | kein Helferpaket: audit-portal ist in diesen Modulen ein Fork von flowinvoice (576 wortgleiche Funktionen = 59 % von flowinvoice). Entscheidung nötig: gemeinsames Paket @auditcore/fraud-report (React) oder eine App als Quelle |
| 3 | **G02** Währungsbetrag formatieren (EUR) | (b) @auditcore/common | 8 | 64 | 40 | 64 / 1975 | @auditcore/common: format/money (formatEur, formatEurCompact) |
| 4 | **G10** Auth-Token/Sitzung (Speicher, Header, Login/Logout) | (b) @auditcore/common | 10 | 41 | 37 | 26 / 389 | @auditcore/common: auth/token (TokenStore-Schnittstelle mit memory/local/session-Umsetzung, bearerHeader, isExpired(jwt)) + Axios/fetch-Adapter; Login/Logout bleiben app-spezifisch |
| 5 | **G09** API-Fehlertext extrahieren | (b) @auditcore/common | 7 | 51 | 31 | 146 / 4781 | @auditcore/common: http/error (errorMessage(err, fallback) für FastAPI detail als String und als 422-Liste, {error:{code,message}}, Error, unknown) |
| 6 | **G03** Zahl/Prozent formatieren | (b) @auditcore/common | 7 | 48 | 36 | 137 / 3419 | @auditcore/common: format/number (formatNumber, formatInt, formatFixed, formatPercent) |
| 7 | **G05** Dateigröße formatieren | (b) @auditcore/common | 7 | 45 | 24 | 8 / 1298 | @auditcore/common: format/bytes (formatBytes) |
| 8 | **G11** HTML-Escaping/Markdown-Rendering | (b) @auditcore/common | 7 | 27 | 21 | 19 / 351 | @auditcore/common: text/html (escapeHtml – 5 Zeichen); Markdown-Rendering (marked + DOMPurify) als optionales Modul |
| 9 | **G14** Tabellen-Sortierung (Umschalten/Vergleich) | (a) nutzen | 7 | 25 | 20 | 0 / 187 | @auditcore/ui table/sort.ts (nextSort, sortRows, compareValues) → Kern nach @auditcore/common/table, Vue-Composable useSort in ui, React-Hook in ui-react |
| 10 | **G06** Dauer/relative Zeit formatieren | (b) @auditcore/common | 6 | 31 | 26 | 7 / 218 | @auditcore/common: format/duration (formatDuration, formatUptime, formatRelativeTime) |
| 11 | **G15** Theme/Dark-Mode anwenden | (a) nutzen | 7 | 21 | 19 | 22 / 169 | @auditcore/ui theme.ts (applyTheme/readTheme/useTheme) für Vue; React-Pendant in @auditcore/ui-react |
| 12 | **G26** eGPU-/Systemmonitor-Widgets | (c) neue Bibliothek | 5 | 39 | 17 | 14 / 77 | eGPU-/Systemmonitor-Widget als React-Komponente in @auditcore/ui-react (oder eigenes Paket @auditcore/ops-widgets) |
| 13 | **G19** Benachrichtigung/Toast (success/error/info/warning) | (b) @auditcore/common | 6 | 25 | 10 | 11 / 7510 | Toast-Store: Vue-Composable useToast in @auditcore/ui, React-Hook in @auditcore/ui-react; gemeinsamer framework-freier Kern (Queue, Dauer, Typen) in @auditcore/common |
| 14 | **G07** Blob-/Datei-Download im Browser | (a) nutzen | 5 | 30 | 28 | 29 / 2014 | @auditcore/ui rest/download.ts saveFile → nach @auditcore/common/browser verschieben (framework-frei) und aus ui re-exportieren |
| 15 | **G08** CSV-Export/-Escaping | (b) @auditcore/common | 5 | 24 | 20 | 1 / 118 | @auditcore/common: export/csv (toCsv, escapeCsvCell, csvBlob mit BOM) |
| 16 | **X1** FlowStat-Custom-Node-Kern (Parameterschema, Validierung, Export/Import, REST-Client, CodeMirror-Setup, Graphanalyse) | (c) neue Bibliothek | 2 | 49 | – | – | neue Bibliothek @auditcore/flowstat-customnode (framework-frei; Vue-Oberfläche bleibt in audit_designer, React in audit-portal) |
| 17 | **G04** Deutsche Zahleneingabe parsen | (b) @auditcore/common | 4 | 17 | 13 | 8 / 148 | @auditcore/common: parse/number (parseDecimalDe, parseAmountInput → Decimal-String) |
| 18 | **G13** Zwischenablage kopieren | (b) @auditcore/common | 4 | 14 | 12 | 2 / 211 | @auditcore/common/browser: copyText (Clipboard-API mit textarea-Rückfall) |
| 19 | **G16** DOM-Hooks: Klick außerhalb, Media-Query, Tastatur | (b) @auditcore/common | 4 | 14 | 9 | 3 / 101 | @auditcore/ui (Vue: useClickOutside, useMediaQuery) und @auditcore/ui-react (Hooks); Kern (matchMedia-Abo) framework-frei |
| 20 | **G28** PDF-Operationen (Metadaten, Wasserzeichen, Seiten) | (c) neue Bibliothek | 4 | 13 | 7 | 0 / 33 | neue Bibliothek @auditcore/pdf-tools (pdf-lib-basierte Operationen + Vue-Composable) |

Im Ranking stehen Klasse (a)–(c) vor (d); danach zählen Anzahl der Apps und Definitionen. Nicht in den Top 20: G22 localStorage-Wrapper, G23 Polling/SSE, G12 Debounce, G17 Initialen, G21 Text kürzen, G29 Validatoren, G25 IDs, X3 Login-Vorlage, G20 mod 97 (b/c); G18 Status-Labels, G27 Nutzerverwaltungs-Client, G24 URL-Bau (d).

## 3. Gruppen im Einzelnen – Varianten und Unterschiede

### G01 – Datum/Uhrzeit formatieren (de-DE)

*Klasse:* (b) @auditcore/common · *Apps:* ai-router, audit-portal, audit_designer, cockpit, flowinvoice, flowsearch, rechnung, regulierung, versteigerung · *Definitionen:* 140 · *Varianten (Rumpf-Hash):* 98

*Ziel:* @auditcore/common: format/date (formatDate, formatDateTime, formatTime, parseIsoDate)

*In auditcore vorhanden:* @auditcore/ui i18n/format.ts formatDate(value, locale, withTime) – dateStyle „medium“, Ersatzwert „“, Locale de|en; liegt aber im Vue-Paket

*Unterschiede:*

- Engine: toLocaleDateString (59), toLocaleString (36), manuell/Template (34), Intl.DateTimeFormat (14), date-fns (1)
- Ausgabe: mit Optionen 2-digit „31.01.2026“ (90) gegenüber toLocaleDateString ohne Optionen „31.1.2026“ (u. a. audit_designer utils/format.ts formatDateDe)
- Reine Datumswerte „YYYY-MM-DD“: new Date(iso) liest UTC-Mitternacht → in Zeitzonen westlich von UTC ein Tag früher (nachgestellt: TZ=America/New_York ergibt 30.1.2026); nur regulierung (formatDatumDe) und versteigerung (parseDateValue) zerlegen lokal
- Keine Variante setzt timeZone (alle 144 lokal); Zeitstempel mit Z werden in Browserzeit gezeigt
- Ersatzwert bei leer/ungültig: kein (59), „-“ (29), „—“ (28), „“ (16), „N/A“ (6), „–“ (6); nur 25 von 144 prüfen Invalid Date
- Mit Sekunden (ai-router, cockpit, regulierung formatDateTime) gegenüber ohne Sekunden (audit-portal vpFormat, regulierung formatDatumZeitDe)

*Parität zur Python-Seite:* Python: auditcore_dataprotection.legacy_report.format_datetime_de, auditcore_invoicesynth.formats.format_date → gemeinsame Fälle (Datum-only, Mitternacht UTC, ungültig)

| App | Def. | Aufrufer Graph | Aufrufer Text |
|---|---:|---:|---:|
| audit_designer | 92 | 2 | 13655 |
| audit-portal | 18 | 33 | 422 |
| flowinvoice | 10 | 8 | 119 |
| regulierung | 9 | 16 | 543 |
| cockpit | 4 | 0 | 18 |
| ai-router | 2 | 0 | 11 |
| flowsearch | 2 | 0 | 10 |
| versteigerung | 2 | 4 | 16 |
| rechnung | 1 | 0 | 1 |

### X2 – Betrugs-/Firmenbericht-Export (Word/PDF/Text/HTML, Abschnitts-Builder, Kennzahlen)

*Klasse:* (c) fachliche Bibliothek · *Apps:* flowinvoice, audit-portal · *Definitionen:* 576

*Ziel:* kein Helferpaket: audit-portal ist in diesen Modulen ein Fork von flowinvoice (576 wortgleiche Funktionen = 59 % von flowinvoice). Entscheidung nötig: gemeinsames Paket @auditcore/fraud-report (React) oder eine App als Quelle

*Unterschiede:*

- fraud-report/useWordExport.ts, usePdfExport.ts, useTextExport, useHtmlExport, company-report/*, risk-wheel/*, belegliste/* doppelt; bereits erste Abweichungen (Zeilenversatz, formatCurrency-Varianten)

### G02 – Währungsbetrag formatieren (EUR)

*Klasse:* (b) @auditcore/common · *Apps:* audit-portal, audit_designer, flowinvoice, flowsearch, rechnung, regulierung, riskanalysis, versteigerung · *Definitionen:* 64 · *Varianten (Rumpf-Hash):* 40

*Ziel:* @auditcore/common: format/money (formatEur, formatEurCompact)

*In auditcore vorhanden:* @auditcore/ui formatNumber(value, locale, options) – kein EUR-Helfer

*Unterschiede:*

- Form: Intl style currency (37), Suffix „ €“ per Hand (11), Suffix „ EUR“ (5), nur Zahl ohne Symbol (12)
- Intl setzt ein geschütztes Leerzeichen (U+00A0) vor €, die Handvarianten ein normales – Textvergleiche/Tests/PDF-Umbruch unterscheiden sich
- Nachkommastellen: Standard 2 (28), fest 2/2 (12), min 2 (12), max 0 (5: riskanalysis, versteigerung), 0/0 (4: flowsearch, TED-Abschnitt)
- Kompaktformen „T€“/„Mio. €“ (flowinvoice/audit-portal KPIStrip, riskanalysis eurMio) mit toFixed → Dezimalpunkt statt Komma bzw. replace(".", ",")
- Cent-Eingaben (/100) in regulierung (3) und audit_designer FindingsView; String-Eingaben (parseFloat) in 9 Varianten
- Ersatzwert: keiner (41), „-“ (13), „–“ (8), „0,00 EUR“ (1), „—“ (1)

*Parität zur Python-Seite:* Python-Berichte (auditcore_reporting, _invoicesynth) formatieren Beträge ebenfalls deutsch → gemeinsame Tabelle Betrag→Text inkl. NBSP-Regel

| App | Def. | Aufrufer Graph | Aufrufer Text |
|---|---:|---:|---:|
| flowinvoice | 17 | 20 | 732 |
| audit-portal | 15 | 32 | 714 |
| audit_designer | 15 | 0 | 212 |
| regulierung | 8 | 8 | 39 |
| riskanalysis | 5 | 0 | 256 |
| flowsearch | 2 | 0 | 3 |
| rechnung | 1 | 1 | 6 |
| versteigerung | 1 | 3 | 13 |

### G10 – Auth-Token/Sitzung (Speicher, Header, Login/Logout)

*Klasse:* (b) @auditcore/common · *Apps:* ai-router, audit-portal, audit_designer, cockpit, flowinvoice, flowsearch, pdf-editor, qaaudit, regulierung, versteigerung · *Definitionen:* 41 · *Varianten (Rumpf-Hash):* 37

*Ziel:* @auditcore/common: auth/token (TokenStore-Schnittstelle mit memory/local/session-Umsetzung, bearerHeader, isExpired(jwt)) + Axios/fetch-Adapter; Login/Logout bleiben app-spezifisch

*In auditcore vorhanden:* @auditcore/ui RestOptions.headers/fetch injizierbar (kein Token-Speicher)

*Unterschiede:*

- Speicherschlüssel: „token“ (audit_designer 26×, flowsearch), „flowaudit_token“ (flowinvoice, audit-portal), „hpp_token“ (regulierung), „ecohesion.token“; ai-router/cockpit/pdf-editor Pinia-Store bzw. Konstante
- Cookie-Sitzung (withCredentials) in audit_designer (2 Dateien) und qaaudit statt Bearer
- 401-Behandlung in Interceptors je App unterschiedlich (Weiterleitung, Store-Reset, nichts)
- ai-router und cockpit teilen wortgleiche auth.ts/Store-Logout-Logik (7 identische Funktionen)

| App | Def. | Aufrufer Graph | Aufrufer Text |
|---|---:|---:|---:|
| ai-router | 8 | 1 | 53 |
| audit_designer | 8 | 8 | 108 |
| cockpit | 8 | 3 | 57 |
| audit-portal | 4 | 1 | 49 |
| pdf-editor | 4 | 13 | 29 |
| flowinvoice | 2 | 0 | 39 |
| flowsearch | 2 | 0 | 10 |
| qaaudit | 2 | 0 | 28 |
| versteigerung | 2 | 0 | 4 |
| regulierung | 1 | 0 | 12 |

### G09 – API-Fehlertext extrahieren

*Klasse:* (b) @auditcore/common · *Apps:* ai-router, audit-portal, audit_designer, cockpit, flowinvoice, regulierung, riskanalysis · *Definitionen:* 51 · *Varianten (Rumpf-Hash):* 31

*Ziel:* @auditcore/common: http/error (errorMessage(err, fallback) für FastAPI detail als String und als 422-Liste, {error:{code,message}}, Error, unknown)

*In auditcore vorhanden:* @auditcore/ui RestError/toError (nur Envelope {error:{…}})

*Unterschiede:*

- 37 Definitionen allein in audit_designer (extractError, extractErrorMessage, fehlertext …) mit 6+ Varianten
- FastAPI-422 (detail als Liste von {loc,msg}) wird nur in 5 von 53 Varianten ausgewertet; die übrigen reichen die Rohliste an die Oberfläche weiter oder zeigen nur den Ersatztext
- Sonderfälle nur vereinzelt: 503-Text (MyDataSourcesPanel), data.message zusätzlich zu detail
- @auditcore/ui RestError erwartet {error:{code,message}} – anderes Fehlerformat als die App-Backends (FastAPI detail)

*Parität zur Python-Seite:* Backend-Fehlerform ist Python-Seite (FastAPI HTTPException/RequestValidationError); auditcore-Router liefern {error:{code,message}} → errorMessage muss beide Formen können

| App | Def. | Aufrufer Graph | Aufrufer Text |
|---|---:|---:|---:|
| audit_designer | 37 | 43 | 3015 |
| regulierung | 6 | 39 | 1176 |
| audit-portal | 3 | 1 | 405 |
| flowinvoice | 2 | 16 | 66 |
| ai-router | 1 | 0 | 34 |
| cockpit | 1 | 47 | 84 |
| riskanalysis | 1 | 0 | 1 |

### G03 – Zahl/Prozent formatieren

*Klasse:* (b) @auditcore/common · *Apps:* ai-router, audit-portal, audit_designer, cockpit, flowinvoice, regulierung, versteigerung · *Definitionen:* 48 · *Varianten (Rumpf-Hash):* 36

*Ziel:* @auditcore/common: format/number (formatNumber, formatInt, formatFixed, formatPercent)

*In auditcore vorhanden:* @auditcore/ui formatNumber/formatPercent (Anteil 0–1)

*Unterschiede:*

- Prozent: Intl style percent mit Anteil 0–1 (audit-portal vpFormat, @auditcore/ui) gegenüber Zahl 0–100 plus „ %“ per toFixed().replace(".", ",") (ai-router, riskanalysis pct) – Faktor 100 Unterschied bei gleichem Namen formatPercent
- toFixed-Varianten ohne Tausendertrennzeichen (ai-router formatTokens/formatPercent, riskanalysis) gegenüber Intl mit Punkt-Gruppierung
- regulierung formatFixed und formatNumberDe sind wortgleich (Dublette in derselben Datei)

*Parität zur Python-Seite:* auditcore_common.text.group_thousands_de (Python) – gleiche Gruppierungsregel testen

| App | Def. | Aufrufer Graph | Aufrufer Text |
|---|---:|---:|---:|
| audit_designer | 18 | 8 | 1992 |
| audit-portal | 12 | 60 | 459 |
| flowinvoice | 12 | 41 | 393 |
| ai-router | 2 | 0 | 24 |
| regulierung | 2 | 26 | 545 |
| cockpit | 1 | 0 | 4 |
| versteigerung | 1 | 2 | 2 |

### G05 – Dateigröße formatieren

*Klasse:* (b) @auditcore/common · *Apps:* ai-router, audit-portal, audit_designer, cockpit, pdf-editor, qaaudit, regulierung · *Definitionen:* 45 · *Varianten (Rumpf-Hash):* 24

*Ziel:* @auditcore/common: format/bytes (formatBytes)

*Unterschiede:*

- Alle 45 rechnen mit 1024, beschriften aber KB/MB statt KiB/MiB
- 41 von 45 nutzen toFixed → „1.5 MB“ mit Dezimalpunkt in deutscher Oberfläche; nur audit-portal (1) nutzt Locale-Komma, ai-router ersetzt per replace
- ai-router formatBytes erwartet Megabyte statt Byte als Eingabe (gleicher Name, andere Einheit)
- Ersatzwert: „—“ (audit-portal, cockpit), „“ bei 0 (audit_designer ReferenceDocsPanel), kein Schutz (Mehrheit)

| App | Def. | Aufrufer Graph | Aufrufer Text |
|---|---:|---:|---:|
| audit_designer | 37 | 1 | 1237 |
| audit-portal | 2 | 0 | 12 |
| pdf-editor | 2 | 4 | 38 |
| ai-router | 1 | 0 | 3 |
| cockpit | 1 | 0 | 3 |
| qaaudit | 1 | 1 | 1 |
| regulierung | 1 | 2 | 4 |

### G11 – HTML-Escaping/Markdown-Rendering

*Klasse:* (b) @auditcore/common · *Apps:* audit-portal, audit_designer, cockpit, flowinvoice, rechnung, regulierung, versteigerung · *Definitionen:* 27 · *Varianten (Rumpf-Hash):* 21

*Ziel:* @auditcore/common: text/html (escapeHtml – 5 Zeichen); Markdown-Rendering (marked + DOMPurify) als optionales Modul

*Unterschiede:*

- escapeHtml mit 5 Zeichen (&<>"') gegenüber nur 3 (&<>, jupyter/ansi.ts) – letzteres unsicher in Attributen
- renderMarkdown mit DOMPurify (audit_designer) gegenüber eigenem Mini-Renderer (audit-portal help/renderMarkdown.ts)

*Parität zur Python-Seite:* auditcore_common.html_text (Python, Branch feat/auditcore-common) – gleiche Escape-Tabelle

| App | Def. | Aufrufer Graph | Aufrufer Text |
|---|---:|---:|---:|
| audit_designer | 16 | 6 | 203 |
| audit-portal | 4 | 4 | 32 |
| flowinvoice | 2 | 2 | 3 |
| regulierung | 2 | 2 | 66 |
| cockpit | 1 | 2 | 3 |
| rechnung | 1 | 2 | 34 |
| versteigerung | 1 | 1 | 10 |

### G14 – Tabellen-Sortierung (Umschalten/Vergleich)

*Klasse:* (a) vorhanden – nutzen · *Apps:* ai-router, audit-portal, audit_designer, flowinvoice, flowsearch, regulierung, riskanalysis · *Definitionen:* 25 · *Varianten (Rumpf-Hash):* 20

*Ziel:* @auditcore/ui table/sort.ts (nextSort, sortRows, compareValues) → Kern nach @auditcore/common/table, Vue-Composable useSort in ui, React-Hook in ui-react

*In auditcore vorhanden:* @auditcore/ui table/sort.ts

*Unterschiede:*

- Zyklus asc→desc (Apps) gegenüber asc→desc→unsortiert (@auditcore/ui nextSort)
- Startrichtung beim Spaltenwechsel: asc (Mehrheit) oder desc (fraud-report DocumentListSection)
- Vergleich: localeCompare ohne numeric/sensitivity in Apps, leere Werte nicht einheitlich am Ende

| App | Def. | Aufrufer Graph | Aufrufer Text |
|---|---:|---:|---:|
| audit_designer | 9 | 0 | 85 |
| audit-portal | 5 | 0 | 29 |
| regulierung | 5 | 0 | 48 |
| flowinvoice | 3 | 0 | 21 |
| ai-router | 1 | 0 | 1 |
| flowsearch | 1 | 0 | 2 |
| riskanalysis | 1 | 0 | 1 |

### G06 – Dauer/relative Zeit formatieren

*Klasse:* (b) @auditcore/common · *Apps:* ai-router, audit-portal, audit_designer, cockpit, flowinvoice, regulierung · *Definitionen:* 31 · *Varianten (Rumpf-Hash):* 26

*Ziel:* @auditcore/common: format/duration (formatDuration, formatUptime, formatRelativeTime)

*Unterschiede:*

- relativeTime: ai-router Intl.RelativeTimeFormat („vor 5 Minuten“) gegenüber cockpit Handtext („vor 5 min“, „gerade eben“)
- formatDuration: ai-router „1,50 s“ (2 Stellen, Komma) gegenüber cockpit „1.5 s“ (1 Stelle, Punkt) und „m s“ ab 60 s
- formatUptime „1d 2h 3m“ englische Kürzel (ai-router, eGPU-Widget)

| App | Def. | Aufrufer Graph | Aufrufer Text |
|---|---:|---:|---:|
| audit_designer | 17 | 0 | 155 |
| audit-portal | 4 | 2 | 11 |
| ai-router | 3 | 0 | 16 |
| cockpit | 3 | 0 | 29 |
| flowinvoice | 2 | 2 | 4 |
| regulierung | 2 | 3 | 3 |

### G15 – Theme/Dark-Mode anwenden

*Klasse:* (a) vorhanden – nutzen · *Apps:* audit-portal, audit_designer, flowinvoice, pdf-editor, regulierung, riskanalysis, versteigerung · *Definitionen:* 21 · *Varianten (Rumpf-Hash):* 19

*Ziel:* @auditcore/ui theme.ts (applyTheme/readTheme/useTheme) für Vue; React-Pendant in @auditcore/ui-react

*In auditcore vorhanden:* @auditcore/ui theme

*Unterschiede:*

- data-theme-Attribut (@auditcore/ui) gegenüber class „dark“ (audit_designer, riskanalysis) gegenüber ThemeContext mit Tokens (flowinvoice/audit-portal)

| App | Def. | Aufrufer Graph | Aufrufer Text |
|---|---:|---:|---:|
| audit_designer | 6 | 2 | 33 |
| regulierung | 4 | 2 | 54 |
| audit-portal | 3 | 5 | 25 |
| flowinvoice | 3 | 11 | 45 |
| pdf-editor | 3 | 2 | 10 |
| riskanalysis | 1 | 0 | 1 |
| versteigerung | 1 | 0 | 1 |

### G26 – eGPU-/Systemmonitor-Widgets

*Klasse:* (c) fachliche Bibliothek · *Apps:* ai-router, audit-portal, audit_designer, flowinvoice, regulierung · *Definitionen:* 39 · *Varianten (Rumpf-Hash):* 17

*Ziel:* eGPU-/Systemmonitor-Widget als React-Komponente in @auditcore/ui-react (oder eigenes Paket @auditcore/ops-widgets)

*Unterschiede:*

- EgpuPipelineWidget.tsx in flowinvoice, audit-portal, regulierung wortgleich (12–13 Funktionen je App: StatBar, VramBar, SystemPanel, useEgpuData, tempColor, formatUptime …)

| App | Def. | Aufrufer Graph | Aufrufer Text |
|---|---:|---:|---:|
| regulierung | 13 | 4 | 29 |
| audit-portal | 12 | 4 | 22 |
| flowinvoice | 12 | 6 | 22 |
| ai-router | 1 | 0 | 2 |
| audit_designer | 1 | 0 | 2 |

### G19 – Benachrichtigung/Toast (success/error/info/warning)

*Klasse:* (b) @auditcore/common · *Apps:* ai-router, audit-portal, audit_designer, cockpit, flowinvoice, pdf-editor · *Definitionen:* 25 · *Varianten (Rumpf-Hash):* 10

*Ziel:* Toast-Store: Vue-Composable useToast in @auditcore/ui, React-Hook in @auditcore/ui-react; gemeinsamer framework-freier Kern (Queue, Dauer, Typen) in @auditcore/common

*Unterschiede:*

- success/error/info/warning als Store-Fassade in 6 Apps; Fehlerdauer 6 s (ai-router/cockpit) sonst Standard; pdf-editor mit title+message

| App | Def. | Aufrufer Graph | Aufrufer Text |
|---|---:|---:|---:|
| pdf-editor | 5 | 1 | 515 |
| ai-router | 4 | 0 | 42 |
| audit-portal | 4 | 0 | 2482 |
| audit_designer | 4 | 10 | 3027 |
| cockpit | 4 | 0 | 111 |
| flowinvoice | 4 | 0 | 1333 |

### G07 – Blob-/Datei-Download im Browser

*Klasse:* (a) vorhanden – nutzen · *Apps:* audit-portal, audit_designer, flowinvoice, pdf-editor, regulierung · *Definitionen:* 30 · *Varianten (Rumpf-Hash):* 28

*Ziel:* @auditcore/ui rest/download.ts saveFile → nach @auditcore/common/browser verschieben (framework-frei) und aus ui re-exportieren

*In auditcore vorhanden:* @auditcore/ui saveFile(DownloadFile), requestFile(...) (in main seit #84)

*Unterschiede:*

- revokeObjectURL sofort nach click() (audit-portal, regulierung, audit_designer) gegenüber setTimeout 0 (@auditcore/ui) – sofortiges Freigeben kann in Safari/Firefox den Download abbrechen
- regulierung setzt automatisch Datumspräfix YYYY-MM-DD_ (mitDatumspraefix, UTC-Datum über toISOString)
- Dateiname aus Content-Disposition: nur @auditcore/ui requestFile; Apps setzen ihn fest oder parsen einzeln (filename*=UTF-8 fehlt überall)
- flowinvoice/audit-portal zusätzlich file-saver (Abhängigkeit)

| App | Def. | Aufrufer Graph | Aufrufer Text |
|---|---:|---:|---:|
| audit_designer | 21 | 7 | 1782 |
| pdf-editor | 4 | 10 | 49 |
| flowinvoice | 2 | 1 | 22 |
| regulierung | 2 | 10 | 105 |
| audit-portal | 1 | 1 | 56 |

### G08 – CSV-Export/-Escaping

*Klasse:* (b) @auditcore/common · *Apps:* audit-portal, audit_designer, flowinvoice, pdf-editor, regulierung · *Definitionen:* 24 · *Varianten (Rumpf-Hash):* 20

*Ziel:* @auditcore/common: export/csv (toCsv, escapeCsvCell, csvBlob mit BOM)

*Unterschiede:*

- Export überwiegend mit „;“ (Excel-DE), DrillDownTable (audit_designer) mit „,“; BOM \uFEFF nur in GisAttributeTable – übrige Exporte öffnen sich in Excel mit falschen Umlauten
- Neben Export auch vier eigene CSV-Parser (parseCsv, parseCsvPreview, csvToArray, parseReportCsv) ohne gemeinsame Quoting-Regeln
- Kein Schutz gegen Formel-Injektion (=, +, -, @ am Zellanfang) gefunden

*Parität zur Python-Seite:* Python-Exporte (auditcore_reporting) schreiben CSV/XLSX – gleiche Zellregeln (Trenner, BOM, Injektionsschutz) festlegen

| App | Def. | Aufrufer Graph | Aufrufer Text |
|---|---:|---:|---:|
| audit_designer | 9 | 1 | 53 |
| audit-portal | 5 | 0 | 3 |
| regulierung | 5 | 0 | 58 |
| flowinvoice | 3 | 0 | 1 |
| pdf-editor | 2 | 0 | 3 |

### X1 – FlowStat-Custom-Node-Kern (Parameterschema, Validierung, Export/Import, REST-Client, CodeMirror-Setup, Graphanalyse)

*Klasse:* (c) fachliche Bibliothek · *Apps:* audit_designer, audit-portal · *Definitionen:* 49

*Ziel:* neue Bibliothek @auditcore/flowstat-customnode (framework-frei; Vue-Oberfläche bleibt in audit_designer, React in audit-portal)

*Unterschiede:*

- customnode/core/*.ts (1354 Zeilen) liegt in beiden Apps; 49 wortgleiche Funktionen (validateParamSpec, schemaBuilder.*, createCustomNodeApi.*, computeTopologicalDepth, findStartNodes …)
- Tests nur in audit_designer (customnode/core/__tests__)

### G04 – Deutsche Zahleneingabe parsen

*Klasse:* (b) @auditcore/common · *Apps:* audit-portal, audit_designer, flowinvoice, regulierung · *Definitionen:* 17 · *Varianten (Rumpf-Hash):* 13

*Ziel:* @auditcore/common: parse/number (parseDecimalDe, parseAmountInput → Decimal-String)

*In auditcore vorhanden:* @auditcore/ui tabular/parse.ts parseNumber(cell, decimal) (Branch feat/ui-sampling-benford-js) – verhält sich mit decimal="," wie regulierung parseNumberDe

*Unterschiede:*

- Siehe Ausführungsmatrix: „1.5“ ergibt 15 (regulierung parseNumberDe/zuZahl, audit_designer parseRaw) oder 1,5 (parseGermanNumber, parseAmountInput)
- „1.234,56“ ergibt 1,234 in flowinvoice/audit-portal BeleglisteGrid.parseDecimal (ersetzt nur das Komma) – Betragsfehler um Faktor 1000
- „12 345,67 €“: nur parseGermanNumber, parseAmountInput, parseNumberDe und @auditcore/ui tabular.parseNumber entfernen Leerzeichen/Währung
- Rückgabe: number (meist), Decimal-String (audit-portal parseAmountInput, audit_designer betragFuerDienst – verlustfrei für das Backend), 0 statt null bei Fehler (parseDecimal, parseGermanNumber)
- regulierung zuZahl lehnt negative Werte ab (null für „-3,2“)

*Parität zur Python-Seite:* Python: auditcore_funding_sources.flowsearch.parse_amount (Heuristik letzter Trenner = parseGermanNumber), auditcore_documents.parse_amount, auditcore_funding_sources._parsing.to_decimal (nur Punkt), auditcore_property_sources.zvg.parse_de_number (Textsuche, „1234,56“ → 123.0). Gemeinsame Testfälle Pflicht

| App | Def. | Aufrufer Graph | Aufrufer Text |
|---|---:|---:|---:|
| audit-portal | 6 | 5 | 101 |
| audit_designer | 6 | 1 | 24 |
| regulierung | 3 | 2 | 10 |
| flowinvoice | 2 | 0 | 13 |

### G13 – Zwischenablage kopieren

*Klasse:* (b) @auditcore/common · *Apps:* audit-portal, audit_designer, cockpit, flowinvoice · *Definitionen:* 14 · *Varianten (Rumpf-Hash):* 12

*Ziel:* @auditcore/common/browser: copyText (Clipboard-API mit textarea-Rückfall)

*Unterschiede:*

- Nur JupyterFileBrowser hat den execCommand-Rückfall (HTTP ohne sicheren Kontext, Intranet!)
- Rest: await ohne try/catch oder ohne await

| App | Def. | Aufrufer Graph | Aufrufer Text |
|---|---:|---:|---:|
| audit_designer | 11 | 1 | 201 |
| audit-portal | 1 | 0 | 4 |
| cockpit | 1 | 1 | 2 |
| flowinvoice | 1 | 0 | 4 |

### G16 – DOM-Hooks: Klick außerhalb, Media-Query, Tastatur

*Klasse:* (b) @auditcore/common · *Apps:* audit-portal, audit_designer, flowinvoice, regulierung · *Definitionen:* 14 · *Varianten (Rumpf-Hash):* 9

*Ziel:* @auditcore/ui (Vue: useClickOutside, useMediaQuery) und @auditcore/ui-react (Hooks); Kern (matchMedia-Abo) framework-frei

*Unterschiede:*

- useMediaQuery wortgleich in flowinvoice, audit-portal, regulierung (eGPU-Widget)

| App | Def. | Aufrufer Graph | Aufrufer Text |
|---|---:|---:|---:|
| audit_designer | 6 | 0 | 76 |
| audit-portal | 3 | 1 | 11 |
| flowinvoice | 3 | 1 | 11 |
| regulierung | 2 | 1 | 3 |

### G28 – PDF-Operationen (Metadaten, Wasserzeichen, Seiten)

*Klasse:* (c) fachliche Bibliothek · *Apps:* audit-portal, audit_designer, flowinvoice, pdf-editor · *Definitionen:* 13 · *Varianten (Rumpf-Hash):* 7

*Ziel:* neue Bibliothek @auditcore/pdf-tools (pdf-lib-basierte Operationen + Vue-Composable)

*Unterschiede:*

- usePdfTools.ts in pdf-editor und audit_designer (vpai/pdf-tools) mit 18 wortgleichen Funktionen (mergePdfs, splitPdf, compressPdf, addWatermark, setMetadata, wordToPdf …); Komponenten PdfRotate/PdfCompare/PageThumbnailGrid doppelt

*Parität zur Python-Seite:* auditcore_documents (Python) für serverseitige PDF-Verarbeitung – Abgrenzung festlegen

| App | Def. | Aufrufer Graph | Aufrufer Text |
|---|---:|---:|---:|
| audit_designer | 6 | 0 | 16 |
| pdf-editor | 5 | 0 | 15 |
| audit-portal | 1 | 0 | 1 |
| flowinvoice | 1 | 0 | 1 |

### G22 – localStorage-JSON-Wrapper

*Klasse:* (b) @auditcore/common · *Apps:* audit-portal, audit_designer, flowinvoice · *Definitionen:* 12 · *Varianten (Rumpf-Hash):* 9

*Ziel:* @auditcore/common/browser: safeStorage (JSON lesen/schreiben mit try/catch, Präfix)

*Unterschiede:*

- loadFromStorage/saveToStorage je Präferenz-Store einzeln (audit_designer 7×, flowinvoice/audit-portal useRiskWheelSettings); pdf-editor hat lib/safeStorage.ts als zentrale Lösung
- Schlüsselpräfixe und Versionierung der gespeicherten Struktur uneinheitlich

| App | Def. | Aufrufer Graph | Aufrufer Text |
|---|---:|---:|---:|
| audit_designer | 8 | 0 | 79 |
| audit-portal | 2 | 0 | 2 |
| flowinvoice | 2 | 0 | 2 |

### G23 – Polling/SSE/Stream-Leser

*Klasse:* (b) @auditcore/common · *Apps:* ai-router, audit_designer, cockpit · *Definitionen:* 11 · *Varianten (Rumpf-Hash):* 11

*Ziel:* @auditcore/common: timing/poll (poll mit Abbruchsignal, Backoff); SSE-Leser als eigenes Modul

*Unterschiede:*

- setInterval ohne Abbruch bei Seitenwechsel in einzelnen Views; SSE per EventSource gegenüber fetch-Reader

| App | Def. | Aufrufer Graph | Aufrufer Text |
|---|---:|---:|---:|
| audit_designer | 9 | 6 | 84 |
| ai-router | 1 | 0 | 2 |
| cockpit | 1 | 0 | 2 |

### G12 – Debounce/Throttle

*Klasse:* (b) @auditcore/common · *Apps:* audit_designer, flowsearch, riskanalysis · *Definitionen:* 7 · *Varianten (Rumpf-Hash):* 7

*Ziel:* @auditcore/common: timing (debounce, throttle, keyedDebounce) + Vue useDebounce in @auditcore/ui

*Unterschiede:*

- Nur Hand-Timer (clearTimeout/setTimeout) mit 400 ms, 600 ms, 1,2 s; keine Abbruch-/flush-Funktion beim Verlassen der Seite (Datenverlust-Risiko bei debouncedSave)
- audit_designer/flowsearch haben @vueuse/core (useDebounceFn) bereits als Abhängigkeit, nutzen es aber hier nicht

| App | Def. | Aufrufer Graph | Aufrufer Text |
|---|---:|---:|---:|
| audit_designer | 5 | 2 | 25 |
| flowsearch | 1 | 0 | 1 |
| riskanalysis | 1 | 0 | 14 |

### G17 – Initialen aus Namen

*Klasse:* (b) @auditcore/common · *Apps:* audit-portal, audit_designer, flowinvoice · *Definitionen:* 7 · *Varianten (Rumpf-Hash):* 3

*Ziel:* @auditcore/common: text (initials)

*Unterschiede:*

- 3 Varianten (5× audit_designer, je 1× flowinvoice/audit-portal DirectorsSection)

| App | Def. | Aufrufer Graph | Aufrufer Text |
|---|---:|---:|---:|
| audit_designer | 5 | 0 | 55 |
| audit-portal | 1 | 1 | 1 |
| flowinvoice | 1 | 1 | 1 |

### G21 – Text kürzen

*Klasse:* (b) @auditcore/common · *Apps:* audit-portal, audit_designer, flowinvoice · *Definitionen:* 4 · *Varianten (Rumpf-Hash):* 3

*Ziel:* @auditcore/common: text (truncate mit „…“)

*Unterschiede:*

- „…“ gegenüber „...“; Kürzung nach Zeichen, nicht nach Graphemen

| App | Def. | Aufrufer Graph | Aufrufer Text |
|---|---:|---:|---:|
| audit_designer | 2 | 0 | 560 |
| audit-portal | 1 | 1 | 4 |
| flowinvoice | 1 | 1 | 4 |

### G29 – Formular-Validatoren (E-Mail, Pflichtfeld, Passwort)

*Klasse:* (b) @auditcore/common · *Apps:* audit-portal, audit_designer, flowinvoice · *Definitionen:* 4 · *Varianten (Rumpf-Hash):* 2

*Ziel:* @auditcore/common: validate (email, required, passwordPolicy)

*Unterschiede:*

- kaum vorhanden (4 Funktionen); Passwortregeln in audit_designer ActivateView eigen

*Parität zur Python-Seite:* Passwort-/E-Mail-Regeln serverseitig (Python) spiegeln

| App | Def. | Aufrufer Graph | Aufrufer Text |
|---|---:|---:|---:|
| audit_designer | 2 | 1 | 10 |
| audit-portal | 1 | 0 | 0 |
| flowinvoice | 1 | 0 | 0 |

### G25 – ID/UUID erzeugen

*Klasse:* (b) @auditcore/common · *Apps:* audit-portal, audit_designer, cockpit · *Definitionen:* 3 · *Varianten (Rumpf-Hash):* 4

*Ziel:* @auditcore/common: ids (newId via crypto.randomUUID mit Rückfall)

*In auditcore vorhanden:* kanban-core (lokal) eigene ID-Erzeugung

*Unterschiede:*

- Math.random().toString(36) gegenüber crypto.randomUUID (ohne sicheren Kontext nicht verfügbar)

*Parität zur Python-Seite:* auditcore_common.ids (Python)

| App | Def. | Aufrufer Graph | Aufrufer Text |
|---|---:|---:|---:|
| audit-portal | 1 | 0 | 7 |
| audit_designer | 1 | 0 | 1 |
| cockpit | 1 | 1 | 2 |

### X3 – Login-Vorlage (packages/login-template)

*Klasse:* (c) fachliche Bibliothek · *Apps:* flowinvoice, audit-portal · *Definitionen:* 8

*Ziel:* @auditcore/ui-react (Login-Formular) – liegt als „Paket“ bereits unter src/packages/login-template mit README

*Unterschiede:*

- wortgleich in beiden Apps; regulierung hat LoginError identisch in vorgangUi.tsx

### G20 – Prüfziffer mod 97 (IBAN/Leitweg-ID)

*Klasse:* (b) @auditcore/common · *Apps:* rechnung · *Definitionen:* 4 · *Varianten (Rumpf-Hash):* 5

*Ziel:* @auditcore/common: checks/mod97 (mod97, ibanIsValid, leitwegCheckDigits)

*Unterschiede:*

- Im Frontend nur rechnung (leitweg.ts: mod97, computeLeitwegCheckDigits); keine IBAN-Prüfung im Browser – obwohl flowinvoice/regulierung IBAN erfassen
- Backend-Seite prüft IBAN (auditcore_documents validate_iban, auditcore_invoicesynth iban_valid)

*Parität zur Python-Seite:* Python validate_iban/iban_valid und TS-Pendant auf dieselben Testfälle (gültig/ungültig/Leerzeichen/Kleinbuchstaben)

| App | Def. | Aufrufer Graph | Aufrufer Text |
|---|---:|---:|---:|
| rechnung | 4 | 3 | 5 |

### G18 – Status-/Risiko-Label und -Farbe

*Klasse:* (d) bleibt in der App · *Apps:* ai-router, audit-portal, audit_designer, cockpit, flowinvoice, flowsearch, qaaudit, regulierung, riskanalysis, versteigerung · *Definitionen:* 99 · *Varianten (Rumpf-Hash):* 58

*Ziel:* bleibt in den Apps; nur Risiko-Stufen (hoch/mittel/niedrig) an @auditcore/ui risk/view/labels.ts angleichen

*In auditcore vorhanden:* @auditcore/ui risk/view/labels.ts (nur Risiko-Flags)

*Unterschiede:*

- Fachliche Status-Enums je App; Farben hart kodiert (#ef4444 …) statt Theme-Token

*Parität zur Python-Seite:* Risikostufen-Schlüssel mit auditcore_risk

| App | Def. | Aufrufer Graph | Aufrufer Text |
|---|---:|---:|---:|
| audit_designer | 47 | 1 | 796 |
| audit-portal | 19 | 17 | 204 |
| flowinvoice | 15 | 9 | 63 |
| ai-router | 4 | 0 | 28 |
| cockpit | 3 | 0 | 39 |
| regulierung | 3 | 2 | 15 |
| flowsearch | 2 | 0 | 2 |
| qaaudit | 2 | 1 | 6 |
| riskanalysis | 2 | 0 | 0 |
| versteigerung | 2 | 2 | 5 |

### G27 – Benutzerverwaltungs-API-Client

*Klasse:* (d) bleibt in der App · *Apps:* audit-portal, audit_designer, flowinvoice, flowsearch, regulierung · *Definitionen:* 20 · *Varianten (Rumpf-Hash):* 15

*Ziel:* bleibt (App-Backends mit eigenen Nutzer-Endpunkten)

*Unterschiede:*

- createUser/updateUser/deleteUser je App gegen eigene REST-Pfade

| App | Def. | Aufrufer Graph | Aufrufer Text |
|---|---:|---:|---:|
| audit-portal | 5 | 0 | 9 |
| flowinvoice | 5 | 0 | 4 |
| regulierung | 5 | 0 | 0 |
| audit_designer | 3 | 0 | 3 |
| flowsearch | 2 | 0 | 0 |

### G24 – Query-String/URL bauen

*Klasse:* (d) bleibt in der App · *Apps:* audit_designer, versteigerung · *Definitionen:* 2 · *Varianten (Rumpf-Hash):* 2

*Ziel:* bleibt

*Unterschiede:*

- nur 2 Fundstellen

| App | Def. | Aufrufer Graph | Aufrufer Text |
|---|---:|---:|---:|
| audit_designer | 1 | 0 | 1 |
| versteigerung | 1 | 6 | 6 |

## 4. Ausführungsmatrix: deutsche Zahleneingabe (G04) im Frontend und in auditcore-Python

Alle TS-Varianten wurden aus dem Quelltext transpiliert und auf dieselben Eingaben angewendet (Werte in JS-Schreibweise, `null` = abgelehnt). `@auditcore/ui tabular.parseNumber` lief mit `decimal=","`. Die Python-Zeilen stammen aus `origin/main` (Import aus `packages/*/src`). Funktionen wie `toNumber` und `toNumberOrNull` sind keine DE-Parser (reines `Number()`). Sie stehen in der Matrix, weil sie an Stellen mit deutscher Eingabe aufgerufen werden.

| Funktion (App) | `1.234,56` | `1234,56` | `1,5` | `1.5` | `1.234` | `1,234.56` | `12 345,67 €` | `-3,2` | `(leer)` | `abc` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| parseDecimal (audit-portal) | `1.234` | `1234.56` | `1.5` | `1.5` | `1.234` | `1.234` | `12` | `-3.2` | `0` | `0` |
| toNumberOrNull (audit-portal) | null | null | null | `1.5` | `1.234` | null | null | null | null | null |
| parseRaw (audit-portal) | `1234.56` | `1234.56` | `1.5` | `15` | `1234` | `1.23456` | null | `-3.2` | null | null |
| parseGermanNumber (audit-portal) | `1234.56` | `1234.56` | `1.5` | `1.5` | `1.234` | `1234.56` | `12345.67` | `-3.2` | `0` | `0` |
| toNumber (audit-portal) | null | null | null | `1.5` | `1.234` | null | null | null | null | null |
| parseAmountInput (audit-portal) | `"1234.56"` | `"1234.56"` | `"1.5"` | `"1.5"` | `"1.234"` | `"1.23456"` | `"12345.67"` | `"-3.2"` | null | null |
| toNumber (audit_designer) | `1234.56` | `1234.56` | `1.5` | `15` | `1234` | `1.23456` | `12` | `-3.2` | `0` | `0` |
| betragFuerDienst (audit_designer) | `"1234.56"` | `"1234.56"` | `"1.5"` | `"1.5"` | `"1.234"` | `"1.23456"` | null | `"-3.2"` | null | null |
| toNumber (audit_designer) | null | null | null | `1.5` | `1.234` | null | null | null | null | null |
| parseRaw (audit_designer) | `1234.56` | `1234.56` | `1.5` | `15` | `1234` | `1.23456` | null | `-3.2` | null | null |
| parseNumber (audit_designer) | null | null | null | `1.5` | `1.234` | null | null | null | null | null |
| toNumberOrNull (audit_designer) | null | null | null | `1.5` | `1.234` | null | null | null | null | null |
| parseDecimal (flowinvoice) | `1.234` | `1234.56` | `1.5` | `1.5` | `1.234` | `1.234` | `12` | `-3.2` | `0` | `0` |
| parseGermanNumber (flowinvoice) | `1234.56` | `1234.56` | `1.5` | `1.5` | `1.234` | `1234.56` | `12345.67` | `-3.2` | `0` | `0` |
| zuZahl (regulierung) | `1234.56` | `1234.56` | `1.5` | `15` | `1234` | `1.23456` | null | null | null | null |
| parseNumberDe (regulierung) | `1234.56` | `1234.56` | `1.5` | `15` | `1234` | `1.23456` | `12345.67` | `-3.2` | null | null |
| parseNumber (auditcore:ui) | `1234.56` | `1234.56` | `1.5` | `15` | `1234` | `1.23456` | `12345.67` | `-3.2` | null | null |
| auditcore_property_sources…parse_de_number (Python) | `1234.56` | `123.0` | `1.5` | `1.0` | `1234.0` | `1.23` | `12.0` | `3.2` | None | None |
| auditcore_funding_sources…to_decimal (Python) | None | None | None | `1.5` | `1.234` | None | None | None | None | None |
| auditcore_funding_sources…parse_amount (Python) | `1234.56` | `1234.56` | `1.5` | `1.5` | `1.234` | `1234.56` | `0.0` | `-3.2` | `0.0` | `0.0` |
| auditcore_documents…parse_amount (Python) | `1234.56` | `1234.56` | `1.5` | `1.5` | None | `1234.56` | None | None | None | None |
| auditcore_price_analysis…parse_decimal (Python) | Ausnahme | Ausnahme | Ausnahme | `1.5` | `1.234` | Ausnahme | Ausnahme | Ausnahme | Ausnahme | Ausnahme |

**Befunde**

1. **`BeleglisteGrid.parseDecimal` (flowinvoice, audit-portal)** ersetzt nur das erste Komma: `1.234,56` → `1.234`, `12 345,67 €` → `12`, und `0` statt Ablehnung. In einer Belegliste ist das ein Betragsfehler.
2. **`1.5` ist mehrdeutig.** Strikt deutsch (regulierung, `@auditcore/ui`, audit_designer `parseRaw`) liest daraus `15`, heuristisch (`parseGermanNumber`, `parseAmountInput`, Python `flowsearch.parse_amount`) `1.5`. Beides ist vertretbar, muss aber pro Feld festgelegt werden. Vorschlag: Betragsfelder strikt deutsch; Import aus Fremddateien heuristisch mit Warnung.
3. **Python ist nicht besser:** `auditcore_property_sources.zvg.parse_de_number` ist ein Textsucher („1234,56“ → `123.0`, „1.5“ → `1.0`) und darf nicht als allgemeiner Parser gelten. `auditcore_price_analysis.parse_decimal` akzeptiert nur Punkt-Notation. `funding_sources._parsing.to_decimal` lehnt alles Deutsche ab.
4. **Rückgabetyp:** Für Beträge, die ans Backend gehen, ist der Decimal-String (`parseAmountInput`, `betragFuerDienst`) richtig, weil er Rundungsfehler von `number` vermeidet. Die gemeinsame API sollte beides anbieten.

## 5. Parität Frontend ↔ Backend (gemeinsame Testfälle)

| Regel | TS-Varianten | Python in auditcore | Vorschlag |
|---|---|---|---|
| Dezimalzahl DE parsen | 13 Varianten (G04), Matrix oben | `parse_amount` (documents, funding_sources ×3), `to_decimal` (×2), `parse_de_number`, `parse_decimal`, `auditcore_common.numeric.parse_percent_rate` | `contracts/common-cases/decimal-de.json`: Eingabe, Modus (`strict-de`/`auto`), Erwartung als Decimal-String oder `null`; gleiche Datei in vitest und pytest |
| Betrag → Text | 40 Varianten (G02); NBSP bei Intl, Leerzeichen bei Hand | Berichtsformatierung in `auditcore_reporting`/`_invoicesynth`; `auditcore_common.text.group_thousands_de` | `money-de.json` mit festgelegtem NBSP (U+00A0) vor „€“, 2 Nachkommastellen, Ersatzwert „—“ |
| Datum → Text | 98 Varianten (G01) | `format_datetime_de` (dataprotection), `format_date` (invoicesynth) | `date-de.json`: Datum-only lokal, UTC-Zeitstempel mit `timeZone: Europe/Berlin`, ungültig → Ersatzwert |
| IBAN / Leitweg-ID (mod 97) | nur rechnung `leitweg.ts` | `validate_iban` (documents), `iban_valid`/`iban_check_digits` (invoicesynth) | `mod97.json`: gültig, falsche Prüfziffer, Kleinbuchstaben, Leerzeichen, Länderlänge |
| HTML-Escaping | 5 bzw. 3 Zeichen (G11) | `auditcore_common.html_text` (Branch `feat/auditcore-common`) | eine Escape-Tabelle mit 5 Zeichen |
| CSV-Zellen | `;`/`,`, BOM selten, kein Formelschutz (G08) | CSV/XLSX-Exporte in `auditcore_reporting` | `csv.json`: Trenner `;`, BOM, Quoting, Präfix `'` vor `= + - @` |
| API-Fehlerform | 31 Varianten (G09) | FastAPI `detail` (String/422-Liste) in den Apps; `{error:{code,message}}` in auditcore-Routern | `errors.json` mit beiden Formen; `errorMessage()` muss beide lesen |

Die Python-Inventur (`app-helfer-python.*`) und `auditcore_common` sollten dieselben Falldateien verwenden. Wo Python und TS heute voneinander abweichen, legt die Falldatei die Regel fest, und beide Seiten folgen ihr.

## 6. Vorschlag: Zuschnitt `@auditcore/common`

Framework-frei, TypeScript strict (`noUncheckedIndexedAccess`), ESM, ohne Laufzeitabhängigkeiten, keine DOM-Zugriffe beim Import (SSR-tauglich für Next.js in versteigerung). DOM-abhängige Helfer liegen im Unterpfad `@auditcore/common/browser`. Die bisher in `@auditcore/ui` liegenden framework-freien Module wandern hierher; `@auditcore/ui` exportiert sie weiter, sodass die öffentliche API unverändert bleibt.

| Modul | API (Entwurf) | Ersetzt (Gruppen) | Herkunft/Vorbild |
|---|---|---|---|
| `format/locale` | `type AppLocale = 'de' \| 'en'`, `localeTag(locale)` | – | `@auditcore/ui i18n/format.ts`, versteigerung `toIntlLocale` |
| `format/date` | `parseDateInput(v): Date \| null` (Datum-only lokal), `formatDate(v, {locale, empty, timeZone})`, `formatDateTime(v, {seconds})`, `formatTime`, `toIsoDate(date)` | G01 | regulierung `formatDatumDe`, versteigerung `parseDateValue`, ui `formatDate` |
| `format/number` | `formatNumber(v, {locale, digits, minDigits, maxDigits, empty})`, `formatInt`, `formatPercent(v, {scale: 'ratio' \| 'percent', digits})` | G03 | regulierung `numberFormat.ts`, ui `formatPercent` |
| `format/money` | `formatEur(v: number \| string \| null, {digits = 2, cents = false, empty = '—'})`, `formatEurCompact(v)` („1,2 Mio. €“, „850 T€“) | G02 | audit-portal `vpFormat.formatEur`, KPIStrip |
| `format/bytes` | `formatBytes(bytes, {locale, digits = 1})` – Basis 1024, Dezimalkomma | G05 | cockpit `formatBytes` (korrigiert) |
| `format/duration` | `formatDuration(ms)`, `formatUptime(s)`, `formatRelativeTime(v, {now, locale})` (Intl.RelativeTimeFormat) | G06 | ai-router `relativeTime` |
| `parse/number` | `parseDecimal(text, {mode: 'strict-de' \| 'strict-en' \| 'auto', allowNegative, stripCurrency}): number \| null`, `parseDecimalString(...)`: `string \| null` | G04 | ui `tabular.parseNumber`, `parseAmountInput`, `parseGermanNumber` |
| `http/error` | `errorMessage(err: unknown, fallback: string): string`, `httpStatus(err): number \| null` – liest Axios-Form, FastAPI `detail` (String und 422-Liste), `{error:{code,message}}`, `Error`, `string` | G09 | audit_designer `extractError`-Familie, ui `toError` |
| `http/rest` | `requestJson`, `requestFile`, `RestError`, `contentDispositionFilename` (inkl. `filename*=UTF-8''`) | G07 (Teil) | ui `rest/client.ts` |
| `auth/token` | `interface TokenStore {get, set, clear}`, `createTokenStore({key, storage: 'local' \| 'session' \| 'memory'})`, `bearerHeaders(store)`, `jwtExpiry(token)` | G10 | ai-router/cockpit `setToken`, flowinvoice `flowaudit_token` |
| `text` | `escapeHtml` (5 Zeichen), `truncate(text, max, '…')`, `initials(name)`, `slugify` | G11, G17, G21 | audit-portal `renderMarkdown.escapeHtml` |
| `export/csv` | `toCsv(rows, columns, {delimiter = ';', bom = true, guardFormulas = true})`, `escapeCsvCell`, `parseCsv` (RFC 4180) | G08 | audit_designer `GisAttributeTable.exportCsv` |
| `timing` | `debounce(fn, ms)` mit `cancel()/flush()`, `throttle`, `keyedDebounce`, `poll(fn, {intervalMs, signal, backoff})` | G12, G23 | – |
| `table/sort` | `compareValues`, `sortRows`, `nextSort(state, key, {cycle: 'bi' \| 'tri'})`, `ariaSort` | G14 | ui `table/sort.ts` |
| `checks/mod97` | `mod97(digits)`, `isValidIban(text)`, `normalizeIban`, `leitwegCheckDigits` | G20 | rechnung `leitweg.ts` |
| `ids` | `newId()` (`crypto.randomUUID` mit Rückfall für HTTP ohne sicheren Kontext) | G25 | – |
| `toast` | framework-freie Warteschlange `createToastQueue({defaultMs, errorMs})` | G19 | ai-router/cockpit `stores/toast.ts` |
| `browser/*` | `saveFile`, `downloadBlob(blob, name, {datePrefix})`, `copyText` (Clipboard + textarea-Rückfall), `safeStorage` (JSON, Präfix, Version), `subscribeMediaQuery`, `onClickOutside` | G07, G13, G16, G22 | ui `saveFile` (mit verzögertem `revokeObjectURL`), pdf-editor `safeStorage.ts`, audit_designer `copyText` |

**Offene Festlegungen vor der Umsetzung (Nutzerentscheidung):** (1) Ersatzwert für leere Werte einheitlich „—“? (2) `formatBytes` mit „KB/MB“ (Status quo, Basis 1024) oder „KiB/MiB“? (3) `1.5` in Betragsfeldern strikt als 15 oder mit Warnung? (4) Anzeige-Zeitzone fest `Europe/Berlin` oder Browserzeit?

## 7. Vue- und React-Anteile

| Baustein | Vue (`@auditcore/ui`) | React (`@auditcore/ui-react`) | Kern in `@auditcore/common` |
|---|---|---|---|
| Toast (G19) | `useToast()` | `useToast()` + `ToastProvider` | `toast` |
| Media-Query / Klick außerhalb (G16) | `useMediaQuery`, `useClickOutside` | `useMediaQuery`, `useClickOutside` (heute wortgleich in 3 React-Apps) | `browser/subscribeMediaQuery`, `onClickOutside` |
| Sortierung (G14) | `useSort` (auf vorhandenem `FaTable`) | `useSort` | `table/sort` |
| Debounce (G12) | `useDebouncedFn` (mit Abbau bei `onBeforeUnmount`) | `useDebouncedCallback` | `timing/debounce` |
| Theme (G15) | vorhanden: `applyTheme/useTheme` | `ThemeProvider/useTheme` (data-theme wie Vue) | – |
| Token/Auth (G10) | `useAuthToken` | `useAuthToken` | `auth/token` |
| eGPU-Widget (G26) | – | `EgpuPipelineWidget` (aus flowinvoice/audit-portal/regulierung) | `format/duration.formatUptime` |
| Login-Vorlage (X3) | – | `LoginTemplate` (heute `src/packages/login-template` in flowinvoice und audit-portal) | – |

Die React-Brücke `@auditcore/ui-react` wickelt heute nur Custom Elements ein (`createElementComponent`). Für echte Hooks braucht sie einen eigenen Hook-Bereich mit `react` als peerDependency.

## 8. Fachliche Cluster (Klasse c) und Forks

| Paar | Wortgleiche Funktionen | Einordnung |
|---|---:|---|
| ai-router ↔ cockpit | 7 | gemeinsames Gerüst `api/auth.ts`, `api/client.ts extractError`, `stores/toast.ts` (G10, G09, G19) |
| audit-portal ↔ audit_designer | 49 | FlowStat-Custom-Node-Kern (42 von 49), React- und Vue-Port desselben Kerns (X1) → `@auditcore/flowstat-customnode` |
| audit-portal ↔ flowinvoice | 576 | Fork: fraud-report, company-report, risk-wheel, belegliste, pipeline, settings (X2). Keine Hilfsfunktionen, sondern eine Produktentscheidung: gemeinsames React-Paket oder eine führende App |
| audit-portal ↔ regulierung | 19 | eGPU-Widget, AuthContext, Hilfs-Toggles (G26) |
| audit_designer ↔ flowinvoice | 4 | Einzelfunktionen (formatCurrency, Status-Mapping) |
| audit_designer ↔ pdf-editor | 23 | `usePdfTools` + PDF-Werkzeugkomponenten (G28) → `@auditcore/pdf-tools` |
| audit_designer ↔ regulierung | 3 | Einzelfunktionen |
| flowinvoice ↔ regulierung | 17 | eGPU-Widget (`EgpuPipelineWidget.tsx` wortgleich), `useAuth`, `LoginError` |

Für X1 und G28 gilt dieselbe Voraussetzung: Eine App wird Quelle (audit_designer hat bei X1 die Tests, pdf-editor ist bei G28 die eigenständige App). Die Charakterisierung erfolgt nach `docs/prompts/CLAUDE_LIBRARY_BUILD.md` (provenance.json, Gates).

## 9. Migrationsaufwand je App

Zählung: Definitionen in Gruppen der Klassen (a) und (b), die durch `@auditcore/common` bzw. `@auditcore/ui(-react)` ersetzt würden. Aufwand grob in Personentagen: S ≤ 1, M 2–4, L 5–10.

| App | FW | Def. (a+b) | Gruppen | Zentrale Helfer vorhanden | Tests für Helfer | Fachliche Cluster (c) | Aufwand |
|---|---|---:|---:|---|---|---|---|
| audit_designer | Vue | 344 | 23 | kaum (`utils/format.ts` mit 2 Funktionen); Formatierer lokal in Komponenten | vitest (149 Specs), u. a. customnode core, NumberInput | X1 (Quelle), G28 | **L** – viele verstreute Einzeiler, 37 × Fehlertext, 37 × Dateigröße; schrittweise pro Modul |
| audit-portal | React | 96 | 21 | `lib/vpFormat.ts`, `lib/download.ts`, `fraud-report/format.ts` | vitest (44), `fraud-report/__tests__/format.test.ts` | X1, X2, X3, G26 | **L** – vor allem wegen des Forks X2 |
| flowinvoice | React | 73 | 19 | `lib/regional-format.ts` (Locale-Präferenzen) | vitest (18), `regional-format.test.ts` | X2 (Quelle), X3, G26 | **M** |
| regulierung | React | 52 | 14 | `lib/numberFormat.ts`, `lib/dateFormat.ts`, `lib/download.ts` | keine Frontend-Tests | G26 | **M** – zentrale Module erleichtern den Tausch; ohne Tests vorher charakterisieren |
| cockpit | Vue | 26 | 11 | `utils/format.ts` | 1 Spec | – | **S** |
| ai-router | Vue | 23 | 9 | `utils/format.ts` | `tests/format.test.ts` | – | **S** – Gerüst mit cockpit teilen |
| pdf-editor | Vue | 20 | 6 | `lib/safeStorage.ts`, `lib/auth.ts` | keine | G28 (Quelle) | **M** (wegen `@auditcore/pdf-tools`) |
| riskanalysis | Vue | 9 | 5 | `verwk/format.ts` | 1 Spec | – | **S** |
| flowsearch | Vue | 8 | 5 | – | keine | – | **S** |
| versteigerung | React/Next | 8 | 6 | `lib/format.ts` (kommt dem Vorschlag am nächsten) | keine | – | **S** (SSR-Tauglichkeit prüfen) |
| rechnung | React | 7 | 4 | `utils/leitweg.ts`, `utils/calc.ts` | keine | – | **S** (Quelle für `checks/mod97`) |
| qaaudit | React | 3 | 2 | – | keine | – | **S** |

**Empfohlene Reihenfolge:** (1) Falldateien `contracts/common-cases/*` für Zahl, Betrag, Datum, mod 97, CSV und Fehlerform anlegen, gemeinsam mit der Python-Inventur. (2) `@auditcore/common` mit `parse/number`, `format/*`, `http/error` bauen, Baseline 0 im Quality-Gate. (3) framework-freie Module aus `@auditcore/ui` verschieben und re-exportieren. (4) Sofortkorrektur `BeleglisteGrid.parseDecimal` in flowinvoice/audit-portal, unabhängig von der Paketarbeit. (5) Apps mit zentralen Helfermodulen zuerst umstellen (regulierung, cockpit, ai-router, riskanalysis, versteigerung). (6) Danach audit_designer schrittweise. (7) X1/G28/X2 als eigene Bibliotheksvorhaben.

## 10. Grenzen der Auswertung

- Namens- und Rumpfmuster finden nicht jede Hilfsfunktion. Inline-Ausdrücke in Templates (etwa `{{ new Date(x).toLocaleDateString() }}`) sind nicht als Funktionen erfasst, der tatsächliche Duplikatumfang ist also größer.
- Die Aufruferzahlen aus graphify sind Untergrenzen (Vue-Templates fehlen, nur ~45 % Knotenzuordnung). Die Textzahlen sind Obergrenzen.
- `@auditcore/ui`-Fachmodule (risk, sampling/tabular, screening) wurden aus Branches gelesen und können sich bis zu ihrem Merge noch ändern; Basis, i18n, rest, table, theme und `kanban-core` sind seit #84 in `main`.
- In den App-Repos wurde nichts geändert (nur `git fetch` und `git archive`).
