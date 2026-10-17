# Ein Blatt ergänzen

Anleitung für das Nachbauen weiterer Blätter der Vorlage. Sie ist so
geschrieben, dass eine Blattgruppe ohne Rückfrage gebaut werden kann. Es gilt:
**Vorlage vor Auftragsbeschreibung vor eigenen Annahmen.** Keine Formel raten,
keine Rundung, Schwelle oder Rechenreihenfolge ändern.

## Was vorhanden ist

Alle Blätter der Vorlage sind gebaut. Als Muster eignen sich:

| Blatt | Art | Muster für |
|---|---|---|
| `02_Grundgesamtheit` | Ableitung der Grundgesamtheit | Blätter ohne Stichprobe, Lieferant für Verknüpfungen |
| `03_MUS_1Z` | statistisch, ein Zeitraum, ungeschichtet | alle Methodenblätter |
| `04_MUS_1Z_S` | statistisch, ein Zeitraum, geschichtet | Schichtzeilen, Werte ohne Grundlage |
| `10_SRS_2Z`, `05_MUS_2Z` | mehrere Zeiträume | `computeTwice`, Neuberechnung |
| `13_NS_GW` | nichtstatistisch | Blätter ohne Genauigkeit |
| `17_Unterstichprobe` | Liste je Stichprobeneinheit | Listenblätter |
| `18_GFQ_AnhIII` | Übernahme aus dem aktiven Verfahren | Bezüge über `context.method` |
| `X3_DiffSch_S_2017` | Altvorlage, Schichten in E–K | abweichender Aufbau |

Gemeinsam vorhanden: Excel-Semantik (`src/excel`), Richtlinie für fehlende
Angaben (`src/model/policy.ts`, `src/model/evaluate.ts`), Schichthelfer
(`src/model/strata.ts`, Erläuterung in
[schichten-und-listen.md](schichten-und-listen.md)), Listenmechanik
(`src/model/list.ts`), wortgleiche Formeln je Blattgruppe unter
`src/sheets/shared/` (`statistical.ts` für 03–12, `periods.ts` für mehrere
Zeiträume, `mus.ts`, `srs.ts`, `nonstatistical.ts`, `legacy.ts`),
Kontextfluss zwischen den Blättern, Schichttabelle, Liste und Bericht in der
Oberfläche, englische Arbeitsübersetzung je Blatt (`texts.en.ts`).

## Wer was ändert

Alle Gruppen arbeiten im selben Arbeitsverzeichnis. Zu jedem Blatt gehört
dieser Satz Dateien – **und nur er wird geändert**:

| Datei | Inhalt |
|---|---|
| `src/sheets/<Blatt>/index.ts` | `export const sheet = defineSheet({ … })` (ersetzt den Platzhalter `plannedSheet`) |
| `src/sheets/<Blatt>/definition.ts` | Methodendefinition |
| `src/sheets/<Blatt>/compute.ts` | Rechenkern |
| `src/sheets/<Blatt>/deviations.ts` | begründete Abweichungen |
| `src/sheets/<Blatt>/texts.en.ts` | englische Arbeitsübersetzung (optional, Muster Blatt 03) |
| `src/sheets/<Blatt>/*.ts` | **weitere Module nach Bedarf** – ein Blatt mit vielen Formeln teilt Definition und Rechenkern auf (`definition-strata.ts`, `compute-periods.ts` …), damit jede Datei unter 400 Zeilen bleibt |
| `src/sheets/shared/<gruppe>.ts` | Formeln, die mehrere Blätter **der eigenen Gruppe** teilen (`mus.ts`, `srs.ts`, `nonstatistical.ts`, `legacy.ts`); jede Gruppe ändert nur ihre Datei |
| `test/cases/<Blatt>.json` | Testfälle: Liste aus `{ "name", "blatt", "eingaben" }` |
| `test/cases/<Blatt>.<name>.json` | weitere Fallsätze, z. B. `.zufall` (optional) |
| `test/golden/<Blatt>[.<name>].golden.json` | erwartete Werte, nur mit dem Werkzeug erzeugt |
| `test/<blatt>.spec.ts` | eigene Tests des Blatts (optional) |

`<Blatt>` ist der Blattname der Vorlage (`05_MUS_2Z`).

