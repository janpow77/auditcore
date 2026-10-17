/**
 * Rechenkern Blatt 06_MUS_2Z_S: MUS-Standardansatz, zwei Stichprobenzeiträume,
 * geschichtet (Anhang II Nr. 1.2 DelVO (EU) 2023/67). Schichtzeilen werden je
 * Schichtspalte gerechnet (`fill`), Summen über alle Schichtspalten; die
 * Vorlage summiert D–J, die Webfassung zusätzlich AA–AM. Trägt keine Schicht
 * einen Summanden, bleibt die Summe offen statt 0 (`totalRow`). Eine Schicht nimmt am
 * ersten Zeitraum teil, wenn ihr Buchwert in Zeile 8 steht, am zweiten, wenn er
 * in Zeile 51 steht – wie in der Vorlage (`IF(D8="";…)`, `IF(D51="";…)`).
 */
import { divide, guard, isBlank, minus, n, required, roundUp, squareRoot } from '../../excel/index'
import { resolveInputs } from '../../model/sheet'
import { STRATA_COLUMNS, stratumCell as at } from '../../model/strata'
import type { CellAddress, CellMap, CellValue, Cells, SheetContext } from '../../model/types'
import { zValue } from '../01_Parameter/index'
import { type Pending, additionalUnits, appliedTotalSize, approachOf, computeTwice, remembered, share, standardSize } from '../shared/mus'
import { checkConfidence, checkMateriality, checkTolerableError, computedSampleSize, limitedSampleSize } from '../shared/statistical'
import { finalSizes, periodTwo, projection } from './compute-periods'
import { definition } from './definition'
import { type Run, checkUnits, createRun, fill, has, inputTotals, relevantInputs, total, varianceTerm, optionalTotals } from './run'
import { blockedGlobal, clearAfterGlobal, globalSize, withoutGlobalAssessment } from '../shared/periods'

/** Standardabweichung (Zeile) zum Buchwert (Zeile), von dem abhängt, ob die Schicht sie braucht. */
const DEVIATION_OF: readonly (readonly [bookValue: number, deviation: number])[] = [[8, 24], [9, 25], [51, 53]]

/**
 * Eingaben, mit denen die Vorlage leer als 0 weiterrechnet: Signifikanzschwelle,
 * voraussichtliche Fehlerquote und je Schicht die Standardabweichungen (Zeilen 24,
 * 25 und 53), soweit die Schicht im jeweiligen Zeitraum einen Buchwert hat. Die
 * Webfassung zeigt in den abhängigen Zellen „Angabe fehlt“ (deviations.ts).
 */
export function requiredInputs(c: CellMap): CellAddress[] {
  const strata = STRATA_COLUMNS.flatMap((column) => DEVIATION_OF.filter(([bookValue]) => !isBlank(c[at(column, bookValue)])).map(([, deviation]) => at(column, deviation)))
  return ['C17', 'C20', ...strata]
}

/** Abschnitte H und I: Summen der Schichten, z, zulässiger und voraussichtlicher Fehler (C8–C27). */
function parameters(run: Run, context: SheetContext): void {
  const { c } = run
  inputTotals(run, [8, 9, 10])
  c.C11 = guard(() => required(c.C8) + required(c.C9))
  c.C15 = guard(() => zValue(context.parameters, c.C13, c.C14))
  c.C16 = checkConfidence(c.C12, c.C13)
  c.C18 = checkMateriality(c.C17)
  c.C19 = guard(() => required(c.C17) * required(c.C11))
  c.C21 = guard(() => required(c.C20) * required(c.C11))
  c.C22 = checkTolerableError(c.C19, c.C21, c.C20)
  // Zeile 26: Die Vorlage rechnet eine fehlende Standardabweichung als 0; die Webfassung verlangt sie für belegte Schichten.
  fill(run, 26, (column) => guard(() => varianceTerm(run, column, 8, 24) + varianceTerm(run, column, 9, 25)))
  c.C26 = total(run, 26, [8, 9])
  c.C27 = guard(() => squareRoot(divide(required(c.C26), required(c.C11))))
}

/** Abschnitt J: Gesamtumfang und Aufteilung auf Schichten und Zeiträume (C29–C38); Rückgabe: begrenzter Umfang. */
function sampleSize(run: Run): number | null {
  const { c } = run
  c.C29 = computedSampleSize({ z: c.C15, bookValue: c.C11, deviation: c.C27, tolerable: c.C19, anticipated: c.C21 })
  const [check, limit] = limitedSampleSize(c.C32, c.C31, c.C30)
  c.C33 = check
  c.C34 = limit
  c.C35 = appliedTotalSize(c.C29, limit, run.pending('C29'), run.context)
  fill(run, 37, (column) => (has(run, column, 8) ? share(c[at(column, 8)], c.C11, c.C35) : null))
  fill(run, 38, (column) => (has(run, column, 9) ? share(c[at(column, 9)], c.C11, c.C35) : null))
  c.C37 = total(run, 37)
  c.C38 = total(run, 38)
  return limit
}

