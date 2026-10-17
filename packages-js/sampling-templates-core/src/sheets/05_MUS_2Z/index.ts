/** Blatt 05_MUS_2Z: MUS-Standardansatz, zwei Stichprobenzeiträume, nicht geschichtet. */
import { gt, isBlank, isNumber, le, sameNumber } from '../../excel/index'
import { defineSheet, type ZeroAssumption } from '../../model/sheet'
import type { CellMap, SheetContext, WebHint } from '../../model/types'
import { approachOf, errorDependents, limitWithoutSize, partialErrorSums } from '../shared/mus'
import { withNotApplicableNote } from '../shared/delvo'
import { compute } from './compute'
import { definition } from './definition'
import { deviations } from './deviations'
import { en } from './texts.en'
import { annexIIIApproximation, komPlanningHints } from '../shared/kom'

const STANDARD = 'Standard (Art. 5 Abs. 6 Buchst. a)'

/** Erfundene Beispielwerte; sie stammen aus keiner Prüfung. */
const sample: CellMap = {
  C4: 'Beispiel – EFRE-Programm',
  C5: '2025/2026',
  C6: 'Zahlungsantrag des Begünstigten',
  C7: 26000000, C8: 22500000, C9: 230, C10: 190,
  C12: 'mittel', C13: 0.7, C14: 'zweiseitig', C17: 0.02, C20: 0.007, C23: 0.12, C24: 0.12, C26: STANDARD,
  C28: 2, C29: 'Nein', C30: 'Nein',
  C37: 3, C38: 2400000, C43: 0, C45: 5000, C46: 0.3, C47: 0.05,
  C48: 24000000, C49: 200, C50: 0.11,
  C71: 2, C72: 1800000, C77: 0, C80: 0, C81: 0.25, C82: 0.04,
  C87: 0, C88: 0,
}

/** Hinweis: Stichprobenumfang eines Zeitraums übersteigt die Anzahl seiner Einheiten. */
function exceeds(results: CellMap, size: string, units: string, period: number): WebHint[] {
  const [n, total] = [results[size], results[units]]
  if (!isNumber(n) || !isNumber(total) || !gt(n, total)) return []
  return [{ id: `size-exceeds-population-${period}`, tone: 'warning', text: `Stichprobenumfang für Zeitraum ${period} übersteigt die Anzahl der Einheiten des Zeitraums` }]
}

/** Hinweise der Webfassung zu Blatt 05; sie verändern kein Rechenergebnis. */
function webHints(inputs: CellMap, results: CellMap, context?: SheetContext): WebHint[] {
  const hints: WebHint[] = [...limitWithoutSize(results, 'C32', 'C27', 'C33'), ...exceeds(results, 'C66', 'C9', 1), ...exceeds(results, 'C67', 'C49', 2)]
  if (approachOf(results.C26) === 'standard' && isNumber(results.C56) && le(results.C56, 0)) {
    hints.push({
      id: 'negative-denominator',
      tone: 'warning',
      text: 'Nenner der Standardneuberechnung ist nicht positiv: Der Standardansatz liefert keinen Umfang für Zeitraum 2. Sind alle Pflichteingaben vorhanden, zeigt die Webfassung wie die Vorlage nur die Untergrenze 3 bzw. die Auffüllung auf 30 und rechnet damit weiter; das Ergebnis ist nicht belastbar. Empfohlen: globale Neuberechnung',
    })
  }
  if (sameNumber(results.C13, 0.95)) hints.push({ id: 'confidence-outside-annex', tone: 'warning', text: 'Konfidenzniveau 95 % liegt außerhalb der Tabelle in Anhang I' })
  return withNotApplicableNote([...hints, ...komPlanningHints(definition, results), ...annexIIIApproximation(context, false)])
}

/** Zellen, die von der Genauigkeit abhängen: SE, Fehlergrenzen, relative Genauigkeit, obere Grenze in %, Würdigung. */
const PRECISION_CELLS = ['C86', 'C89', 'C90', 'C91', 'C94', 'C95']

/** Zellen, die von der Summe der Fehlerquoten eines Zeitraums abhängen: EE_s, EE, Fehlergrenzen, Quoten, Würdigung, N5 und N11. */
const ERROR_CELLS = ['C84', ...errorDependents(85)]

/**
 * Fehlt die Standardabweichung der Stichprobe eines Zeitraums (C47, C82),
 * rechnet die Vorlage dessen Beitrag zur Genauigkeit mit 0. Fehlt die Summe der
 * Fehlerquoten eines Zeitraums (C46, C81), während die des anderen eingetragen
 * ist, rechnet sie dessen Beitrag zur Hochrechnung mit 0.
 */
function zeroAssumed(results: CellMap): ZeroAssumption[] {
  const sums = partialErrorSums(results, 'C85', [['C46', ERROR_CELLS], ['C81', ERROR_CELLS]])
  if (!isNumber(results.C86)) return sums
  return [...['C47', 'C82'].filter((input) => isBlank(results[input])).map((input) => ({ input, cells: PRECISION_CELLS })), ...sums]
}

export const sheet = defineSheet({ id: '05_MUS_2Z', definition, compute, sample: { inputs: sample }, deviations, webHints, zeroAssumed, translations: { en } })