**Nicht ändern:** `src/sheets/registry.ts` (kennt alle Blätter bereits),
`src/sheets/shared/statistical.ts`, `src/sheets/01_Parameter`, die fertigen
Blätter 02, 03, 04, 17, `src/excel`, `src/model`, `src/workspace`, `src/view`,
`src/xlsx`, `src/catalog`, `src/format`, `src/i18n`, `styles/`, die
allgemeinen Tests (`test/golden.ts`, `golden.spec.ts`, `deviations.spec.ts`,
`catalog.spec.ts`, `docs.spec.ts`, `sheets.ts` …), `test/fixtures`, das
Vue-Paket, `eslint.config.mjs`, `package.json`, `package-lock.json`. Die
allgemeinen Tests erfassen ein Blatt von selbst, sobald es verfügbar ist.

**Nicht erzeugen:** `docs/abgleich.md` und die Tabelle in
`docs/abweichungen.md` (`npm run docs:write`) sowie `README.md`,
`CHANGELOG.md`, `PROVENANCE.md`. Das zieht die zusammenführende Stelle am Ende
einmal nach; sonst überschreiben sich die Gruppen gegenseitig. Fehlt in einem
gemeinsamen Baustein etwas, steht es im Abschlussbericht der Gruppe – nicht
selbst einbauen.

**Platzhalter erst ersetzen, wenn das Blatt übersetzt und abgleicht.** Solange
`index.ts` `plannedSheet(...)` exportiert, sehen die anderen Gruppen ein
unverändertes Register. Ein halbfertiges `defineSheet` lässt die allgemeinen
Tests aller Gruppen scheitern.

## Vorlage bereitstellen

Die Arbeitsmappe und `vorlage_zellen.json` liegen nicht im Repository.

```sh
export AUDITCORE_SAMPLING_TEMPLATES_DIR=/pfad/zum/materialordner/referenz
```

Alternativ beide Dateien nach `packages-js/sampling-templates-core/.vorlage/`
kopieren (von git ausgeschlossen). Niemals in einen versionierten Pfad legen.
Für die Golden-Erzeugung braucht es LibreOffice (`soffice`) und `openpyxl`.

## Schritte

Alle Befehle aus dem Verzeichnis `packages-js/sampling-templates-core`.

### 1. Formeln lesen

Im Materialordner `referenz/formeln/<Blatt>.md`: Zelle, Art (eingabe,
verknuepfung, formel, ergebnis), Formel, Format, Auswahlliste.

### 2. Definition erzeugen und prüfen

```sh
node scripts/generate-definition.mjs 05_MUS_2Z > "$TMPDIR/05.ts"
```

Der Entwurf nennt ein Feld je Zeile; Schichtzeilen tragen
`columns: STRATA_COLUMNS` und `total: 'C<Zeile>'`. Nach `definition.ts`
übernehmen und von Hand prüfen:

- `alias`: englischer, sprechender Name je Zelle, eindeutig im Blatt; gleiche
  Größen heißen wie in Blatt 03 bzw. 04 (`sampleSize`, `bookValue`).
- `label` und `hint` wörtlich aus der Vorlage (Spalte B; Fundstelle in
  Spalte D, bei geschichteten Blättern K). Steht in der Bezeichnung eine
  Formel, wandert sie nach `formula`.
- `kind` wie die Art der Vorlage, `type` nach Zahlenformat; Prüfhinweise
  haben `type: 'check'`.
- `list` für Auswahllisten aus Blatt 01, `default` für Vorgaben, `link` für
  Verknüpfungen.
- `interpretation: '<Erläuterung>'`, wo die Hinweisspalte der Vorlage einen
  Punkt als Auslegung kennzeichnet (Blatt 00, Zeile 52). Der Text erscheint in
  Formular, Schichttabelle und Excel-Export unter „Auslegung der Vorlage“.
- `subsample: 'highValueErrors' | 'errorRateSum' | 'errorSum' | 'bookValueSum'`
  an den Eingaben, in die Summen aus Blatt 17 übernommen werden; bei
  Schichtzeilen erfolgt die Übernahme je Schicht, mit `period: 1 | 2 | 3` je
  Stichprobenzeitraum.
- `summary.gauge`: Skala gegen die Signifikanzschwelle; `upper` entfällt,
  wo es keine obere Fehlergrenze gibt, `rateLabel`/`upperLabel` tragen die
  Begriffe des Blatts, wenn sie abweichen (Altvorlagen).
