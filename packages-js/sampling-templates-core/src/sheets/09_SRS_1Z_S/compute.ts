/**
 * Rechenkern Blatt 09_SRS_1Z_S: einfaches Zufallsstichprobenverfahren mit
 * Verhältnisschätzung, ein Stichprobenzeitraum, geschichtet (Anhang II Nr. 2.1
 * DelVO (EU) 2023/67). Schichtzeilen werden je Schichtspalte gerechnet
 * (`fillRow`), Summen über alle Schichtspalten; die Vorlage summiert D–J, die
 * Webfassung zusätzlich AA–AM. Eine Schicht ist belegt, wenn ihre Anzahl
 * Einheiten (Zeile 12) angegeben ist.
 */
import { divide, gt, guard, isBlank, minus, n, required, squareRoot } from '../../excel/index'
import { unfounded } from '../../model/policy'
import { resolveInputs } from '../../model/sheet'
import { STRATA_COLUMNS, countRow, fillRow, stratumCell as at, totalRow } from '../../model/strata'
import type { CellAddress, CellMap, Cells, SheetContext } from '../../model/types'
import { zValue } from '../01_Parameter/index'
import { type Pending, allocate, appliedRandomSize, computeBesideTemplate, conclusion, minimumRandomSize, netLimitedSize, ratioProjection, strataTotal, summary } from '../shared/srs'
import { checkConfidence, checkMateriality, checkStratumUnits, checkTolerableError, computedSampleSize, limitedSampleSize } from '../shared/statistical'
import { definition } from './definition'

/** Zellen einer Schichtzeile über alle Schichtspalten. */
const row = (number: number): CellAddress[] => STRATA_COLUMNS.map((column) => at(column, number))

/**
 * Eingaben, mit denen die Vorlage leer als 0 weiterrechnet; die Webfassung zeigt
 * in den abhängigen Zellen „Angabe fehlt“ (deviations.ts): voraussichtliche
 * Fehlerquote, Buchwert und voraussichtliche Standardabweichung jeder belegten Schicht.
 */
export const REQUIRED_INPUTS: readonly CellAddress[] = ['C24', ...row(13), ...row(28)]

/** Abschnitte H und I: Summen der Schichten, z, zulässiger und voraussichtlicher Fehler (C12–C30). */
function parameters(c: Cells, pending: Pending, context: SheetContext): void {
  const used = (column: string): boolean => !isBlank(c[at(column, 12)])
  c.C12 = totalRow(c, 12, context)
  c.C13 = totalRow(c, 13, context)
  // =C13+N(C8): ohne Buchwert einer Zufallsschicht baut die Vorlage auf der Summe 0 auf.
  c.C14 = guard(() => required(c.C13) + n(c.C8))
  c.C15 = guard(() => minus(required(c.C14), required(context.sheets['02_Grundgesamtheit']?.C51)))
  c.C19 = guard(() => zValue(context.parameters, c.C17, c.C18))
  c.C20 = checkConfidence(c.C16, c.C17)
  c.C22 = checkMateriality(c.C21)
  c.C23 = guard(() => required(c.C21) * required(c.C14))
  c.C25 = guard(() => required(c.C24) * required(c.C14))
  c.C26 = checkTolerableError(c.C23, c.C25, c.C24)
  // Zeile 29: fehlt σ_eh einer belegten Schicht, rechnet die Vorlage mit 0; die Webfassung zeigt „Angabe fehlt“.
  fillRow(c, 29, (column) => (used(column) ? guard(() => required(c[at(column, 12)]) * required(c[at(column, 28)]) ** 2) : 0))
  c.C29 = strataTotal(c, 29, pending, context, used)
  c.C30 = guard(() => squareRoot(divide(required(c.C29), required(c.C12))))
}

/**
 * Abschnitt J (C31–C42). Die Formel der Vorlage lautet (N · z · σ_w / (TE − AE))²;
 * `computedSampleSize` multipliziert in derselben Reihenfolge, wenn N an erster
 * Stelle steht. Zeile 42: Gibt es keinen Umfang je Schicht (D41 = ""), zeigt die
 * Vorlage „✔ ≥ 3“ – ein Prüfhinweis ohne Grundlage (`checkStratumUnits`).
 */
