# Excel-Funktionen der Vorlage

Inventar über alle 25 Blätter (1.299 Zellen mit Formel, Verknüpfungen
eingeschlossen), erzeugt mit
`node scripts/generate-definition.mjs --inventory`. Die Rechenkerne bilden die
Formeln von Hand nach; es gibt keine Formel-Engine. Die rechte Spalte nennt
die Entsprechung in `src/excel/index.ts` (im Paket als `excel.*` exportiert).

| Funktion | Vorkommen | Entsprechung |
|---|---:|---|
| `IFERROR` | 1197 | `guard(() => …)`: Fehlerwert → `null` für `IFERROR(…;"")`; `ifError(() => …, ersatz)` für innere Ersatzwerte wie `IFERROR(D51/D9;1)` |
| `IF` | 1055 | `if` / bedingter Ausdruck |
| `N` | 577 | `n(x)`: Leerwert und Text → 0 |
| `ROUNDUP` | 195 | `roundUp(x, stellen)`: kürzt wie die Tabellenkalkulation auf zwölf signifikante Stellen und rundet dann auf (gemessen) |
| `MAX` | 125 | `Math.max` bei Zahlen, `max(bereich)` über Zellbereiche |
| `SUM` | 110 | `sum(bereich)` |
| `LEFT` | 97 | `left(text, n)` |
| `OR` | 93 | `\|\|` |
| `ISNUMBER` | 47 | `isNumber(x)` |
| `SQRT` | 36 | `squareRoot(x)` (`#ZAHL!` bei negativem Wert) |
| `MIN` | 18 | `Math.min` bzw. `min(bereich)` |
| `COUNT` | 17 | `count(bereich)` |
| `AND` | 14 | `&&` |
| `INDEX` / `MATCH` | 10 / 10 | `zValue(parameters, niveau, testart)` für die z-Tabelle; allgemein `indexOf`, `matchExact` |
| `INDIRECT` | 8 | entfällt: Blatt 18 liest die Ergebnisübersicht des gewählten Methodenblatts aus dem Kontext (`context.method`, `summaryOf`) |
| `ABS` | 3 | `Math.abs` |
| `SEARCH` | 2 | `search(teil, text)` |
| `SUMIF` | 1 | `sumIf(bereich, kriterium, werte)` |

Operatoren:

| Vorlage | Rechenkern |
|---|---|
| `=`, `<>`, `<`, `<=`, `>`, `>=` zwischen Zahlen | `eq`, `ne`, `lt`, `le`, `gt`, `ge` – mit der Toleranz der Tabellenkalkulation (2⁻⁴⁸ relativ); rohe Vergleiche sind in `src/sheets` per Lint-Regel gesperrt |
| `=`/`<>` mit Text | `sameText` (ohne Groß- und Kleinschreibung); Auswahl mit Zahlenwert: `sameNumber` |
| `-`, `+` zwischen Beträgen | `minus`, `plus`: Differenz fast gleicher Werte ist 0 |
| `^` (156 Formeln) | `**` |
| `&` (9) | Zeichenkette |

Ein Text ist im Größenvergleich größer als jede Zahl; wo eine Formel davon
abhängt, steht es im Rechenkern als Kommentar (`assessment` in
`src/sheets/shared/statistical.ts`).

Vergleiche und Aufrunden sind an LibreOffice 24.2 gemessen
(`scripts/measure_semantics.py`, Messwerte in
`test/fixtures/libreoffice-semantik.json`, geprüft in `test/excel.spec.ts`).
Microsoft Excel ist nicht gegengeprüft ([abweichungen.md](abweichungen.md) Nr. 3).

## Leerwerte

| In der Vorlage | Im Rechenkern |
|---|---|
| leere Eingabezelle | `null` |
| `""` aus `IFERROR(…;"")` | `null` |
| leere Zelle in einer Rechnung (zählt als 0) | `required(x)` löst einen Fehlerwert aus → `null`, „Angabe fehlt“ ([abweichungen.md](abweichungen.md)) |
| `N(leer)` | `n(x)` = 0, wie in der Vorlage |
| Division durch 0, Wurzel aus negativer Zahl | `divide`, `squareRoot` lösen einen Fehlerwert aus → `null` |