- `summary`: Hauptgröße, Kennzahlen und Skala der Ergebnisspalte.
- Die Zellen M/N der Ergebnisübersicht gehören nicht in die Definition.

### 3. Rechenkern schreiben

`compute(inputs, context)` beginnt mit
`resolveInputs(definition, inputs, context)` und weist jede Formelzelle einmal
zu, in Blattreihenfolge, gegliedert nach Abschnitten (Funktionen höchstens 60
Zeilen, Komplexität höchstens 10).

| Vorlage | Rechenkern |
|---|---|
| `=IFERROR(A*B;"")` | `c.X = guard(() => required(c.A) * required(c.B))` |
| `IFERROR(D51/D9;1)` innerhalb einer Formel | `ifError(() => divide(required(c.D51), required(c.D9)), 1)` |
| `N(A)` | `n(c.A)` |
| `ROUNDUP(x;0)` | `roundUp(x)` |
| `A/B` | `divide(a, b)` |
| `A-B`, `A+B` zwischen Beträgen, deren Ergebnis verglichen oder geteilt wird | `minus(a, b)`, `plus(a, b)` |
| `SQRT(x)` | `squareRoot(x)` |
| `A>B`, `A>=B`, `A<B`, `A<=B`, `A=B`, `A<>B` (Zahlen) | `gt`, `ge`, `lt`, `le`, `eq`, `ne` |
| `A="Ja"` (Text) | `sameText(c.A, 'Ja')` |
| `A=2` (Auswahl mit Zahlenwert) | `sameNumber(c.A, 2)` |
| `LEFT($C$28;8)="Standard"` | `sameText(left(c.C28, 8), 'Standard')` |
| `IF(A="";"";…)` | `isBlank(c.A) ? null : …` bzw. `isNumber` |
| `SUM(D9:J9)` | angezeigte Summe einer Schichtzeile: `totalRow(c, 9, context)`; Zwischenrechnung: `sumRow(c, 9)`; sonst `sum([...])` |
| `MAX(a;b)`, `MIN(a;b)` mit Zahlen | `Math.max`, `Math.min` |
| `MAX(D9:J9)`, `MIN(…)`, `COUNT(…)` über Bereiche | `max`, `min`, `count` – sie übergehen Leer- und Textwerte wie Excel |

Regeln, die der Abgleich nicht von selbst erzwingt:

- **Vergleiche nur über die Helfer.** Excel vergleicht nach Rundung beider
  Seiten auf 15 geltende Stellen; `>`, `<`, `>=`, `<=` und `===` gegen Zahlen sind in
  `src/sheets` deshalb per Lint-Regel gesperrt. Schwellen wie „≤ 2 %“ oder
  „TE > AE“ fallen sonst bei glatten Werten anders aus als in der Vorlage.
- **Aufrunden nur mit `roundUp`.** Es bildet das gemessene Verhalten nach
  von Excel (Rundung auf 15 geltende Stellen, dann aufrunden). Die
  Schichtverteilung `ROUNDUP(D9/C9·C33)` trifft besonders oft glatte Werte.
- **Differenzen mit `minus`**, wenn die Subtraktion die letzte Operation der
  Formel ist: Excel setzt ein Ergebnis, das 50 Binärstellen unter dem
  kleineren Summanden liegt, auf 0.
- **`MAX`/`MIN` mit einer leeren Zelle als Argument:** Als Einzelargument
  zählt die leere Zelle 0 (`Math.max(n(c.A), 30)`), in einem Bereich wird sie
  übergangen (`max([...])`). Ein Text als Einzelargument ist ein Fehlerwert:
  `required(c.A)` innerhalb von `guard`.
- **Ein Text ist im Größenvergleich größer als jede Zahl.** Hängt eine Formel
  davon ab (Würdigung mit leerer oberer Fehlergrenze), steht es als Kommentar
  im Rechenkern; Muster `assessment` in `shared/statistical.ts`.
- Rechenreihenfolge wie in der Formel (Gleitkomma ist nicht assoziativ).
  Prüfhinweistexte wortgleich, mit ✔/⚠/✖.
- Methodenblätter füllen die Ergebnisübersicht N3–N11.
- Keine Abkürzungen über andere Blätter: Was von außen kommt, steht im
  Kontext (`context.sheets['02_Grundgesamtheit']?.C51`).

