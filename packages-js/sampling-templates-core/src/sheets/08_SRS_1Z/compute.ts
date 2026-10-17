/**
 * Rechenkern Blatt 08_SRS_1Z: einfaches Zufallsstichprobenverfahren mit
 * Verhältnisschätzung, ein Stichprobenzeitraum, nicht geschichtet (Anhang II
 * Nr. 2.1 DelVO (EU) 2023/67). Jede Zuweisung bildet die Formel der
 * gleichnamigen Zelle der Vorlage nach.
 */
import { divide, guard, isNumber, minus, n, required, squareRoot } from '../../excel/index'
import { unfounded } from '../../model/policy'
import { resolveInputs } from '../../model/sheet'
import type { CellMap, Cells, SheetContext } from '../../model/types'
import { zValue } from '../01_Parameter/index'
import { appliedRandomSize, conclusion, minimumRandomSize, netLimitedSize, ratioProjection, summary } from '../shared/srs'
import { checkConfidence, checkMateriality, checkTolerableError, computedSampleSize, isSizePending, limitedSampleSize } from '../shared/statistical'
import { definition } from './definition'

/** Abschnitte H und I: Zufallsschicht, z, zulässiger und voraussichtlicher Fehler (C12–C24). */
function parameters(c: Cells, context: SheetContext): void {
  c.C12 = guard(() => minus(required(c.C7), n(c.C9)))
  c.C13 = guard(() => minus(required(c.C8), n(c.C10)))
  c.C17 = guard(() => zValue(context.parameters, c.C15, c.C16))
  c.C18 = checkConfidence(c.C14, c.C15)
  c.C20 = checkMateriality(c.C19)
  c.C21 = guard(() => required(c.C19) * required(c.C7))
  c.C23 = guard(() => required(c.C22) * required(c.C7))
  c.C24 = checkTolerableError(c.C21, c.C23, c.C22)
}

/**
 * Abschnitt J: rechnerischer, begrenzter und anzuwendender Umfang (C26–C35).
 * Die Formel der Vorlage lautet (N_s · z · σ_e / (TE − AE))²; `computedSampleSize`
 * multipliziert in derselben Reihenfolge, wenn N_s an erster Stelle steht.
 * Rückgabe `true`: Der Umfang ist offen, weil eine Angabe fehlt, mit der die
 * Vorlage als 0 weiterrechnen würde (N, voraussichtliche Fehlerquote, σ_e).
 */
function sampleSize(c: Cells): boolean {
  c.C26 = computedSampleSize({ z: c.C13, bookValue: c.C17, deviation: c.C25, tolerable: c.C21, anticipated: c.C23 })
  const [check, limit] = limitedSampleSize(c.C29, c.C28, c.C27)
  c.C30 = check
  c.C31 = limit
  c.C32 = minimumRandomSize(3, c.C10)
  c.C33 = netLimitedSize(limit, c.C11)
  const pending = isSizePending(c.C26, c.C21, c.C17)
  c.C34 = appliedRandomSize(c.C26, c.C32, c.C33, pending)
  c.C35 = guard(() => required(c.C34) + n(c.C10))
  return pending
}

/**
 * Abschnitt L: Hochrechnung (Verhältnisschätzung) und Genauigkeit (C41–C44).
 * C42 liest die Fehlersumme mit `N(…)`: Fehlt sie, zeigt die Vorlage 0 € – ein
 * Wert ohne Grundlage: offen, solange eine Pflichteingabe fehlt; bei vollständigen
 * Pflichteingaben zeigt ihn die Webfassung wie die Vorlage mit Hinweis (`evaluateSheet`).
 */
function projection(c: Cells, context: SheetContext): void {
  const projected = guard(() => ratioProjection(c.C12, c.C37, c.C36))
  c.C41 = n(c.C40)
  c.C42 = isNumber(c.C37) ? projected : unfounded(context, projected)
  c.C43 = isNumber(c.C37) ? guard(() => n(c.C41) + required(c.C42)) : null
  // Fehlt s_q (C39), rechnet die Vorlage mit 0; die Webfassung ebenso und weist es aus (`zeroAssumed`).
  c.C44 = guard(() => divide(required(c.C13) * required(c.C17) * n(c.C39), squareRoot(required(c.C34))))
}

/** Berechnet alle Formelzellen des Blatts 08; Eingaben und Ergebnisse tragen die Zelladressen der Vorlage. */
export function compute(inputs: CellMap, context: SheetContext): CellMap {
  const c = resolveInputs(definition, inputs, context)
  parameters(c, context)
  const pending = sampleSize(c)
  projection(c, context)
  conclusion(c, 43, { bookValue: 'C7', testType: 'C16', materiality: 'C19' }, pending)
  summary(c, { method: 'Einfaches Zufallsstichprobenverfahren, 1 Zeitraum', bookValue: 'C7', first: 43, exhaustive: 'C41', sampleSize: c.C35 })
  return c
}
