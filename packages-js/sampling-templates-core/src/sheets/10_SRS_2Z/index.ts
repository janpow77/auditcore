/** Blatt 10_SRS_2Z: einfaches Zufallsstichprobenverfahren (Verhältnisschätzung), zwei Stichprobenzeiträume, nicht geschichtet. */
import { gt, isBlank, isNumber, le, sameNumber } from '../../excel/index'
import { defineSheet, type ZeroAssumption } from '../../model/sheet'
import type { CellAddress, CellMap, WebHint } from '../../model/types'
import { precisionCells, projectionCells, recalculationOf } from '../shared/srs'
import { compute } from './compute'
import { definition } from './definition'
import { deviations } from './deviations'
import { en } from './texts.en'

/** Erfundene Beispielwerte; sie stammen aus keiner Prüfung. */
const sample: CellMap = {
  C4: 'Beispiel – EFRE-Programm',
  C5: '2025/2026',
  C6: 'Zahlungsantrag des Begünstigten',
  C7: 26000000, C8: 230, C9: 3000000, C10: 3, C11: 2, C14: 22500000, C15: 190,
  C18: 'mittel', C19: 0.7, C20: 'zweiseitig', C23: 0.02, C26: 0.007, C29: 9000, C30: 9000, C32: 'Standard (Art. 5 Abs. 6 Buchst. a)',
  C34: 2, C35: 'Nein', C36: 'Nein',
  C44: 2400000, C45: 14000, C46: 2600, C47: 2400, C48: 9000,
  C49: 24000000, C50: 200, C51: 2000000, C52: 2, C53: 1, C56: 8500, C57: 0.008,
  C77: 880000, C78: 5000, C79: 2000, C80: 2100, C81: 1500,
  C86: 0, C87: 0,
}

/** Hinweis: Stichprobenumfang eines Zeitraums übersteigt die Anzahl der Einheiten seiner Zufallsschicht. */
function exceeds(results: CellMap, size: CellAddress, units: CellAddress, period: number): WebHint[] {
  const [n, total] = [results[size], results[units]]
  if (!isNumber(n) || !isNumber(total) || !gt(n, total)) return []
  return [{ id: `size-exceeds-population-${period}`, tone: 'warning', text: `Stichprobenumfang für Zeitraum ${period} übersteigt die Anzahl der Einheiten der Zufallsschicht des Zeitraums` }]
}

/** Hinweise der Webfassung zu Blatt 10; sie verändern kein Rechenergebnis. */
function webHints(inputs: CellMap, results: CellMap): WebHint[] {
  const hints: WebHint[] = [...exceeds(results, 'C72', 'C13', 1), ...exceeds(results, 'C73', 'C55', 2)]
  if (recalculationOf(results.C32) === 'standard' && isNumber(results.C62) && le(results.C62, 0)) {
    hints.push({
      id: 'negative-denominator',
      tone: 'warning',
      text: 'Nenner der Standardneuberechnung ist nicht positiv: Der anzuwendende Umfang für Zeitraum 2 beruht nur auf den Untergrenzen (mindestens 3, Auffüllung auf 30)',
    })
  }
  if (sameNumber(results.C19, 0.95)) hints.push({ id: 'confidence-outside-annex', tone: 'warning', text: 'Konfidenzniveau 95 % liegt außerhalb der Tabelle in Anhang I' })
  return hints
}

/**
 * Mit 0 gerechnete Eingaben: Fehlt die Standardabweichung der Variablen q in der
 * Stichprobe eines Zeitraums (C47, C80), rechnet die Vorlage dessen Beitrag zur
 * Genauigkeit mit 0. Fehlt die Fehlersumme eines Zeitraums (C45, C78), während
 * der andere eine trägt, zählt sie in der Hochrechnung 0 (`N(…)` in C83). Die
 * Webfassung zeigt die Werte und weist sie je Eingabe aus.
 */
function zeroAssumed(results: CellMap): ZeroAssumption[] {
  const lacking = (inputs: readonly CellAddress[], result: CellAddress): CellAddress[] => (isNumber(results[result]) ? inputs.filter((input) => isBlank(results[input])) : [])
  return [
    ...lacking(['C47', 'C80'], 'C85').map((input): ZeroAssumption => ({ input, cells: precisionCells(84) })),
    ...lacking(['C45', 'C78'], 'C84').map((input): ZeroAssumption => ({ input, cells: ['C83', ...projectionCells(84)], kind: 'partialErrorSum' })),
  ]
}

export const sheet = defineSheet({ id: '10_SRS_2Z', definition, compute, sample: { inputs: sample }, deviations, webHints, zeroAssumed, translations: { en } })