**Wortgleiche Formeln nicht abschreiben.** Für die Blätter 03–12 liegen in
`shared/statistical.ts`: `checkConfidence`, `checkMateriality`,
`checkTolerableError`, `computedSampleSize`, `isSizePending`,
`limitedSampleSize`, `appliedSampleSize`, `checkMinimumUnits`,
`checkIteration`, `lowerErrorLimit`, `assessment`. Vor der Verwendung die
Formel der eigenen Zelle gegen die Funktion lesen; weicht sie ab (anderer
Text, andere Bedingung), gehört die Variante in die Datei der eigenen Gruppe,
nicht in `statistical.ts`.

### 4. Schichtzeilen (Blätter 06, 09, 11, 14, 16, X3)

Muster ist `04_MUS_1Z_S/compute.ts`. Eine Schichtzeile hat je Schicht eine
Zelle `<Spalte><Zeile>`; die Spalten der Vorlage sind D–J (`TEMPLATE_STRATA`),
die Webfassung führt die 8. bis 20. Schicht unter AA–AM (`EXTRA_STRATA`),
zusammen `STRATA_COLUMNS`. Die Vorlage hat zu AA–AM keine Zellen; Golden deckt
D–J ab, die Erweiterung prüft `test/strata.spec.ts` am Muster von Blatt 04
(eigener Test je geschichtetem Blatt: dieselben Werte in Spalte D und in
Spalte AA ergeben dieselben Ergebnisse).

```ts
import { countRow, fillRow, stratumCell as at, totalRow } from '../../model/strata'

// =IF(D9="";"";IFERROR(ROUNDUP(D9/$C$9*$C$33;0);""))  – je Schichtspalte
const used = (column: string): boolean => !isBlank(c[at(column, 9)])
fillRow(c, 35, (column) => (used(column) ? guard(() => roundUp(divide(required(c[at(column, 9)]), required(c.C9)) * required(c.C33))) : null))

// =SUM(D9:J9)  – Summe über alle Schichtspalten; ohne Summanden ein Wert ohne Grundlage
c.C9 = totalRow(c, 9, context)

// =COUNT(D46:J46)
const filled = countRow(c, 46)
```

- **Leere Schichtspalte:** `IF(D9="";"";…)` → `null`; die Spalte erscheint in
  der Oberfläche nicht. Hilfszeilen, in denen die Vorlage für die leere Spalte
  0 liefert (Zeile 52 in Blatt 04), liefern auch hier 0.
- **Summen, die vom Stichprobenumfang abhängen**, bleiben offen, solange der
  Umfang offen ist (`const total = (row) => (pending ? null : totalRow(c, row, context))`).
- **Summe ohne Summanden:** `totalRow` liefert sie als Wert ohne Grundlage
  (Abschnitt 6); die Summenzelle und alle Zellen, die auf ihrer 0 aufbauen,
  stehen mit `kind: 'withoutBasis'` in den Abweichungen (Muster `emptyTotal`
  und `withoutTotal` in `04_MUS_1Z_S/deviations.ts`).
- **Mindestens drei Einheiten je Schicht:** `checkStratumUnits(units, open, context)`.
- **Definition:** `columns: STRATA_COLUMNS`, `total: 'C<Zeile>'`; die
  Summenzelle ist kein eigenes Feld.
- **Abweichungen** je Zeile mit Spaltenmuster über alle Schichtspalten des
  Blatts, nicht je Zelle von Hand: `STRATA_COLUMNS.map((column) => stratumCell(column, 25))`;
  die erzeugte Tabelle fasst sie zu `D25–J25, AA25–AM25` zusammen. Belegt sein
  muss die Abweichung durch einen Fall in einer Schichtspalte.
- **Hinweise der Webfassung**, die eine Schicht betreffen, nennen ihre Nummer.

### 5. Mehrere Zeiträume (05, 06, 07, 10, 11, 12, X4)

- Jeder Zeitraum hat eigene Zellen; die Definition bildet sie als eigene
  Abschnitte ab (Überschriften der Vorlage).
- **Neuberechnung des Stichprobenumfangs:** Die Vorlage verzweigt über die
  Auswahl in Blatt 01 (`LEFT(…;8)="Standard"` gegen „global“). Beide Zweige
  bauen und mit je eigenen Fällen abgleichen.
