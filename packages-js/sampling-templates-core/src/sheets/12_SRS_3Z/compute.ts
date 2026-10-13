/**
 * Rechenkern Blatt 12_SRS_3Z: einfaches Zufallsstichprobenverfahren mit
 * Verhältnisschätzung, drei Stichprobenzeiträume, nicht geschichtet (Anhang II
 * Nr. 2.3 DelVO (EU) 2023/67). Jede Zuweisung bildet die Formel der
 * gleichnamigen Zelle der Vorlage nach; Rundung, Schwellen und
 * Rechenreihenfolge sind unverändert. Die Neuberechnungen stehen in
 * `compute-period2.ts` (Abschnitt L) und `compute-period3.ts` (Abschnitt N).
 */
import { count, divide, eq, guard, minus, n, required, squareRoot } from '../../excel/index'
import { unfounded } from '../../model/policy'
import { resolveInputs } from '../../model/sheet'
import type { CellAddress, CellMap, Cells, SheetContext } from '../../model/types'
import { zValue } from '../01_Parameter/index'
import { type Pending, appliedRandomSize, computeBesideTemplate, conclusion, minimumRandomSize, netLimitedSize, ratioProjection, recalculationOf, share, summary, weightedDeviation } from '../shared/srs'
import { checkConfidence, checkMateriality, checkTolerableError, computedSampleSize, limitedSampleSize } from '../shared/statistical'
import { secondPeriod } from './compute-period2'
import { thirdPeriod } from './compute-period3'
import { definition } from './definition'

/**
 * Eingaben, mit denen die Vorlage leer als 0 weiterrechnet; die Webfassung
 * zeigt in den abhängigen Zellen „Angabe fehlt“ (deviations.ts). Nicht dabei:
 * fakultative Angaben in `N(…)`, Eingaben mit eigener Verzweigung „leer = …“
 * (C50, C64, C89, C100), die Standardabweichungen s_q der Genauigkeit (C51,
 * C90, C124) und die Summen der Buchwerte der Stichproben (C48, C87, C121:
 * leer ergibt auch in der Vorlage keinen Wert).
 */
export const REQUIRED_INPUTS: readonly CellAddress[] = ['C7', 'C8', 'C14', 'C15', 'C16', 'C17', 'C25', 'C28', 'C31', 'C32', 'C33', 'C53', 'C54', 'C60', 'C61', 'C62', 'C63', 'C92', 'C93', 'C99']

/** Abschnitte H und I: Zufallsschicht, Prognosen, z, zulässiger und voraussichtlicher Fehler (C12–C34). */
function parameters(c: Cells, context: SheetContext): void {
  c.C12 = guard(() => minus(required(c.C7), n(c.C9)))
  c.C13 = guard(() => minus(required(c.C8), n(c.C10)))
  c.C18 = guard(() => required(c.C7) + required(c.C14) + required(c.C16))
  c.C19 = guard(() => required(c.C13) + required(c.C15) + required(c.C17))
  c.C23 = guard(() => zValue(context.parameters, c.C21, c.C22))
  c.C24 = checkConfidence(c.C20, c.C21)
  c.C26 = checkMateriality(c.C25)
  c.C27 = guard(() => required(c.C25) * required(c.C18))
  c.C29 = guard(() => required(c.C28) * required(c.C18))
  c.C30 = checkTolerableError(c.C27, c.C29, c.C28)
  c.C34 = weightedDeviation([[c.C13, c.C31], [c.C15, c.C32], [c.C17, c.C33]], c.C19)
}

/**
 * Abschnitt J: rechnerischer, begrenzter und anzuwendender Gesamtumfang und
 * seine Aufteilung auf die Zeiträume (C36–C47). Die Formel der Vorlage lautet
 * (z · N · σ_ew / (TE − AE))²; `computedSampleSize` multipliziert in dieser Reihenfolge.
 */
function sampleSize(c: Cells, pending: Pending): void {
  c.C36 = computedSampleSize({ z: c.C23, bookValue: c.C19, deviation: c.C34, tolerable: c.C27, anticipated: c.C29 })
  const [check, limit] = limitedSampleSize(c.C39, c.C38, c.C37)
  c.C40 = check
  c.C41 = limit
  c.C42 = minimumRandomSize(9, c.C10)
  c.C43 = netLimitedSize(limit, c.C11)
  c.C44 = appliedRandomSize(c.C36, c.C42, c.C43, pending('C36'))
  c.C45 = share(c.C13, c.C19, c.C44)
  c.C46 = share(c.C15, c.C19, c.C44)
  c.C47 = share(c.C17, c.C19, c.C44)
}

/** Beitrag eines Zeitraums zur Varianz der Hochrechnung: `N_t^2·s_qt^2/n_t`; fehlt s_q, zählt es wie in der Vorlage 0. */
function varianceTerm(units: CellAddress, deviation: CellAddress, size: CellAddress, c: Cells): number {
  return divide(required(c[units]) ** 2 * n(c[deviation]) ** 2, required(c[size]))
}

/**
 * Abschnitt P: Hochrechnung (Verhältnisschätzung) und Genauigkeit (C126–C129).
 * Trägt kein Zeitraum eine Fehlersumme, ist die Hochrechnung 0 der Vorlage ein
 * Wert ohne Grundlage; fehlt sie nur in einzelnen Zeiträumen, zählt sie dort
 * wie in der Vorlage 0 (`zeroAssumed`).
 */
function projection(c: Cells, context: SheetContext): void {
  const anyErrorSum = !eq(count([c.C49, c.C88, c.C122]), 0)
  const projected = guard(() => ratioProjection(c.C12, c.C49, c.C48) + ratioProjection(c.C58, c.C88, c.C87) + ratioProjection(c.C97, c.C122, c.C121))
  c.C126 = n(c.C52) + n(c.C91) + n(c.C125)
  c.C127 = anyErrorSum ? projected : unfounded(context, projected)
  // =IF(COUNT(C49;C88;C122)=0;"";C126+C127)
  c.C128 = anyErrorSum ? guard(() => n(c.C126) + required(c.C127)) : null
  // Fehlt s_q eines Zeitraums (C51, C90, C124), rechnet die Vorlage dessen Beitrag mit 0; die Webfassung ebenso und weist es aus (`zeroAssumed`).
  c.C129 = guard(() => required(c.C23) * squareRoot(varianceTerm('C13', 'C51', 'C116', c) + varianceTerm('C59', 'C90', 'C117', c) + varianceTerm('C98', 'C124', 'C118', c)))
}

/** Alle Formelzellen in Blattreihenfolge; `pending` siehe `computeBesideTemplate`. */
function evaluate(c: Cells, pending: Pending, context: SheetContext): void {
  const approach = recalculationOf(c.C35)
  parameters(c, context)
  sampleSize(c, pending)
  secondPeriod(c, pending, approach, context)
  thirdPeriod(c, pending, approach, context)
  projection(c, context)
  conclusion(c, 128, { bookValue: 'C101', testType: 'C22', materiality: 'C25' }, pending('C129'))
  summary(c, { method: 'Einfaches Zufallsstichprobenverfahren, 3 Zeiträume', bookValue: 'C101', first: 128, exhaustive: 'C126', sampleSize: c.C119 })
}

/** Berechnet alle Formelzellen des Blatts 12; Eingaben und Ergebnisse tragen die Zelladressen der Vorlage. */
export function compute(inputs: CellMap, context: SheetContext): CellMap {
  return computeBesideTemplate(resolveInputs(definition, inputs, context), REQUIRED_INPUTS, context, evaluate)
}
