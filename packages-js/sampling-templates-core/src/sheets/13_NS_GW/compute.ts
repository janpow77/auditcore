/**
 * Rechenkern Blatt 13_NS_GW: nichtstatistisches Verfahren, Auswahl mit gleicher
 * Wahrscheinlichkeit, nicht geschichtet (Art. 6 Abs. 1 Buchst. b; Anhang II
 * Nr. 2.1 DelVO (EU) 2023/67, Verhältnisschätzung). Jede Zuweisung bildet die
 * Formel der gleichnamigen Zelle der Vorlage nach.
 */
import { divide, guard, isNumber, minus, n, plus, required } from '../../excel/index'
import { resolveInputs } from '../../model/sheet'
import type { CellMap, Cells, SheetContext } from '../../model/types'
import { assessment, checkAdmissibility, checkCoverage, fillSummary, minimumCoverage, projectedError, projectedErrorRate, totalErrorRate } from '../shared/nonstatistical'
import { definition } from './definition'

/** Abschnitte H und I: Zulässigkeit, Zufallsschicht, Gesamtstichprobe und Mindesterfassung (C9–C16). */
function sample(c: Cells): void {
  c.C9 = checkAdmissibility(c.C8)
  c.C12 = guard(() => minus(required(c.C7), n(c.C10)))
  // =N(C13)+N(C11): Ohne Umfang der Zufallsstichprobe rechnet die Vorlage mit 0; die Webfassung zeigt „Angabe fehlt“.
  c.C14 = guard(() => plus(required(c.C13), n(c.C11)))
  c.C15 = minimumCoverage(c.C8)
  c.C16 = checkCoverage(c.C14, c.C15)
}

/** Abschnitt K: Hochrechnung mit Verhältnisschätzung, Fehlerquoten und Würdigung (C20–C28). */
function projection(c: Cells): void {
  c.C20 = n(c.C19)
  c.C21 = guard(() => divide(required(c.C12) * n(c.C18), required(c.C17)))
  c.C22 = projectedError(isNumber(c.C18) ? 1 : 0, c.C20, c.C21)
  c.C25 = projectedErrorRate(c.C22, c.C7)
  c.C26 = totalErrorRate(c.C22, c.C23, c.C24, c.C7)
  c.C28 = assessment(c.C26, c.C27)
}

/** Berechnet alle Formelzellen des Blatts 13; Eingaben und Ergebnisse tragen die Zelladressen der Vorlage. */
export function compute(inputs: CellMap, context: SheetContext): CellMap {
  const c = resolveInputs(definition, inputs, context)
  sample(c)
  projection(c)
  fillSummary(c, { method: 'Nichtstatistisch, gleiche Wahrscheinlichkeit', bookValue: 'C7', projectedError: 'C22', exhaustiveError: 'C20', systemicErrors: 'C23', anomalousErrors: 'C24', sampleSize: 'C14', totalErrorRate: 'C26' })
  return c
}