- **Negativer Nenner:** Die Prüfung der Vorlage (Text mit ✖) wortgleich
  übernehmen; Folgezellen liefern dann, was die Vorlage liefert (`""` bzw.
  den Fehlerwert über `guard`).
- **Erhöhung bei begrenztem Umfang** und jede andere Stelle, die die
  Hinweisspalte als Auslegung kennzeichnet: `interpretation: true`.
- Gemeinsame Formeln der Zeiträume liegen in der Datei der eigenen Gruppe und
  nehmen die Zellen als Argumente, wie `computedSampleSize`.
- Die Ergebnisübersicht N3–N11 fasst die Zeiträume so zusammen, wie die
  Vorlage es in M/N tut.

### 6. Fehlende Angaben

Die Webfassung zeigt nie einen anderen Wert als die Vorlage, höchstens keinen.
Was sie zeigt, wenn eine Angabe fehlt, entscheidet **eine** Stelle:
`src/model/policy.ts` (Richtlinie je Fallart) über `evaluateSheet`. Ein Blatt
ordnet nur jede Stelle einer Fallart zu und liest die Richtlinie nie selbst
([abweichungen.md](abweichungen.md) Nr. 1):

| Fallart | Wann | Was das Blatt tut |
|---|---|---|
| `requiredInput` | Pflichteingabe fehlt, die Vorlage rechnet mit 0 weiter – auch voraussichtliche Standardabweichungen und alle Größen der Planung und Neuberechnung, selbst wenn die Vorlage sie mit `N(…)` liest | `required(...)` in `guard` → `null`; Zeile in `deviations.ts` ohne `kind` |
| `sampleDeviation` | Standardabweichung der Stichprobe in der Auswertung fehlt (nur die Genauigkeit wird 0) | wie die Vorlage mit 0 rechnen; `zeroAssumed` meldet `{ input, cells }` |
| `partialErrorSum` | Fehlersumme einer von mehreren belegten Schichten bzw. eines von mehreren Zeiträumen fehlt, eine andere ist eingetragen | wie die Vorlage mit 0 rechnen; `zeroAssumed` meldet `{ input, cells, kind: 'partialErrorSum' }` |
| `withoutBasis` | Die Vorlage zeigt einen Wert ohne Grundlage: „✔“, obwohl die geprüfte Größe leer oder ein Text ist; Summe 0 über Schichten ohne Wert und alles, was darauf aufbaut | `unfounded(context, wert)` bzw. `totalRow(…, context)`; Zeile in `deviations.ts` mit `kind: 'withoutBasis'` |

Freiwillige Einzelbeträge, die die Vorlage mit `N(…)` liest (Fehler der
hochwertigen Einheiten, systembedingte und anomale Fehler), zählen still 0.

```ts
// Pflichteingabe
{ cell: 'C16', whenEmpty: ['C7', 'C14'], template: '0,00 € (leere Zelle zählt als 0)', reason: 'Der zulässige Fehler setzt Buchwert und Signifikanzschwelle voraus.' }

// Wert ohne Grundlage
c.D41 = used ? checkStratumUnits(c.D40, pending, context) : null
{ cell: 'D41', whenEmpty: ['D40'], template: '„✔ ≥ 3“ (leere Textzelle ist im Vergleich größer als jede Zahl)', reason: '…', kind: 'withoutBasis' }

// mit 0 gerechnet und ausgewiesen
function zeroAssumed(results: CellMap): ZeroAssumption[] {
  if (!isBlank(results.C39) || !isNumber(results.C43)) return []
  return [{ input: 'C39', cells: ['C43', 'C46', 'C47', 'C48', 'C51', 'C52'] }]
}
```

- `whenEmpty` nennt **genau** die Eingaben, deren Fehlen die Abweichung
  auslöst – bei `withoutBasis` die fehlende Größe (eine Zelle, die dann leer
  ist). Eingaben anderer Blätter heißen `'02_Grundgesamtheit!C51'`.
- **Gegenprobe im Abgleich:** `requiredInput` – mit 0 statt der leeren Eingaben
  liefert der Rechenkern den Wert der Vorlage; `withoutBasis` – unter
  `TEMPLATE_POLICY` liefert er ihn. Eine falsche Formel lässt sich so nicht
  hinter „Angabe fehlt“ verstecken. `check: 'none'` gibt es nur noch als
  Ausnahme mit Begründung im Abschlussbericht.
