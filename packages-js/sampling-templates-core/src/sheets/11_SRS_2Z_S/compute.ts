/**
 * Rechenkern Blatt 11_SRS_2Z_S: einfaches Zufallsstichprobenverfahren mit
 * Verhältnisschätzung, zwei Stichprobenzeiträume, geschichtet (Anhang II Nr. 2.2
 * DelVO (EU) 2023/67). Schichtzeilen werden je Schichtspalte gerechnet
 * (`fillRow`), Summen über alle Schichtspalten; die Vorlage summiert D–J, die
 * Webfassung zusätzlich AA–AM. Jede Zuweisung bildet die Formel der
 * gleichnamigen Zelle nach. Abschnitt L steht in `compute-recalculation.ts`,
 * Abschnitt N in `compute-projection.ts`. Summen über Schichtzeilen ohne
 * Summanden sind Werte ohne Grundlage (`totalRow`); was auf ihnen aufbaut,
 * bleibt offen.
 */
import { divide, guard, n, plus, required, squareRoot } from '../../excel/index'
import { resolveInputs } from '../../model/sheet'
import { STRATA_COLUMNS, fillRow, stratumCell as at, totalRow } from '../../model/strata'
import type { CellAddress, CellMap, Cells, SheetContext } from '../../model/types'
import { zValue } from '../01_Parameter/index'
import { type Pending, allocate, appliedRandomSize, computeBesideTemplate, conclusion, minimumRandomSize, netLimitedSize, strataTotal, summary } from '../shared/srs'
import { checkConfidence, checkMateriality, checkStratumUnits, checkTolerableError, computedSampleSize, limitedSampleSize } from '../shared/statistical'
import { projection } from './compute-projection'
import { recalculation } from './compute-recalculation'
import { definition } from './definition'
import { UNITS, sizeDeviation, used } from './strata'

/** Zellen einer Schichtzeile über alle Schichtspalten. */
const row = (number: number): CellAddress[] => STRATA_COLUMNS.map((column) => at(column, number))

/**
 * Eingaben, mit denen die Vorlage leer als 0 weiterrechnet; die Webfassung zeigt
 * in den abhängigen Zellen „Angabe fehlt“ (deviations.ts): Signifikanzschwelle,
 * voraussichtliche Fehlerquote, Buchwerte der Schichten (Zeilen 12, 58) und die
 * Standardabweichungen für den Stichprobenumfang (Zeilen 29, 30, 59). Keine
 * dieser Zellen wird in der Vorlage auf `""` geprüft, außer C22 und C25 in
 * Prüfhinweisen, die `pending` nicht befragt.
 */
export const REQUIRED_INPUTS: readonly CellAddress[] = ['C22', 'C25', ...[12, 29, 30, 58, 59].flatMap(row)]

/** `=SUM(D..:J..)` der Eingabezeilen; ohne Summanden ein Wert ohne Grundlage. */
function sums(c: Cells, rows: readonly number[], context: SheetContext): void {
  for (const number of rows) c[`C${number}`] = totalRow(c, number, context)
}

/** Abschnitte H und I: Summen der Schichten, z, zulässiger und voraussichtlicher Fehler, gewichtete Standardabweichung (C11–C32). */
function parameters(c: Cells, pending: Pending, context: SheetContext): void {
  sums(c, [11, 12, 13, 14], context)
  // =C12+N(C7)+C14 und =C11+C13: Trägt eine der Summen keinen Wert, baute der Wert auf einer 0 ohne Grundlage auf.
  c.C15 = guard(() => plus(plus(required(c.C12), n(c.C7)), required(c.C14)))
  c.C16 = guard(() => required(c.C11) + required(c.C13))
  c.C20 = guard(() => zValue(context.parameters, c.C18, c.C19))
  c.C21 = checkConfidence(c.C17, c.C18)
  c.C23 = checkMateriality(c.C22)
  c.C24 = guard(() => required(c.C22) * required(c.C15))
  c.C26 = guard(() => required(c.C25) * required(c.C15))
  c.C27 = checkTolerableError(c.C24, c.C26, c.C25)
  // =N(D11)*N(D29)^2+N(D13)*N(D30)^2 – fehlt σ einer belegten Schicht, bleibt die Zelle offen (`sizeDeviation`).
  fillRow(c, 31, (column) =>
    guard(() => n(c[at(column, 11)]) * sizeDeviation(c, column, UNITS.period1, 29) ** 2 + n(c[at(column, 13)]) * sizeDeviation(c, column, UNITS.forecast2, 30) ** 2),
  )
  c.C31 = strataTotal(c, 31, pending, context, (column) => used(c, column, UNITS.period1) || used(c, column, UNITS.forecast2))
  c.C32 = guard(() => squareRoot(divide(required(c.C31), required(c.C16))))
}

/**
 * Abschnitt J: Gesamtumfang und Aufteilung auf Schichten und Zeiträume (C34–C46).
 * `computedSampleSize` multipliziert z · N₁₊₂ · σ_ew in der Reihenfolge der Vorlage.
 * Rückgabe: begrenzter Umfang.
 */
function sampleSize(c: Cells, pending: Pending, context: SheetContext): number | null {
  c.C34 = computedSampleSize({ z: c.C20, bookValue: c.C16, deviation: c.C32, tolerable: c.C24, anticipated: c.C26 })
  const [check, limit] = limitedSampleSize(c.C37, c.C36, c.C35)
  c.C38 = check
  c.C39 = limit
  c.C40 = minimumRandomSize(6, c.C8)
  c.C41 = netLimitedSize(limit, c.C9)
  c.C42 = appliedRandomSize(c.C34, c.C40, c.C41, pending('C34'))
  fillRow(c, 44, (column) => (used(c, column, UNITS.period1) ? guard(() => allocate(c[at(column, 11)], c.C16, c.C42)) : null))
  fillRow(c, 45, (column) => (used(c, column, UNITS.forecast2) ? guard(() => allocate(c[at(column, 13)], c.C16, c.C42)) : null))
  fillRow(c, 46, (column) => (used(c, column, UNITS.period1) ? checkStratumUnits(c[at(column, 44)], pending(at(column, 44)), context) : null))
  c.C44 = strataTotal(c, 44, pending, context)
  c.C45 = strataTotal(c, 45, pending, context)
  return limit
}

/** Alle Formelzellen in Blattreihenfolge; `pending` siehe `computeBesideTemplate`. */
function evaluate(c: Cells, pending: Pending, context: SheetContext): void {
  parameters(c, pending, context)
  const limit = sampleSize(c, pending, context)
  sums(c, [49, 50], context)
  recalculation(c, pending, limit, context)
  sums(c, [84, 85], context)
  projection(c, pending, context)
  conclusion(c, 92, { bookValue: 'C61', testType: 'C19', materiality: 'C22' }, pending('C93'))
  summary(c, { method: 'Einfaches Zufallsstichprobenverfahren, 2 Zeiträume, geschichtet', bookValue: 'C61', first: 92, exhaustive: 'C91', sampleSize: c.C80 })
}

/** Berechnet alle Formelzellen des Blatts 11; Eingaben und Ergebnisse tragen die Zelladressen der Vorlage. */
export function compute(inputs: CellMap, context: SheetContext): CellMap {
  return computeBesideTemplate(resolveInputs(definition, inputs, context), REQUIRED_INPUTS, context, evaluate)
}