function sampleSize(c: Cells, pending: Pending, context: SheetContext): void {
  const used = (column: string): boolean => !isBlank(c[at(column, 12)])
  c.C31 = computedSampleSize({ z: c.C12, bookValue: c.C19, deviation: c.C30, tolerable: c.C23, anticipated: c.C25 })
  const [check, limit] = limitedSampleSize(c.C34, c.C33, c.C32)
  c.C35 = check
  c.C36 = limit
  c.C37 = minimumRandomSize(3, c.C9)
  c.C38 = netLimitedSize(limit, c.C10)
  c.C39 = appliedRandomSize(c.C31, c.C37, c.C38, pending('C31'))
  fillRow(c, 41, (column) => (used(column) ? guard(() => allocate(c[at(column, 12)], c.C12, c.C39)) : null))
  fillRow(c, 42, (column) => (used(column) ? checkStratumUnits(c[at(column, 41)], pending(at(column, 41)), context) : null))
  c.C41 = strataTotal(c, 41, pending, context)
}

/**
 * Abschnitt L (Zeilen 49–53). Fehlt der Buchwert einer belegten Schicht, rechnet
 * die Vorlage ihre Hochrechnung mit 0; die Webfassung zeigt „Angabe fehlt“, auch
 * in der Summe. Trägt keine Schicht eine Fehlersumme, ist die Hochrechnung 0 je
 * Schicht ein Wert ohne Grundlage. Trägt nur eine belegte Schicht keine, zählt
 * sie wie in der Vorlage 0 (`zeroAssumed`), ebenso ein fehlendes s_qh.
 */
function projection(c: Cells, pending: Pending, context: SheetContext): void {
  const used = (column: string): boolean => !isBlank(c[at(column, 12)])
  const anyErrorSum = gt(countRow(c, 46), 0)
  c.C45 = totalRow(c, 45, context)
  c.C46 = totalRow(c, 46, context)
  fillRow(c, 49, (column) => {
    if (!used(column)) return 0
    const projected = guard(() => ratioProjection(c[at(column, 13)], c[at(column, 46)], c[at(column, 45)]))
    return anyErrorSum ? projected : unfounded(context, projected)
  })
  fillRow(c, 50, (column) => (!used(column) || isBlank(c[at(column, 47)]) ? 0 : guard(() => required(c[at(column, 12)]) * required(c[at(column, 47)]) ** 2)))
  c.C49 = strataTotal(c, 49, pending, context, used)
  c.C50 = strataTotal(c, 50, pending, context, used)
  c.C51 = n(c.C43)
  // =IF(COUNT(D46:J46)=0;"";C51+C49)
  c.C52 = anyErrorSum ? guard(() => n(c.C51) + required(c.C49)) : null
  c.C53 = guard(() => divide(required(c.C12) * required(c.C19) * squareRoot(divide(required(c.C50), required(c.C12))), squareRoot(required(c.C41))))
}

/** Alle Formelzellen in Blattreihenfolge; `pending` siehe `computeBesideTemplate`. */
function evaluate(c: Cells, pending: Pending, context: SheetContext): void {
  parameters(c, pending, context)
  sampleSize(c, pending, context)
  projection(c, pending, context)
  conclusion(c, 52, { bookValue: 'C14', testType: 'C18', materiality: 'C21' }, pending('C53'))
  const sampleUnits = guard(() => required(c.C41) + n(c.C9))
  summary(c, { method: 'Einfaches Zufallsstichprobenverfahren, 1 Zeitraum, geschichtet', bookValue: 'C14', first: 52, exhaustive: 'C51', sampleSize: sampleUnits })
}

/** Berechnet alle Formelzellen des Blatts 09. */
export function compute(inputs: CellMap, context: SheetContext): CellMap {
  return computeBesideTemplate(resolveInputs(definition, inputs, context), REQUIRED_INPUTS, context, evaluate)
}
