/**
 * Formeln, die in den Blättern 08–12 (einfaches Zufallsstichprobenverfahren,
 * Verhältnisschätzung) wortgleich vorkommen; nur die Zellbezüge unterscheiden
 * sich. Jedes Blatt ruft sie mit seinen Zellen auf. Was auch die MUS-Blätter
 * teilen (Prüfhinweise, rechnerischer Umfang, Würdigung), liegt in
 * `statistical.ts` und wird hier nur verwendet.
 */
import { divide, ge, guard, ifError, isBlank, isNumber, le, minus, n, required, roundUp } from '../../excel/index'
import { unfounded } from '../../model/policy'
import { STRATA_COLUMNS, stratumCell, sumRow, totalRow } from '../../model/strata'
import type { CellAddress, CellValue, Cells, SheetContext } from '../../model/types'
import { NOT_APPLICABLE, allocate, appliedPeriodSize, globalBlocked, type Pending } from './periods'
import { assessment, lowerErrorLimit } from './statistical'

export { INCREASE_INTERPRETATION, NOT_APPLICABLE, allocate, computeBesideTemplate, globalComputedSize, recalculationOf, share, weightedDeviation, type Pending, type Recalculation } from './periods'

/** Zelle in Spalte C. */
const at = (row: number): CellAddress => `C${row}`

/**
 * Mindestumfang der Zufallsstichprobe: `MAX(untergrenze;30-N(a)-N(b)…)`.
 * `floor` ist 3 je Stichprobenzeitraum (3, 6, 9); abgezogen werden die
 * Einheiten der umfassenden Schichten.
 */
export function minimumRandomSize(floor: number, ...exhaustiveUnits: readonly (CellValue | undefined)[]): number {
  return Math.max(floor, exhaustiveUnits.reduce<number>((rest, units) => rest - n(units), 30))
}

/** Begrenzter Umfang abzüglich hochwertiger Einheiten: `IF(n_lim="";"";n_lim-N(a)-N(b)…)`. */
export function netLimitedSize(limit: CellValue | undefined, ...highValueUnits: readonly (CellValue | undefined)[]): number | null {
  if (!isNumber(limit)) return null
  return highValueUnits.reduce<number>((rest, units) => rest - n(units), limit)
}

/**
 * Anzuwendender Umfang der Zufallsstichprobe:
 * `IF(netto<>"";IF(ISNUMBER(n);MIN(MAX(n;mindest);netto);netto);IF(ISNUMBER(n);MAX(n;mindest);""))`.
 * `pending`: Der rechnerische Umfang ist offen, weil eine Angabe fehlt, mit der
 * die Vorlage als 0 weiterrechnen würde – dann bleibt auch dieser Umfang offen.
 */
export function appliedRandomSize(computed: CellValue | undefined, minimum: number, netLimit: number | null, pending: boolean, global = false): CellValue {
  // Globale Neuberechnung bei AE = TE nicht anwendbar: kein Umfang, auch kein begrenzter; im ersten Zeitraum gilt der begrenzte Umfang.
  if (pending || (global && globalBlocked(computed))) return null
  const atLeast = isNumber(computed) ? Math.max(computed, minimum) : null
  if (netLimit === null) return atLeast
  return atLeast === null ? netLimit : Math.min(atLeast, netLimit)
}

/** Verhältnisschätzung einer Zufallsschicht: `BV · N(Σ E_i) / Σ BV_i`. */
export function ratioProjection(bookValue: CellValue | undefined, errorSum: CellValue | undefined, sampleBookValue: CellValue | undefined): number {
  return divide(required(bookValue) * n(errorSum), required(sampleBookValue))
}

/**
 * Erhöhung bei begrenztem Umfang (Art. 5 Abs. 7 UAbs. 4 Buchst. a; Auslegung der Vorlage):
 * `ROUNDUP(geplant·MAX(1;IFERROR(a1/b1;1);IFERROR(a2/b2;1));0)`. Die Quotienten
 * vergleichen Ist und Prognose; ein Fehlerwert zählt 1.
 */
export function increasedSize(planned: CellValue | undefined, ratios: readonly (readonly [CellValue | undefined, CellValue | undefined])[]): number {
  const factors = ratios.map(([actual, forecast]) => ifError(() => divide(required(actual), required(forecast)), 1))
  return roundUp(required(planned) * Math.max(1, ...factors))
}

