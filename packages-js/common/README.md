# @flowaudit/common

## Zweck

Framework-freie Hilfsfunktionen der FlowAudit-Anwendungen in TypeScript: deutsche Formatierung in Berliner Zeit, strikte Zahleneingabe, API-Fehlertexte, REST, Token, CSV, Zeitsteuerung, Sortierung und Prüfziffern.

Für alle Frontends (Vue, React, Next.js, ohne Framework) und für Node-Skripte.
Das Paket ersetzt die vielen lokalen Einzeiler aus der Inventur
[`docs/reports/app-helfer-ts.md`](../../docs/reports/app-helfer-ts.md)
(Abschnitt 6). Vue-Composables liegen in `@flowaudit/ui`, React-Hooks in
`@flowaudit/ui-react`; beide bauen auf diesem Paket auf. Fachlogik (Kanban,
Risiko, Stichprobe) gehört nicht hierher.

## Installation

Im auditcore-Repository ist das Paket Teil des npm-Workspace:

```sh
npm ci                               # im Repository-Stamm
npm run build -w @flowaudit/common   # dist/: ESM und Typen
npm test -w @flowaudit/common        # Vitest, zweiter Lauf mit TZ=America/New_York
```

Im Anwendungsrepository:

```sh
npm install @flowaudit/common
```

Das Paket ist noch nicht in einer npm-Registry veröffentlicht; bis dahin
Bezug über den Workspace oder ein mit `npm pack -w @flowaudit/common`
erzeugtes Tarball (`npm install ./flowaudit-common-0.1.0.tgz`). Keine
Peer-Abhängigkeiten, kein CSS.

## Schnellstart

```ts run
import { errorMessage, formatBytes, formatDate, formatDateTime, formatEur, parseDecimalResult, parseDecimalString, toCsv } from '@flowaudit/common'

// Anzeige immer in Berliner Zeit, reine Datumswerte ohne Verschiebung, Ersatzwert „—“
if (formatDate('2026-01-31') !== '31.01.2026') throw new Error('Datum')
if (formatDateTime('2026-01-31T23:30:00Z') !== '01.02.2026, 00:30') throw new Error('Zeit')
if (formatEur(0.125) !== '0,13 €') throw new Error('kaufmännisch runden')
if (formatBytes(1536) !== '1,5 KB' || formatDate(null) !== '—') throw new Error('Format')

// Betragsfelder: strikt deutsch, nichts raten
if (parseDecimalString('1.234,56') !== '1234.56') throw new Error('Betrag')
const ambiguous = parseDecimalResult('1.5')
if (ambiguous.ok || ambiguous.reason !== 'ambiguous') throw new Error('„1.5“ ist mehrdeutig')

// FastAPI-422-Liste lesbar statt „[object Object]“
const error = { response: { status: 422, data: { detail: [{ loc: ['body', 'betrag'], msg: 'Field required' }] } } }
console.log(errorMessage(error, 'Unbekannter Fehler')) // betrag: Field required

// CSV für Excel: BOM, „;“, Dezimalkomma, Formelschutz
console.log(JSON.stringify(toCsv([['Name', 'Betrag'], ['=HYPERLINK("x")', 1234.5]])))
```

Browser-Helfer (Download, Zwischenablage, Speicher, Media-Query, Klick
außerhalb) kommen aus dem Unterpfad `@flowaudit/common/browser`:

```ts
import { copyText, downloadBlob, safeStorage } from '@flowaudit/common/browser'
import { csvBlob, toCsv } from '@flowaudit/common'

downloadBlob(csvBlob(toCsv([['Beleg'], ['R-1']])), 'belege.csv', { datePrefix: true })
const prefs = safeStorage({ prefix: 'flowinvoice', version: 1 })
prefs.set('filter', { status: 'offen' })
void copyText('DE89 3704 0044 0532 0130 00')
```

## Einbindung

- **Direkt** in TypeScript/JavaScript (Browser, Node ≥ 20.19, SSR): alle
  Funktionen sind rein bzw. greifen erst beim Aufruf auf `globalThis` zu;
  beim Import wird nichts ausgeführt.
- **Vue:** Composables in `@flowaudit/ui` – `useToast`, `useMediaQuery`,
  `useClickOutside`, `useSort`, `useDebouncedFn`, `useDebouncedRef`,
  `useThrottledFn`, `useAuthToken`.
- **React:** Hooks in `@flowaudit/ui-react` – `useToast` mit
  `ToastProvider`, `useMediaQuery`, `useClickOutside`, `useSort`,
  `useDebouncedCallback`, `useAuthToken`.
