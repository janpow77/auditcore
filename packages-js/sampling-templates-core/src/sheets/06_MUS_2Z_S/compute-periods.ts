/**
 * Rechenkern Blatt 06_MUS_2Z_S, zweiter Teil: anzuwendende Umfänge je Schicht
 * (Zeilen 69–72), Auswahl und Ergebnisse Zeitraum 2 (Zeilen 74–84) sowie
 * Hochrechnung und Genauigkeit (Zeilen 86–99).
 */
import { divide, eq, guard, isBlank, isNumber, minus, n, required, roundUp, squareRoot } from '../../excel/index'
import { countRow, stratumCell as at } from '../../model/strata'
import { unfounded } from '../../model/policy'
import type { CellValue } from '../../model/types'
import { type Approach, appliedPeriodSize, checkLimitKept, checkYearMinimum, errorLimits, summary, underestimationFactor } from '../shared/mus'
import { type Run, checkUnits, fill, has, inputTotals, total, optionalTotals } from './run'

/**
 * Zeile 69: Umfang Zeitraum 2 je Schicht nach dem gewählten Ansatz, mindestens 3.
 * Standard, global und Erhöhung sind Rechenwerte (ein Fehlerwert leert die Zelle);
 * ohne Neuberechnung steht dort der Bezug auf den Planumfang, den `MAX` übergeht,
 * wenn er leer ist.
 */
function sizePeriodTwo(run: Run, approach: Approach, column: string): CellValue {
  const { c } = run
  const actual = c[at(column, 51)]
  const planned = at(column, 38)
  if (approach === 'none') return appliedPeriodSize(c[planned], run.pending(planned), run.context)
  const factor = (): number => underestimationFactor(actual, c[at(column, 9)], c[at(column, 52)], c[at(column, 10)])
  const computed: Record<Exclude<Approach, 'none'>, () => number> = {
    standard: () => roundUp(divide(required(actual), required(c.C51)) * required(c.C63)),
    global: () => roundUp(divide(required(actual), required(c.C55)) * required(c.C66)),
    increase: () => roundUp(required(c[planned]) * factor()),
  }
  return guard(() => Math.max(3, computed[approach]()))
}

/** Abschnitt L, zweiter Teil: anzuwendende und endgültige Umfänge je Schicht und ihre Prüfung (Zeilen 69–72). */
export function finalSizes(run: Run, approach: Approach): void {
  const { c } = run
  fill(run, 69, (column) => (has(run, column, 51) ? sizePeriodTwo(run, approach, column) : null))
  fill(run, 70, (column) => (has(run, column, 8) ? guard(() => required(c[at(column, 37)]) + (approach === 'global' ? required(c[at(column, 68)]) : 0)) : null))
  c.C69 = total(run, 69)
  c.C70 = total(run, 70)
  const year = (): number => required(c.C70) + required(c.C69)
  c.C71 = checkLimitKept(run.limit, year, '⚠ Umfang überschritten – Art. 5 Abs. 7 UAbs. 4')
  c.C72 = isNumber(c.C69) && !eq(c.C69, 0) ? checkYearMinimum(year) : null
}

/** Abschnitt M: Auswahl und Ergebnisse Zeitraum 2 je Schicht (Zeilen 74–84). */
export function periodTwo(run: Run): void {
  const { c } = run
  const second = (formula: (column: string) => CellValue) => (column: string) => (has(run, column, 51) ? formula(column) : null)
  fill(run, 74, second((column) => guard(() => divide(required(c[at(column, 51)]), required(c[at(column, 69)])))))
  fill(run, 77, second((column) => guard(() => minus(required(c[at(column, 51)]), n(c[at(column, 76)])))))
  fill(run, 78, second((column) => guard(() => minus(required(c[at(column, 69)]), n(c[at(column, 75)])))))
  fill(run, 79, (column) => checkUnits(run, column, 51, 78))
  fill(run, 80, second((column) => guard(() => divide(required(c[at(column, 77)]), required(c[at(column, 78)])))))
  fill(run, 84, (column) => (has(run, column, 8) ? guard(() => minus(required(c[at(column, 70)]), n(c[at(column, 41)]))) : null))
  optionalTotals(run, [75, 76, 81])
  inputTotals(run, [82])
  for (const row of [77, 78, 84]) c[`C${row}`] = total(run, row)
}

/**
 * Beitrag eines Zeitraums zu Hochrechnung (`power` 1, mal Summe der Fehlerquoten)
 * bzw. Genauigkeit (`power` 2, mal s²): `BV_hs^power / n_hs · Faktor`.
 */
function term(run: Run, column: string, rows: readonly [bookValue: number, units: number], power: number, factor: number): number {
  return divide(required(run.c[at(column, rows[0])]) ** power, required(run.c[at(column, rows[1])])) * factor
}

/**
 * Summe einer Hilfszeile der Hochrechnung (87, 88). Offen, solange der Umfang
 * einer belegten Schicht offen ist – die Vorlage zeigte dort 0, weil sie eine
 * fehlende Summe der Fehlerquoten bzw. Standardabweichung als 0 rechnet. Trägt
 * in einem der beiden Zeiträume keine Schicht einen Buchwert, käme die Summe
 * allein aus dem anderen Zeitraum: ein Wert ohne Grundlage.
 */
function projectionTotal(run: Run, row: number): CellValue {
  const { c } = run
  if (run.active.some((column) => run.pending(at(column, 84)) || run.pending(at(column, 78)))) return null
  const sum = total(run, row, [8, 51])
  return isBlank(c.C8) || isBlank(c.C51) ? unfounded(run.context, sum) : sum
}

/**
 * Abschnitt N: Hochrechnung und Genauigkeit (Zeilen 86–99). Fehlt die
 * Standardabweichung der Stichprobe einer belegten Schicht (Zeilen 49, 83), ist
 * ihr Beitrag zur Genauigkeit wie in der Vorlage 0 (`zeroAssumed`).
 */
export function projection(run: Run): void {
  const { c } = run
  const value = (column: string, row: number): CellValue => c[at(column, row)] ?? null
  const part = (column: string, used: number, rows: readonly [number, number], power: number, factor: () => number): number => (has(run, column, used) ? term(run, column, rows, power, factor()) : 0)
  const squared = (column: string, row: number): number => required(value(column, row)) ** 2
  fill(run, 86, (column) => n(value(column, 47)) + n(value(column, 81)))
  fill(run, 87, (column) => guard(() => part(column, 8, [43, 84], 1, () => n(value(column, 48))) + part(column, 51, [77, 78], 1, () => n(value(column, 82)))))
  fill(run, 88, (column) =>
    guard(() => (isBlank(value(column, 49)) ? 0 : part(column, 8, [43, 84], 2, () => squared(column, 49))) + (isBlank(value(column, 83)) ? 0 : part(column, 51, [77, 78], 2, () => squared(column, 83)))),
  )
  c.C86 = total(run, 86, [8, 47, 51, 81])
  c.C87 = projectionTotal(run, 87)
  c.C88 = projectionTotal(run, 88)
  c.C89 = eq(countRow(c, 48) + countRow(c, 82), 0) ? null : guard(() => required(c.C86) + required(c.C87))
  c.C90 = guard(() => required(c.C15) * squareRoot(required(c.C88)))
  errorLimits(c, 89, c.C14, c.C55, c.C17)
  summary(c, 'MUS-Standardansatz, 2 Zeiträume, geschichtet', 89, c.C55, c.C86, () => required(c.C70) + required(c.C69))
}