- **Beide Varianten müssen stimmen:** `test/golden.spec.ts` prüft die geltende
  Richtlinie (0 unbegründete Abweichungen), `test/policy.spec.ts` die Variante
  „wie die Vorlage“ (0 Abweichungen überhaupt).
- **Leeres Formular:** Kein berechneter Wert darf nur deshalb erscheinen, weil
  Eingaben fehlen – insbesondere nicht die Hauptgröße, N4, N5, N10, N11 und
  kein „✔“. Zulässig sind feste Texte, Hinweise zu gesetzten Vorgaben, feste
  Werte der Vorlage und freiwillige Einzelbeträge. Die Liste der Zellen, die
  beim leeren Formular einen Wert zeigen, steht ausdrücklich im Test des Blatts.
- `cells` in `zeroAssumed` nennt alle abhängigen Zellen (Genauigkeit,
  Fehlergrenzen, Würdigung; bei Schichten die Zelle der Schicht und die
  Gesamtwerte). Je solcher Eingabe ein Fall „alles ausgefüllt außer …“ und ein
  Test über `evaluateSheet` (Wert, `assumed`, `lacking`).

### 7. Werte aus anderen Blättern

- **Blatt 02 → Methodenblatt.** Die Verknüpfungen (BV, N) stehen als
  `kind: 'link'` mit `link: { sheet: '02_Grundgesamtheit', cell: 'C51' }` in
  der Definition. `resolveInputs` nimmt den eigenen (überschriebenen) Wert,
  sonst den aus `context.sheets['02_Grundgesamtheit']`. Ein leeres Blatt 02
  liefert keinen Wert, nicht 0.
- **Methodenblatt → Blatt 18.** Jedes Methodenblatt füllt N3–N11; Blatt 18
  liest sie aus `context.method` (`summaryOf`), nicht über `INDIRECT`.
- **Blatt 17 → Methodenblatt.** Per Knopf in die Eingaben mit `subsample`;
  das ist eine Eingabe dort, keine Verknüpfung.

### 8. Altvorlagen X1–X4

Der Generator liefert hier nur ein Gerüst, weil die Blätter keine farblich
gekennzeichneten Eingaben haben. Eingaben sind die leeren Zellen, auf die
Formeln verweisen; diese Ableitung im Kopf von `definition.ts` festhalten
(Zelle, verweisende Formeln). Bezeichnungen aus der Nachbarzelle der Vorlage;
fehlt eine, steht das im Abschlussbericht statt einer erfundenen Bezeichnung.
Fundstellen der Vorlage von 2017 unverändert übernehmen und als solche
belassen.

### 9. Fälle anlegen

`test/cases/<Blatt>.json`: Liste aus `{ "name": …, "blatt": "<Blatt>", "eingaben": { "C7": … } }`.
`"C24": null` leert eine Vorgabe; `"02_Grundgesamtheit!C25": 1000` schreibt in
ein anderes Blatt, der Abgleich rechnet dieses Blatt dann mit. Werte erfinden,
nie echte Prüfdaten.

| Blattart | Mindestabdeckung |
|---|---|
| alle | Standardfall; leeres Formular; je Pflichteingabe ein Fall „alles ausgefüllt außer …“; Werte genau auf jeder Schwelle (2 %, TE = AE, Konfidenzeckwerte) und knapp daneben; ein Fall mit Verknüpfung aus Blatt 02 und einer mit überschriebener Verknüpfung |
| statistisch (03–12) | jede Zuverlässigkeitsstufe und Testart; TE ≤ AE; begrenzter Umfang zulässig, unzulässig, mit Art. 83; rechnerischer Umfang genau auf einer ganzen Zahl; systembedingte und anomale Fehler; fehlende Standardabweichung der Stichprobe |
| MUS | weniger als drei Einheiten in der Zufallsschicht; Iteration; hochwertige Einheiten mit und ohne Fehler |
| geschichtet | eine, drei und sieben Schichten; leere Schicht zwischen belegten; Schichtumfänge, die beim Aufrunden die Summe über den Gesamtumfang heben; fehlende Angabe in nur einer Schicht |
| mehrere Zeiträume | Standard- und globale Neuberechnung; negativer Nenner; Zeitraum ohne Fehler; nur der erste Zeitraum ausgefüllt |
| nichtstatistisch (13–16) | N < 300; Mindesterfassung nach Anzahl und nach Ausgaben genau erreicht und knapp verfehlt; Prüfung der Gesamtfehlerquote |
| Altvorlagen | jede Verzweigung der Formeln mindestens einmal in jedem Zweig |