- **Weiter exportiert:** `@flowaudit/ui` (und `@flowaudit/ui-react`) reichen
  die bisher dort liegenden Teile unter den alten Namen weiter:
  `formatDate`/`formatNumber`/`formatPercent` (= `intlFormat*`, Rechnerzeit,
  leerer Ersatzwert), `localeTag`, `requestJson`, `requestFile`, `RestError`,
  `saveFile`, `compareValues`, `sortRows`, `nextSort`, `ariaSort`,
  `parseNumber`, `parseTable` …

## API-Überblick

Gliederung: `format/*` (Datum, Zahl, Betrag, Dateigröße, Dauer, Intl-Kurzformen),
`parse/*` (strikte Zahleneingabe, Tabellen-Einlesen), `http/*` (Fehlertext,
REST-Client), `auth/token`, `text`, `export/csv`, `timing`, `table/sort`,
`checks/mod97`, `ids`, `toast`; Unterpfad `browser`.

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Exporte der Einstiegspunkte aus `package.json#exports` (139):

| Einstieg | Name | Art | Kurzbeschreibung (erste JSDoc-Zeile) | Modul |
|---|---|---|---|---|
| `@flowaudit/common` | `APP_LOCALES` | Konstante | Alle unterstützten Sprachen. | `format/locale` |
| `@flowaudit/common` | `AppLocale` | Typ | Sprachen der FlowAudit-Oberflächen (gleich `Locale` in `@flowaudit/ui`). | `format/locale` |
| `@flowaudit/common` | `BYTE_UNITS` | Konstante | Einheiten zur Basis 1024 (Festlegung `filesize_units`). | `format/bytes` |
| `@flowaudit/common` | `BytesFormatOptions` | Schnittstelle | Optionen für `formatBytes`. | `format/bytes` |
| `@flowaudit/common` | `CSV_BOM` | Konstante | UTF-8-Byte-Order-Mark am Dateianfang. | `export/csv` |
| `@flowaudit/common` | `CellValue` | Typ | – | `table/sort` |
| `@flowaudit/common` | `CsvColumn` | Schnittstelle | Deklarative Spalte für `recordsToCsv`. | `export/csv` |
| `@flowaudit/common` | `CsvOptions` | Schnittstelle | Schreiboptionen; Standard ist Excel-DE. | `export/csv` |
| `@flowaudit/common` | `CsvValue` | Typ | Zellwert: Zahlen werden mit Dezimalkomma geschrieben, `Date` als ISO 8601, `null`/`undefined` leer. | `export/csv` |
| `@flowaudit/common` | `DISPLAY_TIME_ZONE` | Konstante | Zeitzone aller Anzeigeformatierer, unabhängig von der Rechnerzeit (Festlegung `display_timezone`). | `format/locale` |
| `@flowaudit/common` | `DateFormatOptions` | Schnittstelle | Optionen der Datumsformatierer. | `format/date` |
| `@flowaudit/common` | `DateInput` | Typ | Eingaben der Datumsformatierer: ISO-Zeichenkette, `Date` oder Epoch-Millisekunden. | `format/date` |
| `@flowaudit/common` | `Debounced` | Schnittstelle | Entprellte bzw. gedrosselte Funktion mit Steuerung des ausstehenden Aufrufs. | `timing` |
| `@flowaudit/common` | `DecimalSeparator` | Typ | – | `parse/table` |
| `@flowaudit/common` | `Delimiter` | Typ | – | `parse/table` |
| `@flowaudit/common` | `DisplayOptions` | Schnittstelle | Gemeinsame Optionen der Anzeigeformatierer. | `format/locale` |
| `@flowaudit/common` | `DownloadFile` | Schnittstelle | Heruntergeladene Datei (Export). | `http/rest` |
| `@flowaudit/common` | `EMPTY_VALUE` | Konstante | Ersatzwert jedes Anzeigeformatierers für fehlende oder ungültige Werte (Festlegung `empty_value`). | `format/locale` |
| `@flowaudit/common` | `ExpiryOptions` | Schnittstelle | Bezugszeit und Sicherheitsabstand für `isTokenExpired`. | `auth/token` |
| `@flowaudit/common` | `FetchLike` | Typ | Signatur von `fetch` (injizierbar für Authentisierung, Tests, Proxy). | `http/rest` |
| `@flowaudit/common` | `IBAN_LENGTHS` | Konstante | IBAN-Gesamtlänge je Land (SWIFT-Register, gleich `auditcore_identifiers`). | `checks/mod97` |
| `@flowaudit/common` | `KeyedDebounced` | Schnittstelle | Entprellung je Schlüssel; `cancel()` ohne Schlüssel verwirft alle. | `timing` |
| `@flowaudit/common` | `MoneyFormatOptions` | Schnittstelle | Optionen für `formatEur`. | `format/money` |
| `@flowaudit/common` | `NextSortOptions` | Schnittstelle | Umschaltzyklus für `nextSort`. | `table/sort` |
| `@flowaudit/common` | `NumberColumn` | Schnittstelle | – | `parse/table` |
| `@flowaudit/common` | `NumberFormatOptions` | Schnittstelle | Optionen für `formatNumber`. | `format/number` |
| `@flowaudit/common` | `NumberInput` | Typ | Eingaben der Zahlformatierer: Zahl oder Dezimal-String aus dem Backend. | `format/number` |
| `@flowaudit/common` | `PARSE_FAILURE_HINTS` | Konstante | Deutsche Hinweistexte zu den Ablehnungsgründen (für Formularfelder). | `parse/number` |
| `@flowaudit/common` | `ParseDecimalOptions` | Schnittstelle | Optionen der Zahleneingabe. | `parse/number` |
| `@flowaudit/common` | `ParseDecimalResult` | Typ | Ergebnis mit Dezimal-String oder Ablehnungsgrund. | `parse/number` |
| `@flowaudit/common` | `ParseFailure` | Typ | Grund einer Ablehnung: leer (nur Leerraum/Trenner/Währung), mehrdeutig oder ungültig. | `parse/number` |
| `@flowaudit/common` | `ParseMode` | Typ | `strict-de` (Betragsfelder), `strict-en` oder `auto` (Fremddateien). | `parse/number` |
| `@flowaudit/common` | `ParsedTable` | Schnittstelle | – | `parse/table` |
| `@flowaudit/common` | `PercentFormatOptions` | Schnittstelle | Optionen für `formatPercent`. | `format/number` |
| `@flowaudit/common` | `PollOptions` | Schnittstelle | Optionen für `poll`. | `timing` |
| `@flowaudit/common` | `RelativeTimeOptions` | Schnittstelle | Optionen für `formatRelativeTime`. | `format/duration` |
| `@flowaudit/common` | `RestError` | Klasse | Fehler der REST-Schnittstelle mit Status, Code und deutscher Meldung des Servers. | `http/rest` |
| `@flowaudit/common` | `RestOptions` | Schnittstelle | Basis-URL, `fetch` und Kopfzeilen eines REST-Ports. | `http/rest` |
| `@flowaudit/common` | `SortDirection` | Typ | – | `table/sort` |
| `@flowaudit/common` | `SortState` | Schnittstelle | – | `table/sort` |
| `@flowaudit/common` | `TableColumn` | Schnittstelle | – | `table/sort` |
| `@flowaudit/common` | `TableRow` | Typ | – | `table/sort` |
| `@flowaudit/common` | `TimeFormatOptions` | Schnittstelle | Optionen der Uhrzeitformatierer. | `format/date` |
| `@flowaudit/common` | `Toast` | Schnittstelle | Sichtbarer Toast. | `toast` |
| `@flowaudit/common` | `ToastInput` | Schnittstelle | Eingabe für `push`; `kind` Standard `info`. | `toast` |
| `@flowaudit/common` | `ToastKind` | Typ | Art eines Toasts (bestimmt Farbe und Standarddauer). | `toast` |
| `@flowaudit/common` | `ToastListener` | Typ | Rückruf mit dem neuen Stand der Warteschlange. | `toast` |
| `@flowaudit/common` | `ToastQueue` | Schnittstelle | Framework-freie Warteschlange; Vue und React abonnieren sie. | `toast` |
| `@flowaudit/common` | `ToastQueueOptions` | Schnittstelle | Dauer und Höchstzahl der Warteschlange. | `toast` |
| `@flowaudit/common` | `TokenListener` | Typ | Rückruf bei Tokenänderung (`null` nach `clear`). | `auth/token` |
| `@flowaudit/common` | `TokenStorageKind` | Typ | Ablageort des Tokens. | `auth/token` |
| `@flowaudit/common` | `TokenStore` | Schnittstelle | Schnittstelle für Token-Speicher (eigene Umsetzungen, z. B. Cookies, sind möglich). | `auth/token` |
| `@flowaudit/common` | `TokenStoreOptions` | Schnittstelle | Optionen für `createTokenStore`. | `auth/token` |
| `@flowaudit/common` | `ariaSort` | Funktion | – | `table/sort` |
| `@flowaudit/common` | `bearerHeaders` | Funktion | Kopfzeile `Authorization: Bearer …`, leer ohne Token. | `auth/token` |
| `@flowaudit/common` | `bodyMessage` | Funktion | Meldung aus einem Antwortkörper (`detail`, `{error: {message}}`, `message`, reiner Text). | `http/error` |
| `@flowaudit/common` | `columnCells` | Funktion | Zellen einer Spalte. | `parse/table` |
| `@flowaudit/common` | `compareValues` | Funktion | Vergleich: leere Werte immer zuletzt, Zahlen/Daten numerisch, Text sprachsensitiv. | `table/sort` |
| `@flowaudit/common` | `contentDispositionFilename` | Funktion | Dateiname aus `Content-Disposition`: `filename*=UTF-8''…` (RFC 5987, Umlaute) vor `filename="…"` und `filename=…`; ohne Angabe `null`. | `http/rest` |
| `@flowaudit/common` | `createToastQueue` | Funktion | Neue Warteschlange mit selbstständigem Ausblenden nach `durationMs`. | `toast` |
| `@flowaudit/common` | `createTokenStore` | Funktion | Token-Speicher über Web Storage oder Arbeitsspeicher (Standard `local`, Schlüssel `flowaudit_token`). | `auth/token` |
| `@flowaudit/common` | `csvBlob` | Funktion | CSV-Text als `Blob` (`text/csv;charset=utf-8`) für den Download. | `export/csv` |
| `@flowaudit/common` | `debounce` | Funktion | Führt `fn` erst aus, wenn `ms` lang kein weiterer Aufruf kam (letzte Argumente gewinnen). | `timing` |
| `@flowaudit/common` | `detailMessage` | Funktion | FastAPI-`detail`: Text, 422-Liste (`[{loc, msg, type}]`) oder Objekt mit `message`. | `http/error` |
| `@flowaudit/common` | `detectDecimal` | Funktion | Dezimaltrenner einer Spalte: stehen beide Zeichen in einer Zelle, ist das letzte der Dezimaltrenner; ein Trenner ohne genau drei Folgeziffern ist ebenfalls eindeutig. | `parse/table` |
| `@flowaudit/common` | `detectDelimiter` | Funktion | Häufigstes Trennzeichen der ersten Zeile; eine Spalte ohne Trenner ergibt ';'. | `parse/table` |
| `@flowaudit/common` | `errorMessage` | Funktion | Fehlertext für die Oberfläche. Reihenfolge: Antwortkörper (`error.response.data` oder der übergebene Körper selbst), dann `error.message`, sonst `fallback`. | `http/error` |
| `@flowaudit/common` | `escapeCsvCell` | Funktion | Eine Zelle: Formelschutz für Texte, Anführungszeichen nach RFC 4180 bei Trenner, `"` oder Zeilenumbruch. | `export/csv` |
| `@flowaudit/common` | `escapeHtml` | Funktion | Maskiert die fünf HTML-Sonderzeichen `& < > " '` (für Text in HTML und Attributen). | `text` |
| `@flowaudit/common` | `formatBytes` | Funktion | Dateigröße zur Basis 1024: `512 B`, `1,5 KB`, `117,7 MB`; negativ/leer → `—`. | `format/bytes` |
| `@flowaudit/common` | `formatDate` | Funktion | Datum `TT.MM.JJJJ` in Berliner Zeit; reine Datumswerte ohne Umrechnung; leer/ungültig → `—`. | `format/date` |
| `@flowaudit/common` | `formatDateTime` | Funktion | Datum mit Uhrzeit `TT.MM.JJJJ, HH:MM` in Berliner Zeit. Ein reines Datum hat keine Uhrzeit und erscheint wie bei `formatDate`. | `format/date` |
| `@flowaudit/common` | `formatDuration` | Funktion | Dauer in Millisekunden kompakt: `250 ms`, `3,2 s`, `4 min 5 s`, `2 h 5 min`, `3 d 4 h`; negativ/leer → `—`. | `format/duration` |
| `@flowaudit/common` | `formatEur` | Funktion | Betrag wie `Intl.NumberFormat('de-DE', {style: 'currency'})`: `1.234,50 €` mit geschütztem Leerzeichen, kaufmännisch gerundet; Zahl oder Decimal-String; leer/ungültig → `—`. | `format/money` |
| `@flowaudit/common` | `formatEurCompact` | Funktion | Kurzform für Kennzahlen: `1,2 Mio. €`, `850 T€`, `3,4 Mrd. €`; unter 1.000 wie `formatEur`. | `format/money` |
| `@flowaudit/common` | `formatIban` | Funktion | IBAN in Vierergruppen (`DE89 3704 0044 …`). | `checks/mod97` |
| `@flowaudit/common` | `formatInt` | Funktion | Ganze Zahl mit Tausenderpunkt (`12.345`). | `format/number` |
| `@flowaudit/common` | `formatNumber` | Funktion | Zahl mit Tausenderpunkt und Dezimalkomma (`1.234,5`); leer/ungültig → `—`. | `format/number` |
| `@flowaudit/common` | `formatPercent` | Funktion | Prozentwert mit geschütztem Leerzeichen vor „%“ (`12,5 %`). | `format/number` |
| `@flowaudit/common` | `formatRelativeTime` | Funktion | Relative Zeit mit `Intl.RelativeTimeFormat`: „vor 5 Minuten“, „gestern“, „in 2 Tagen“. | `format/duration` |
| `@flowaudit/common` | `formatTime` | Funktion | Uhrzeit `HH:MM` (optional mit Sekunden) in Berliner Zeit. | `format/date` |
| `@flowaudit/common` | `formatUptime` | Funktion | Laufzeit in Sekunden (Dienste, eGPU): `45 s`, `12 min 3 s`, `5 d 2 h`. | `format/duration` |
| `@flowaudit/common` | `guessNumberColumn` | Funktion | Index der ersten Spalte, deren nicht leere Zellen überwiegend (≥ 60 %) Zahlen sind; sonst 0. | `parse/table` |
| `@flowaudit/common` | `httpStatus` | Funktion | HTTP-Status eines Fehlers (`error.response.status` oder `error.status`); sonst `null`. | `http/error` |
| `@flowaudit/common` | `initials` | Funktion | Initialen aus einem Namen (`Jan Riener` → `JR`, `riener, jan` → `RJ`), höchstens `max` Zeichen. | `text` |
| `@flowaudit/common` | `intlFormatDate` | Funktion | Datum (ISO-Zeichenkette oder Date) kurz und sprachabhängig; ungültige Werte bleiben leer. | `format/intl` |
| `@flowaudit/common` | `intlFormatNumber` | Funktion | Zahl mit `Intl.NumberFormat` und frei wählbaren Optionen. | `format/intl` |
| `@flowaudit/common` | `intlFormatPercent` | Funktion | Anteil (0–1) als Prozent mit fester Nachkommazahl. | `format/intl` |
| `@flowaudit/common` | `isEmptyValue` | Funktion | `null`, `undefined`, leere Zeichenkette oder `NaN` – Werte, für die Formatierer den Ersatzwert zeigen. | `format/locale` |
| `@flowaudit/common` | `isTokenExpired` | Funktion | Abgelaufen oder läuft innerhalb des Sicherheitsabstands ab? Tokens ohne `exp` gelten als nicht abgelaufen. | `auth/token` |
| `@flowaudit/common` | `isValidIban` | Funktion | Gültig nur mit bekanntem Land, passender Länge und Prüfziffer (Leerzeichen und Kleinbuchstaben erlaubt). | `checks/mod97` |
| `@flowaudit/common` | `isValidLei` | Funktion | LEI nach ISO 17442: 20 Zeichen A–Z/0–9, die letzten beiden sind Prüfziffern (MOD 97-10). | `checks/mod97` |
| `@flowaudit/common` | `isValidLeitwegId` | Funktion | Leitweg-ID `Grob[-Fein]-Prüfziffer` mit gültiger Prüfziffer. | `checks/mod97` |
| `@flowaudit/common` | `iso7064CheckDigits` | Funktion | Zwei Prüfziffern nach ISO 7064 MOD 97-10 für einen Rumpf aus A–Z/0–9. | `checks/mod97` |
| `@flowaudit/common` | `jwtExpiry` | Funktion | Ablaufzeit (`exp`) eines JWT; `null`, wenn keine lesbar ist. | `auth/token` |
| `@flowaudit/common` | `jwtPayload` | Funktion | Nutzdaten eines JWT ohne Signaturprüfung (nur zur Anzeige und Ablaufsteuerung); `null` bei Fehlform. | `auth/token` |
| `@flowaudit/common` | `keyedDebounce` | Funktion | Entprellen je Schlüssel (z. B. Speichern je Datensatz). | `timing` |
| `@flowaudit/common` | `leitwegCheckDigits` | Funktion | Prüfziffern einer Leitweg-ID (XRechnung) aus Grob- und Feinadressierung, z. B. `04011000-1234512345`. | `checks/mod97` |
| `@flowaudit/common` | `lettersToDigits` | Funktion | Buchstaben in Zahlen (A=10 … Z=35); andere Zeichen bleiben. | `checks/mod97` |
| `@flowaudit/common` | `localeTag` | Funktion | BCP-47-Tag für `Intl`: `de` → `de-DE`, `en` → `en-GB`. | `format/locale` |
| `@flowaudit/common` | `mod97` | Funktion | Rest modulo 97 einer beliebig langen Ziffernfolge (stückweise, ohne BigInt). | `checks/mod97` |
| `@flowaudit/common` | `newId` | Funktion | Neue UUID v4. Nutzt `crypto.randomUUID` und fällt ohne sicheren Kontext (HTTP im Intranet) auf `crypto.getRandomValues` zurück, zuletzt auf `Math.random` (nur für Anzeige-Kennungen … | `ids` |
| `@flowaudit/common` | `nextSort` | Funktion | Nächster Zustand beim Klick auf eine Spalte: aufsteigend → absteigend → unsortiert (bzw. zurück zu aufsteigend bei `bi`). | `table/sort` |
| `@flowaudit/common` | `normalizeIban` | Funktion | IBAN ohne Leerraum, in Großbuchstaben. | `checks/mod97` |
| `@flowaudit/common` | `numberColumn` | Funktion | Eine Spalte als Zahlen; unlesbare Zellen werden verworfen und gemeldet. | `parse/table` |
| `@flowaudit/common` | `parseCalendarDay` | Funktion | Reines Datum `JJJJ-MM-TT` als Kalendertag (ohne Zeitzone); `null` bei anderem Format oder ungültigem Tag. | `format/date` |
| `@flowaudit/common` | `parseCsv` | Funktion | Liest CSV nach RFC 4180 (Anführungszeichen, `""`, Zeilenumbrüche in Zellen); BOM wird entfernt, Leerzeilen am Ende entfallen. | `export/csv` |
| `@flowaudit/common` | `parseDateInput` | Funktion | Eingabe → `Date` oder `null`. Reine Datumswerte `JJJJ-MM-TT` werden als lokale Mitternacht gelesen (nicht wie `new Date('JJJJ-MM-TT')` als UTC), damit sie in keiner Zeitzone auf de … | `format/date` |
| `@flowaudit/common` | `parseDecimal` | Funktion | Zahleneingabe → `number`; sonst `null`. Für Beträge mit Rechenbedarf `parseDecimalString` bevorzugen. | `parse/number` |
| `@flowaudit/common` | `parseDecimalResult` | Funktion | Liest eine Zahleneingabe und nennt bei Ablehnung den Grund (`empty`, `ambiguous`, `invalid`, `negative`). | `parse/number` |
| `@flowaudit/common` | `parseDecimalString` | Funktion | Zahleneingabe → Dezimal-String (`"1234.56"`) ohne Rundungsverlust; sonst `null`. | `parse/number` |
| `@flowaudit/common` | `parseNumber` | Funktion | Zelle → Zahl mit ausdrücklichem Dezimaltrenner; der jeweils andere Trenner gilt als Tausenderpunkt. Leer ergibt `null` (fehlend), Unlesbares `undefined`. | `parse/table` |
| `@flowaudit/common` | `parseTable` | Funktion | Text → Tabelle. `hasHeader` legt fest, ob die erste Zeile Spaltennamen enthält; sonst heißen die Spalten „Spalte 1“, „Spalte 2“ … | `parse/table` |
| `@flowaudit/common` | `poll` | Funktion | Ruft `fn` im Intervall auf, bis `until` erfüllt ist; liefert das letzte Ergebnis. Fehler verlängern bei `backoff` den Abstand; nach `maxAttempts` wird der letzte Fehler geworfen. | `timing` |
| `@flowaudit/common` | `recordsToCsv` | Funktion | CSV aus Datensätzen über deklarative Spalten. | `export/csv` |
| `@flowaudit/common` | `requestFile` | Funktion | POST mit Dateiantwort; der Dateiname kommt aus `Content-Disposition`. | `http/rest` |
| `@flowaudit/common` | `requestJson` | Funktion | GET/POST mit JSON-Antwort. Der Antworttyp ist der dokumentierte REST-Vertrag. | `http/rest` |
| `@flowaudit/common` | `roundHalfUp` | Funktion | Rundet eine Dezimalzeichenkette half-up auf `digits` Nachkommastellen (Ergebnis wieder als Zeichenkette). | `format/decimal` |
| `@flowaudit/common` | `shortId` | Funktion | Kurze Kennung mit Präfix für DOM-IDs und Schlüssel (`fa-3k9x2m`); nicht kryptografisch. | `ids` |
| `@flowaudit/common` | `slugify` | Funktion | URL-/Dateinamen-Kennung: Kleinbuchstaben, Ziffern und `-`; deutsche Sonderzeichen werden umschrieben. | `text` |
| `@flowaudit/common` | `sortRows` | Funktion | Stabile Sortierung einer Kopie; die Eingabe bleibt unverändert. | `table/sort` |
| `@flowaudit/common` | `splitLine` | Funktion | Eine Zeile mit Anführungszeichen nach RFC 4180 (doppelte "" als Maskierung). | `parse/table` |
| `@flowaudit/common` | `throttle` | Funktion | Führt `fn` höchstens alle `ms` aus: sofort beim ersten Aufruf, danach einmal am Ende des Fensters. | `timing` |
| `@flowaudit/common` | `toCsv` | Funktion | Ganze Datei aus Zeilen (erste Zeile = Kopf); jede Zeile endet mit dem Zeilenende. | `export/csv` |
| `@flowaudit/common` | `toFiniteNumber` | Funktion | Zahl aus `number` oder Dezimal-String (`"1234.5"`, Backend-Decimal); sonst `null`. | `format/locale` |
| `@flowaudit/common` | `toIsoDate` | Funktion | Kalendertag `JJJJ-MM-TT` eines Zeitpunkts in der Anzeigezeitzone (Standard Berlin); `null` bei ungültig. | `format/date` |
| `@flowaudit/common` | `toPlainDecimal` | Funktion | Dezimalzeichenkette ohne Exponent (`1e-7` → `0.0000001`); `null` bei nicht endlichen Zahlen. | `format/decimal` |
| `@flowaudit/common` | `truncate` | Funktion | Kürzt auf höchstens `max` Zeichen (Codepunkte) inklusive Auslassungszeichen. | `text` |
| `@flowaudit/common/browser` | `DownloadOptions` | Schnittstelle | Optionen für `downloadBlob`. | `browser/download` |
| `@flowaudit/common/browser` | `ElementSource` | Typ | Element oder Getter (z. B. Template-Ref), zum Zeitpunkt des Klicks ausgewertet. | `browser/dom` |
| `@flowaudit/common/browser` | `SafeStorage` | Schnittstelle | Abgesicherte JSON-Ablage; Fehler ergeben den Rückfallwert. | `browser/storage` |
| `@flowaudit/common/browser` | `SafeStorageOptions` | Schnittstelle | Präfix, Version und Speicherart für `safeStorage`. | `browser/storage` |
| `@flowaudit/common/browser` | `copyText` | Funktion | Kopiert Text in die Zwischenablage (Clipboard-API, sonst Textfeld-Rückfall); `true` bei Erfolg. | `browser/clipboard` |
| `@flowaudit/common/browser` | `downloadBlob` | Funktion | Blob unter einem Dateinamen speichern, optional mit Datumspräfix. | `browser/download` |
| `@flowaudit/common/browser` | `matchesMediaQuery` | Funktion | Aktueller Stand einer Media-Query; ohne `matchMedia` (SSR, Tests) `false`. | `browser/dom` |
| `@flowaudit/common/browser` | `onClickOutside` | Funktion | Ruft `handler` bei Zeiger-Klick außerhalb aller Elemente und bei Escape (`escape: true`, Standard); gibt die Abmeldung zurück. | `browser/dom` |
| `@flowaudit/common/browser` | `safeStorage` | Funktion | Abgesicherte JSON-Ablage (`localStorage` oder `sessionStorage`). | `browser/storage` |
| `@flowaudit/common/browser` | `saveFile` | Funktion | Bietet eine Datei im Browser zum Speichern an. | `browser/download` |
| `@flowaudit/common/browser` | `subscribeMediaQuery` | Funktion | Abonniert eine Media-Query (`(prefers-color-scheme: dark)`, `(max-width: 768px)`); gibt die Abmeldung zurück. | `browser/dom` |
<!-- api-overview:end -->

## Konfiguration

Festlegungen aus [`contracts/common-cases/decisions.json`](../../contracts/common-cases/decisions.json)
sind die Standardwerte; jede Funktion lässt sie über Optionen ändern:

| Festlegung | Standard | Option |
|---|---|---|
| Ersatzwert für leer/ungültig | `EMPTY_VALUE` = „—“ | `empty` |
| Anzeigezeitzone | `DISPLAY_TIME_ZONE` = `Europe/Berlin`; reine Datumswerte ohne Umrechnung | `timeZone` |
| Sprache | `de` (`de-DE`), alternativ `en` (`en-GB`) | `locale` |
| Beträge | 2 Nachkommastellen, kaufmännisch (half-up), U+00A0 vor „€“ | `digits`, `cents`, `currency` |
| Dateigröße | Basis 1024, `B/KB/MB/GB/TB`, höchstens eine Nachkommastelle mit Komma | `digits` |
| Zahleneingabe | `strict-de`: höchstens 2 Nachkommastellen, „1.5“/„1.234“/„1,234“ mehrdeutig | `mode` (`strict-de`, `strict-en`, `auto`), `maxFractionDigits`, `allowNegative`, `stripCurrency` |
| CSV | „;“, BOM, CRLF, Dezimalkomma, Präfix „'“ vor `= + - @` Tab CR | `delimiter`, `bom`, `decimal`, `guardFormulas`, `lineEnding` |
| Token | `localStorage`, Schlüssel `flowaudit_token` | `createTokenStore({ key, storage })` |
| Toasts | 4 s, Fehler 8 s, höchstens 5 | `createToastQueue({ defaultMs, errorMs, max })` |

Keine Umgebungsvariablen.

## Herkunft und Charakterisierung

Neu in auditcore aus der Inventur der App-Frontends
([`app-helfer-ts.md`](../../docs/reports/app-helfer-ts.md): 140 Datums-,
64 Betrags-, 45 Dateigrößen-Formatierer, 17 Zahlenparser, 51
Fehlertext-Varianten). Die Regeln sind nicht aus einer App kopiert, sondern
aus den **gemeinsamen Vertragsfällen**
[`contracts/common-cases/*.json`](../../contracts/common-cases/) abgeleitet,
gegen die auch die Python-Referenz (`auditcore.tools.helpers`) und die
Helfer-Verträge der Anwendungen laufen. `test/contracts.spec.ts` liest die
JSON-Dateien direkt, verlangt eine Bindung für jeden TypeScript-Vertrag und
besteht alle TypeScript-Fälle (165 Fälle in 11 Verträgen, darunter 48
Betragsfälle aus flowinvoice `german-amount-cases.json`) in der
Prüfzeitzone `America/New_York`. Der Modus `strict-de` folgt der strikten
Betragsauslegung von flowinvoice (`german-decimal.ts`).

Aus `@flowaudit/ui` 0.1.0 unverändert übernommen: `i18n/format.ts` (jetzt
`intlFormat*` und `localeTag`), `rest/client.ts` (jetzt `http/rest`),
`table/sort.ts` und `tabular/parse.ts` (jetzt `parse/table`), `saveFile`.
Ergänzt wurden dabei nur abwärtskompatible Erweiterungen (siehe
[CHANGELOG.md](CHANGELOG.md)).

## Abhängigkeiten

Keine Laufzeitabhängigkeiten (weder `dependencies` noch
`peerDependencies`). Node ≥ 20.19 für Bau und Tests; im Browser eine
ES2022-Umgebung mit `Intl` (inklusive Zeitzonendaten) und `fetch`
(injizierbar).

## Sicherheit und Datenschutz

- **HTML:** Das Paket erzeugt kein HTML; `escapeHtml` maskiert die fünf
  Sonderzeichen für eigene Ausgaben.
- **CSV-Injektion:** `escapeCsvCell`/`toCsv` setzen „'“ vor Texte, die mit
  `= + - @` Tab oder CR beginnen (Standard, abschaltbar); Zahlen bleiben
  Zahlen.
- **Netzwerk:** nur `requestJson`/`requestFile` an die übergebene `baseUrl`
  mit den übergebenen Kopfzeilen; `fetch` ist injizierbar.
- **Token:** `createTokenStore` legt das Token im gewählten Speicher ab
  (`localStorage` ist per XSS lesbar; `memory` oder `session` wählen, wo das
  nicht passt). `jwtPayload`/`jwtExpiry` prüfen **keine Signatur** und
  dienen nur der Anzeige und Ablaufsteuerung; verbindlich entscheidet der
  Server.
- **Browser-Speicher:** `safeStorage` speichert nur, was die Anwendung
  übergibt, mit Präfix und Version; Fehler (gesperrt, voll) ergeben den
  Rückfallwert.
- **Kennungen:** `newId` nutzt `crypto.randomUUID`/`getRandomValues`, ohne
  sie `Math.random` – nicht für Geheimnisse verwenden.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Neu entwickelt; die aus `@flowaudit/ui` verschobenen Module
stammen aus demselben Repository (MIT). Kein Fremdcode.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
