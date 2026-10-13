/**
 * Rechenkern Blatt 15_NS_PPS: nichtstatistisches Verfahren, wertproportionale
 * Auswahl (PPS), nicht geschichtet (Art. 6 Abs. 1 Buchst. a; Anhang II Nr. 1.1
 * DelVO (EU) 2023/67). Jede Zuweisung bildet die Formel der gleichnamigen Zelle
 * der Vorlage nach.
 */
import { divide, guard, isNumber, minus, n, required } from '../../excel/index'
import { resolveInputs } from '../../model/sheet'
import type { CellMap, Cells, SheetContext } from '../../model/types'
import { assessment, checkAdmissibility, checkCoverage, fillSummary, minimumCoverage, projectedError, projectedErrorRate, totalErrorRate } from '../shared/nonstatistical'
// Die Formeln der Zellen C18 und C21 sind wortgleich mit C33 und C36 in Blatt 03.
import { checkIteration, checkMinimumUnits } from '../shared/statistical'
import { definition } from './definition'

/** Abschnitte H und I: Zulässigkeit, Mindesterfassung, Grenzwert, Zufallsschicht und Auswahlintervall (C9–C21). */
function sample(c: Cells): void {
  c.C9 = checkAdmissibility(c.C8)
  c.C11 = minimumCoverage(c.C8)
  c.C12 = checkCoverage(c.C10, c.C11)
  c.C13 = guard(() => divide(required(c.C7), required(c.C10)))
  c.C16 = guard(() => minus(required(c.C7), n(c.C15)))
  c.C17 = guard(() => minus(required(c.C10), n(c.C14)))
  c.C18 = checkMinimumUnits(c.C17)
  c.C19 = guard(() => divide(required(c.C16), required(c.C17)))
  c.C21 = checkIteration(c.C20)
}

/** Abschnitt K: Hochrechnung, Fehlerquoten und Würdigung (C24–C32). */
function projection(c: Cells): void {
  c.C24 = n(c.C22)
  c.C25 = guard(() => required(c.C19) * n(c.C23))
  c.C26 = projectedError(isNumber(c.C23) ? 1 : 0, c.C24, c.C25)
  c.C29 = projectedErrorRate(c.C26, c.C7)
  c.C30 = totalErrorRate(c.C26, c.C27, c.C28, c.C7)
  c.C32 = assessment(c.C30, c.C31)
}

/** Berechnet alle Formelzellen des Blatts 15; Eingaben und Ergebnisse tragen die Zelladressen der Vorlage. */
export function compute(inputs: CellMap, context: SheetContext): CellMap {
  const c = resolveInputs(definition, inputs, context)
  sample(c)
  projection(c)
  fillSummary(c, { method: 'Nichtstatistisch, PPS', bookValue: 'C7', projectedError: 'C26', exhaustiveError: 'C24', systemicErrors: 'C27', anomalousErrors: 'C28', sampleSize: 'C10', totalErrorRate: 'C30' })
  return c
}