Mindestens 12 Fälle je Blatt, dazu der **Zufallsabgleich**: Der Abgleich
erklärt leere Zellen großzügig, deshalb braucht jedes Blatt mindestens 100
zufällig erzeugte, **vollständig ausgefüllte** Belegungen als eigenen Fallsatz
`test/cases/<Blatt>.zufall.json` (mit festem Startwert erzeugt, Werte im
fachlich möglichen Bereich, Auswahlfelder über alle Einträge). Für diese
Fälle muss jede Zelle ohne Abweichung stimmen.

```sh
node scripts/random-cases.mjs --liste                 # Blätter mit Startwert und Anzahl
node scripts/random-cases.mjs 05_MUS_2Z               # schreibt test/cases/05_MUS_2Z.zufall.json
node scripts/random-cases.mjs 05_MUS_2Z --anzahl 100 --start 2026101305 --ziel "$TMPDIR/05.json"
```

Die Belegung eines Blatts steht in `scripts/random-cases/sheets/` (je
Blattgruppe eine Datei), der Zufallsgenerator mit Startwert und die Hilfen für
Beträge, Anteile, Auswahlwerte und Schichten in `scripts/random-cases/core.mjs`.
Mit dem hinterlegten Startwert entsteht dieselbe Datei wieder; wer die
Belegung ändert, erzeugt danach die Golden-Datei neu.

### 10. Golden erzeugen

```sh
python3 scripts/golden_recalc.py test/cases/05_MUS_2Z.json test/golden/05_MUS_2Z.golden.json
python3 scripts/golden_recalc.py test/cases/05_MUS_2Z.zufall.json test/golden/05_MUS_2Z.zufall.golden.json
```

Das Werkzeug schreibt die Eingaben in eine Kopie der Vorlage, lässt
LibreOffice neu rechnen und liest alle Formelzellen aus. Es arbeitet in einem
eigenen Verzeichnis mit eigenem LibreOffice-Profil; mehrere Läufe gleichzeitig
sind möglich. Golden-Dateien nie von Hand ändern.

Maßgeblich sind seit Fassung 0.1.6 Sollwerte aus **Microsoft Excel**. LibreOffice
liefert nur einen vorläufigen Stand; es weicht an Schwellen (Vergleich), beim
Aufrunden, bei `VERGLEICH`, bei Wahrheits- und Fehlerwerten von Excel ab
([abweichungen.md](abweichungen.md) Nr. 3). Vor der Aufnahme eines Blatts sind
die Fälle über den Office-Dienst in Excel neu zu rechnen (Werkzeugkette der
Excel-Gegenprobe: Aufträge bauen, im Dienst rechnen, ins Golden-Format wandeln)
und die Excel-Werte als Golden-Dateien zu übernehmen.

### 11. Abgleichen

```sh
SAMPLING_TEMPLATES_SHEET=05_MUS_2Z SAMPLING_TEMPLATES_SKIP_DOCS=1 npx vitest run
SAMPLING_TEMPLATES_SHEET=05_MUS_2Z SAMPLING_TEMPLATES_REPORT="$TMPDIR/05.txt" npx vitest run test/report.spec.ts
```

- `SAMPLING_TEMPLATES_SHEET` beschränkt Golden-, Richtlinien- und
  Abweichungstests auf das eigene Blatt (mehrere mit Komma), damit halbfertige Blätter anderer Gruppen
  nicht stören.
- `SAMPLING_TEMPLATES_SKIP_DOCS=1` überspringt die Prüfung der erzeugten
  Nachweise (sie werden erst am Ende neu erzeugt).
- `SAMPLING_TEMPLATES_REPORT` schreibt jede abweichende Zelle mit Fall,
  Wert der Vorlage und Wert der Webfassung in eine Datei.

Für vollständige Belegungen muss jede Zelle stimmen (Zellen mit
Ganzzahlformat exakt, übrige auf 1e-9 relativ). Liefert der Rechenkern einen
**anderen Wert** als die Vorlage, ist der Rechenkern falsch – nie eine
Abweichung dafür eintragen.