/** Prüfung Mindestumfang des Geschäftsjahres (Art. 5 Abs. 5). */
export function checkAnnualMinimum(total: number): string {
  return ge(total, 30) ? '✔ ≥ 30 Einheiten' : '✖ < 30 Einheiten (Art. 5 Abs. 5)'
}

/** Prüfung begrenzter Umfang (Art. 5 Abs. 7 UAbs. 4). */
export function checkLimitKept(used: number, limit: number): string {
  return le(used, limit) ? '✔ begrenzter Umfang eingehalten' : '⚠ Umfang überschritten – Art. 5 Abs. 7 UAbs. 4'
}

/** Zellen außerhalb des Ergebnisblocks, auf die er sich bezieht. */
export interface ConclusionCells {
  /** Buchwert der Hochrechnungsbasis (BV). */
  bookValue: CellAddress
  testType: CellAddress
  materiality: CellAddress
}

/**
 * Ergebnisblock, der in allen fünf Blättern gleich aufgebaut ist. `first` ist
 * die Zeile des extrapolierten Fehlers EE; es folgen SE (+1), systembedingte
 * (+2) und anomale Fehler (+3) sowie die hier berechneten Zeilen: obere (+4)
 * und untere Fehlergrenze (+5), relative Genauigkeit (+6), Zufallsfehlerquote
 * (+7), Gesamtfehlerquote (+8), obere Fehlergrenze in % (+9), Würdigung (+10).
 *
 * `open`: Die Genauigkeit fehlt, weil eine Angabe fehlt, mit der die Vorlage
 * als 0 weiterrechnen würde. Die Würdigung bleibt dann offen, soweit sie von
 * der oberen Fehlergrenze abhängt – die Vorlage zeigt dort einen Befund auf
 * Grundlage der mit 0 gerechneten Genauigkeit. Fehlt die obere Fehlergrenze
 * dagegen auch in der Vorlage (z. B. „TE ≤ AE“), gilt deren Wortlaut.
 */
export function conclusion(c: Cells, first: number, cells: ConclusionCells, open: boolean): void {
  const [projected, precision, systemic, anomalous] = [c[at(first)], c[at(first + 1)], c[at(first + 2)], c[at(first + 3)]]
  const bookValue = c[cells.bookValue]
  c[at(first + 4)] = guard(() => required(projected) + required(precision) + n(systemic) + n(anomalous))
  c[at(first + 5)] = lowerErrorLimit(c[cells.testType], projected, precision, systemic, anomalous)
  c[at(first + 6)] = guard(() => divide(required(precision), required(bookValue)))
  c[at(first + 7)] = guard(() => divide(required(projected), required(bookValue)))
  c[at(first + 8)] = guard(() => divide(required(projected) + n(systemic) + n(anomalous), required(bookValue)))
  c[at(first + 9)] = guard(() => divide(required(c[at(first + 4)]), required(bookValue)))
  const verdict = assessment(c[at(first + 8)], c[at(first + 9)], c[cells.materiality])
  c[at(first + 10)] = open && typeof verdict === 'string' && !verdict.startsWith('✖') ? null : verdict
}

/** Zellen des Ergebnisblocks, die von der Genauigkeit SE abhängen (für `zeroAssumed`). */
export function precisionCells(first: number): CellAddress[] {
  return [first + 1, first + 4, first + 5, first + 6, first + 9, first + 10].map(at)
}

/**
 * Zellen, die vom extrapolierten Fehler EE abhängen (für `zeroAssumed` mit
 * `kind: 'partialErrorSum'`): EE, Fehlergrenzen, Quoten, Würdigung, N5 und N11.
 */
export function projectionCells(first: number): CellAddress[] {
  return [...[first, first + 4, first + 5, first + 7, first + 8, first + 9, first + 10].map(at), 'N5', 'N11']
}

/** Zellen, aus denen die Ergebnisübersicht N3–N11 gefüllt wird. */
export interface SummarySource {
  method: string
  bookValue: CellAddress
  /** Zeile des extrapolierten Fehlers EE (wie bei `conclusion`). */
  first: number
  /** Fehler der umfassenden Schicht(en). */
  exhaustive: CellAddress
  /** Stichprobenumfang gesamt; als Wert, weil manche Blätter ihn erst in N10 bilden. */
  sampleSize: CellValue | undefined
}

