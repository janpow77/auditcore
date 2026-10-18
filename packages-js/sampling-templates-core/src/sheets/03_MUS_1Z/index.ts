/** Blatt 03_MUS_1Z: MUS-Standardansatz, ein Stichprobenzeitraum, nicht geschichtet. */
import { gt, isBlank, isNumber, sameNumber } from '../../excel/index'
import { defineSheet, type ZeroAssumption } from '../../model/sheet'
import type { CellMap, WebHint } from '../../model/types'
import { compute } from './compute'
import { definition } from './definition'
import { deviations } from './deviations'
import { en } from './texts.en'
import { komPlanningHints } from '../shared/kom'

/** Erfundene Beispielwerte; sie stammen aus keiner Prüfung. */
const sample: CellMap = {
  C4: 'Beispiel – EFRE-Programm',
  C5: '2025/2026',
  C6: 'Zahlungsantrag des Begünstigten',
  C7: 48500000,
  C8: 420,
  C9: 'mittel',
  C10: 0.7,
  C11: 'zweiseitig',
  C14: 0.02,
  C17: 0.007,
  C20: 0.12,
  C22: 2,
  C23: 'Nein',
  C24: 'Nein',
  C29: 4,
  C30: 6200000,
  C35: 0,
  C37: 18400,
  C38: 0.62,
  C39: 0.045,
  C44: 0,
  C45: 0,
}

/** Hinweise der Webfassung zu Blatt 03; sie verändern kein Rechenergebnis. */
function webHints(inputs: CellMap, results: CellMap): WebHint[] {
  const hints: WebHint[] = []
  const size = results.C27
  const units = results.C8
  if (isNumber(size) && isNumber(units) && gt(size, units)) {
    hints.push({ id: 'size-exceeds-population', tone: 'warning', text: 'Stichprobenumfang übersteigt die Anzahl der Einheiten der Grundgesamtheit' })
  }
  if (sameNumber(results.C10, 0.95)) {
    hints.push({ id: 'confidence-outside-annex', tone: 'warning', text: 'Konfidenzniveau 95 % liegt außerhalb der Tabelle in Anhang I' })
  }
  return [...hints, ...komPlanningHints(definition, results)]
}

/**
 * Fehlt die Standardabweichung der Stichprobe (C39), rechnet die Vorlage die
 * Genauigkeit mit 0 (Entscheidung des Auftraggebers: Wert zeigen und ausweisen).
 */
function zeroAssumed(results: CellMap): ZeroAssumption[] {
  if (!isBlank(results.C39) || !isNumber(results.C43)) return []
  return [{ input: 'C39', cells: ['C43', 'C46', 'C47', 'C48', 'C51', 'C52'] }]
}

export const sheet = defineSheet({ id: '03_MUS_1Z', definition, compute, sample: { inputs: sample }, deviations, webHints, zeroAssumed, translations: { en } })