### 12. Beispielwerte, Hinweise, Übersetzung

- `sample`: erfundene Beispielwerte, die ein vollständiges Ergebnis ergeben.
- `webHints`: Hinweise der Webfassung, wenn das Blatt welche braucht; sie
  verändern kein Ergebnis und nutzen die Vergleichshelfer.
- `texts.en.ts`: englische Arbeitsübersetzung der Bezeichnungen, Fundstellen
  und Prüfhinweise (Muster Blatt 03). Gespeicherte Werte bleiben deutsch.
  Ohne die Datei erscheint das Blatt auch in der englischen Oberfläche
  deutsch; das ist zulässig und steht dann im Abschlussbericht.

### 13. Im Browser ansehen

```sh
npm run demo -w @auditcore/sampling-templates-vue -- --port <eigener Port>
```

Blatt wählen, Beispielwerte laden, Speichern → Neu → Öffnen, Excel-Export
öffnen. Die Browsertests (`e2e/`) gehören dem Fundament und bleiben
unverändert; sie laufen mit festem Blattbestand.

## Fertig heißt

- [ ] `index.ts` meldet das Blatt mit `defineSheet` an; sonst nur Dateien des
      Blatts und der eigenen Gruppe geändert (`git status` ansehen).
- [ ] Jede Formelzelle des Blatts wird berechnet; jede Zelle der Definition
      kommt im Ergebnis vor, jeder Alias ist eindeutig.
- [ ] Fälle mit der Mindestabdeckung der Blattart und mindestens 100
      Zufallsbelegungen; 0 unbegründete Abweichungen; in den vollständigen
      Belegungen 0 Abweichungen überhaupt.
- [ ] Jede Zeile in `deviations.ts` ist durch einen Fall belegt, nennt genau
      die auslösenden Eingaben, trägt die richtige Fallart und besteht die
      Gegenprobe; `check: 'none'` nur mit Begründung.
- [ ] Variante „wie die Vorlage“ (`test/policy.spec.ts`): 0 Abweichungen.
- [ ] Leeres Formular zeigt keinen Wert ohne Grundlage (Test mit der Liste
      der zulässigen Zellen).
- [ ] Mit 0 gerechnete Eingaben: `zeroAssumed` meldet jede (mit Fallart), mit Test.
- [ ] Geschichtete Blätter: Test, dass Spalte AA wie Spalte D rechnet.
- [ ] Bezeichnungen, Fundstellen und Prüfhinweise wortgleich; Punkte der
      Auslegung gekennzeichnet.
- [ ] Beispielwerte erfunden; keine Dateien der Vorlage im Repository
      (`git status` zeigt weder `.xlsx` noch `vorlage_zellen.json`).
- [ ] `npx eslint packages-js/sampling-templates-core` (aus der Wurzel),
      `npx tsc --noEmit -p tsconfig.json` und die Tests des eigenen Blatts
      grün: Dateien höchstens 400 Zeilen, Funktionen höchstens 60,
      Komplexität höchstens 10, kein `any`, keine rohen Vergleiche.
- [ ] Im Browser angesehen.
- [ ] Abschlussbericht: Abgleichszahlen je Blatt (Fälle, Zellen, gleich,
      begründet, unbegründet), Liste der Eingaben mit „Angabe fehlt“ und
      ihrer Folge, Verwendungen von `check: 'none'`, fehlende gemeinsame
      Bausteine, offene Auslegungsfragen.

Nicht Aufgabe der Gruppe: committen, pushen, veröffentlichen, erzeugte
Nachweise und Paketdokumente fortschreiben.

## Zusammenführen

Wer die Arbeit mehrerer Gruppen zusammenführt, prüft den Gesamtstand und
erzeugt die Nachweise:

```sh
SAMPLING_TEMPLATES_SKIP_DOCS=1 npx vitest run                       # alle Blätter: Abgleich, Richtlinie, Abweichungen
npm run docs:write -w @auditcore/sampling-templates-core            # docs/abgleich.md, Tabelle in docs/abweichungen.md
```

Danach `README.md`, `CHANGELOG.md` und `PROVENANCE.md` fortschreiben
(Abgleichszahlen aus `docs/abgleich.md`) und die Prüfungen der Repo-Wurzel
ausführen.