/** Abschnitt K: Auswahl und Ergebnisse Zeitraum 1 je Schicht (Zeilen 40–48). */
function periodOne(run: Run): void {
  const { c } = run
  const first = (formula: (column: string) => CellValue) => (column: string) => (has(run, column, 8) ? formula(column) : null)
  fill(run, 40, first((column) => guard(() => divide(required(c[at(column, 8)]), required(c[at(column, 37)])))))
  fill(run, 43, first((column) => guard(() => minus(required(c[at(column, 8)]), n(c[at(column, 42)])))))
  fill(run, 44, first((column) => guard(() => minus(required(c[at(column, 37)]), n(c[at(column, 41)])))))
  fill(run, 45, (column) => checkUnits(run, column, 8, 44))
  fill(run, 46, first((column) => guard(() => divide(required(c[at(column, 43)]), required(c[at(column, 44)])))))
  optionalTotals(run, [41, 42, 47])
  inputTotals(run, [48])
  c.C43 = total(run, 43)
  c.C44 = total(run, 44)
}

/** Abschnitt L, erster Teil: aktualisierte Größen, Standard- und globale Neuberechnung (C51–C66). */
function recalculation(run: Run): void {
  const { c } = run
  inputTotals(run, [51, 52])
  c.C55 = guard(() => required(c.C8) + required(c.C51))
  c.C56 = guard(() => required(c.C17) * required(c.C55))
  c.C57 = guard(() => required(isBlank(c.C54) ? c.C20 : c.C54) * required(c.C55))
  fill(run, 59, (column) => (has(run, column, 8) ? ((isBlank(c[at(column, 49)]) ? c[at(column, 24)] : c[at(column, 49)]) ?? null) : null))
  fill(run, 60, (column) => (has(run, column, 8) ? guard(() => divide(required(c[at(column, 8)]) ** 2, required(c[at(column, 37)])) * required(c[at(column, 59)]) ** 2) : 0))
  fill(run, 61, (column) => guard(() => varianceTerm(run, column, 51, 53)))
  c.C60 = total(run, 60, [8])
  c.C61 = total(run, 61, [51])
  c.C62 = guard(() => minus(minus(required(c.C56), required(c.C57)) ** 2, required(c.C15) ** 2 * required(c.C60)))
  c.C63 = standardSize(c.C62, () => required(c.C15) ** 2 * required(c.C51) * required(c.C61))
  fill(run, 64, (column) => guard(() => varianceTerm(run, column, 8, 59) + varianceTerm(run, column, 51, 53)))
  c.C64 = total(run, 64, [8, 51])
  c.C65 = globalSize(c.C56, c.C57, () => roundUp(divide(required(c.C15) * required(c.C55) * squareRoot(divide(required(c.C64), required(c.C55))), minus(required(c.C56), required(c.C57))) ** 2))
  c.C66 = appliedTotalSize(c.C65, run.limit, run.pending('C65'), run.context, true)
  fill(run, 68, (column) => (has(run, column, 8) ? additionalUnits(share(c[at(column, 8)], c.C55, c.C66), c[at(column, 37)]) : null))
  // Nach der DelVO nicht anwendbar: keine Zusatzeinheiten aus der globalen Neuberechnung (statt der Summe 0).
  c.C68 = blockedGlobal(c, 'C65', run.pending) ? null : total(run, 68)
}

/** Alle Formelzellen in Blattreihenfolge; `pending` und `context` siehe `computeTwice`. */
function evaluate(c: Cells, pending: Pending, context: SheetContext): void {
  const run = createRun(c, pending, context)
  parameters(run, context)
  run.limit = sampleSize(run)
  periodOne(run)
  recalculation(run)
  finalSizes(run, approachOf(c.C28))
  periodTwo(run)
  projection(run)
  withoutGlobalAssessment(c, approachOf(c.C28), ['C65'], pending, 'C99')
  if (approachOf(c.C28) === 'global' && blockedGlobal(c, 'C65', pending)) clearAfterGlobal(c, definition, 65)
}

/** Rechnet das Blatt aus den aufgelösten Eingaben; `compute` merkt sich die Ergebnisse. */
export function computeCells(cells: Cells, context: SheetContext): Cells {
  return computeTwice(cells, requiredInputs(cells), context, evaluate)
}

const calculate = remembered(computeCells, relevantInputs)

/** Berechnet alle Formelzellen des Blatts 06. */
export function compute(inputs: CellMap, context: SheetContext): CellMap {
  return calculate(resolveInputs(definition, inputs, context), context)
}
