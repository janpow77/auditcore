/** Blatt 12_SRS_3Z: einfaches Zufallsstichprobenverfahren (Verhältnisschätzung), drei Stichprobenzeiträume, nicht geschichtet. */
import { gt, isBlank, isNumber, le, sameNumber } from '../../excel/index'
import { defineSheet, type ZeroAssumption } from '../../model/sheet'
import type { CellAddress, CellMap, SheetContext, WebHint } from '../../model/types'
import { precisionCells, projectionCells, recalculationOf } from '../shared/srs'
import { exclusionReference, globalWithoutMargin, withNotApplicableNote } from '../shared/delvo'
import { compute } from './compute'
import { definition } from './definition'
import { deviations } from './deviations'
import { en } from './texts.en'

/** Erfundene Beispielwerte; sie stammen aus keiner Prüfung. */
const sample: CellMap = {
  C4: 'Beispiel – EFRE-Programm',
  C5: '2025/2026',
  C6: 'Zahlungsantrag des Begünstigten',
  C7: 20000000, C8: 180, C9: 2400000, C10: 3, C11: 1,
  C14: 16000000, C15: 150, C16: 12500000, C17: 110,
  C20: 'mittel', C21: 0.7, C22: 'zweiseitig', C25: 0.02, C28: 0.007,
  C31: 9000, C32: 9500, C33: 8800, C35: 'Standard (Art. 5 Abs. 6 Buchst. a)',
  C37: 2, C38: 'Nein', C39: 'Nein',
  C48: 1900000, C49: 9500, C50: 8200, C51: 2400, C52: 6200,
  C53: 15200000, C54: 146, C55: 1100000, C56: 2, C57: 1,
  C60: 13000000, C61: 115, C62: 9200, C63: 8700,
  C87: 1400000, C88: 7800, C89: 7900, C90: 2300, C91: 0,
  C92: 13400000, C93: 121, C94: 900000, C95: 1, C96: 0, C99: 8600,
  C121: 800000, C122: 5200, C123: 7000, C124: 2500, C125: 0,
  C130: 0, C131: 0,
}

/** Hinweis: Stichprobenumfang eines Zeitraums übersteigt die Anzahl der Einheiten seiner Zufallsschicht. */
function exceeds(results: CellMap, size: CellAddress, units: CellAddress, period: number): WebHint[] {
  const [n, total] = [results[size], results[units]]
  if (!isNumber(n) || !isNumber(total) || !gt(n, total)) return []
  return [{ id: `size-exceeds-population-${period}`, tone: 'warning', text: `Stichprobenumfang für Zeitraum ${period} übersteigt die Anzahl der Einheiten der Zufallsschicht des Zeitraums` }]
}

/** Hinweis: Nenner der Standardneuberechnung nicht positiv; der Umfang beruht dann nur auf den Untergrenzen. */
function negativeDenominator(results: CellMap, denominator: CellAddress, period: number, floor: string): WebHint[] {
  const value = results[denominator]
  if (recalculationOf(results.C35) !== 'standard' || !isNumber(value) || !le(value, 0)) return []
  return [{ id: `negative-denominator-${period}`, tone: 'warning', text: `Nenner der Standardneuberechnung ist nicht positiv: Der anzuwendende Umfang für Zeitraum ${period} beruht nur auf den Untergrenzen (${floor})` }]
}

/** Hinweise der Webfassung zu Blatt 12; sie verändern kein Rechenergebnis. */
function webHints(inputs: CellMap, results: CellMap, context?: SheetContext): WebHint[] {
  const hints: WebHint[] = [
    ...exceeds(results, 'C116', 'C13', 1),
    ...exceeds(results, 'C117', 'C59', 2),
    ...exceeds(results, 'C118', 'C98', 3),
    ...negativeDenominator(results, 'C71', 2, 'mindestens 3'),
    ...negativeDenominator(results, 'C105', 3, 'mindestens 3, Auffüllung auf 30'),
  ]
  if (sameNumber(results.C21, 0.95)) hints.push({ id: 'confidence-outside-annex', tone: 'warning', text: 'Konfidenzniveau 95 % liegt außerhalb der Tabelle in Anhang I' })
  return withNotApplicableNote([...hints, ...globalWithoutMargin(results, 'C35', { size: 'C77' }, 2), ...globalWithoutMargin(results, 'C35', { size: 'C109' }, 3), ...exclusionReference(context)])
}

/** Standardabweichungen der Variablen q in den Stichproben der drei Zeiträume (s_q). */
const RATIO_DEVIATIONS: readonly CellAddress[] = ['C51', 'C90', 'C124']

/** Summen der Fehler der Stichproben der drei Zeiträume (Σ E_i). */
const ERROR_SUMS: readonly CellAddress[] = ['C49', 'C88', 'C122']

/**
 * Mit 0 gerechnete Eingaben: Fehlt die Standardabweichung der Variablen q in der
 * Stichprobe eines Zeitraums (C51, C90, C124), rechnet die Vorlage dessen Beitrag
 * zur Genauigkeit mit 0. Fehlt die Fehlersumme eines Zeitraums (C49, C88, C122),
 * während ein anderer eine trägt, zählt sie in der Hochrechnung 0 (`N(…)` in
 * C127). Die Webfassung zeigt die Werte und weist sie je fehlender Eingabe aus.
 */
function zeroAssumed(results: CellMap): ZeroAssumption[] {
  const lacking = (inputs: readonly CellAddress[], result: CellAddress): CellAddress[] => (isNumber(results[result]) ? inputs.filter((input) => isBlank(results[input])) : [])
  return [
    ...lacking(RATIO_DEVIATIONS, 'C129').map((input): ZeroAssumption => ({ input, cells: precisionCells(128) })),
    ...lacking(ERROR_SUMS, 'C128').map((input): ZeroAssumption => ({ input, cells: ['C127', ...projectionCells(128)], kind: 'partialErrorSum' })),
  ]
}

export const sheet = defineSheet({ id: '12_SRS_3Z', definition, compute, sample: { inputs: sample }, deviations, webHints, zeroAssumed, translations: { en } })