/** Ergebnisübersicht für Blatt 18 (feste Zellen N3–N11). */
export function summary(c: Cells, source: SummarySource): void {
  c.N3 = source.method
  c.N4 = c[source.bookValue] ?? null
  c.N5 = c[at(source.first)] ?? null
  c.N6 = c[source.exhaustive] ?? null
  c.N7 = c[at(source.first + 1)] ?? null
  c.N8 = n(c[at(source.first + 2)])
  c.N9 = n(c[at(source.first + 3)])
  c.N10 = source.sampleSize ?? null
  c.N11 = c[at(source.first + 8)] ?? null
}

type Value = CellValue | undefined

/**
 * `SUM(D<zeile>:J<zeile>)` einer berechneten Schichtzeile. Die Summe bleibt
 * offen, sobald eine Schichtzelle offen ist, während die Vorlage dort einen
 * Wert zeigt (`pending`) – sonst zeigte sie eine Zahl ohne den Beitrag dieser
 * Schicht. Zellen, die auch in der Vorlage leer sind (`""` aus `IFERROR`),
 * übergeht die Summe. Trägt keine Schicht einen Wert, ist die Summe 0 der
 * Vorlage ein Wert ohne Grundlage (`totalRow`). `used`: Zeile, die für
 * unbelegte Schichten wie in der Vorlage 0 trägt (Hilfszeilen, Hochrechnung je
 * Schicht) – Summanden sind dann nur die Werte belegter Schichten.
 */
export function strataTotal(c: Cells, row: number, pending: Pending, context: SheetContext, used?: (column: string) => boolean): CellValue {
  if (STRATA_COLUMNS.some((column) => pending(stratumCell(column, row)))) return null
  if (!used) return totalRow(c, row, context)
  return STRATA_COLUMNS.some((column) => used(column) && !isBlank(c[stratumCell(column, row)])) ? sumRow(c, row) : unfounded(context, 0)
}

/** Stand des gewählten Umfangs eines neu berechneten Zeitraums (siehe `periodSize`). */
export interface ChosenSize {
  /** Der gewählte Umfang ist offen, während die Vorlage dort einen Wert zeigt. */
  open: boolean
  /** Der gewählte Ansatz ist ausdrücklich nicht anwendbar („✖ nicht anwendbar (Nenner ≤ 0)“). */
  notApplicable: boolean
}

/**
 * Anzuwendender Umfang eines neu berechneten Zeitraums (`appliedPeriodSize`):
 * `MAX(gewählter Umfang;3[;Auffüllung auf 30])`. Trägt der gewählte Umfang
 * keine Zahl, übergeht `MAX` den Bezug, und die Vorlage zeigt nur die
 * Untergrenzen. Ist der gewählte Ansatz nicht anwendbar (Nenner ≤ 0), bleibt
 * das wie in der Vorlage stehen – alle Angaben liegen vor, das Blatt weist es
 * als Hinweis aus. Fehlt der gewählte Umfang dagegen ganz (leeres Formular,
 * „TE ≤ AE“), ist die Untergrenze ein Wert ohne Grundlage (`unfounded`).
 */
export function periodSize(chosen: Value, state: ChosenSize, context: SheetContext, shortfall?: () => number): CellValue {
  const size = appliedPeriodSize(chosen, state.open, shortfall)
  return isNumber(chosen) || state.notApplicable ? size : unfounded(context, size)
}

/** Abzug eines geprüften Zeitraums im Nenner der Standardneuberechnung: `z^2·N_t^2/n_t·s_t^2`. */
export function auditedTerm(z: Value, units: Value, size: Value, deviation: Value): number {
  return divide(required(z) ** 2 * required(units) ** 2, required(size)) * required(deviation) ** 2
}

/** Standardneuberechnung: `IF(Nenner<=0;"✖ nicht anwendbar (Nenner ≤ 0)";ROUNDUP((z·N·σ)^2/Nenner;0))`. */
export function standardSize(z: Value, units: Value, deviation: Value, denominator: Value): CellValue {
  return guard(() => (le(required(denominator), 0) ? NOT_APPLICABLE : roundUp(divide((required(z) * required(units) * required(deviation)) ** 2, required(denominator)))))
}

/** Zusatzeinheiten eines bereits geprüften Zeitraums: `MAX(0;ROUNDUP(teil/gesamt·umfang;0)-bisher)`. */
export function additionalUnits(part: Value, whole: Value, size: Value, current: Value): CellValue {
  return guard(() => Math.max(0, minus(allocate(part, whole, size), required(current))))
}
