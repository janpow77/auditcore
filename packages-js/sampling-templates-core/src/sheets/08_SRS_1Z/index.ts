/** Blatt 08_SRS_1Z: einfaches Zufallsstichprobenverfahren (Verhältnisschätzung), ein Stichprobenzeitraum, nicht geschichtet. */
import { gt, isBlank, isNumber, sameNumber } from '../../excel/index'
import { defineSheet, type ZeroAssumption } from '../../model/sheet'
import type { CellMap, SheetContext, WebHint } from '../../model/types'
import { precisionCells } from '../shared/srs'
import { exclusionReference } from '../shared/delvo'
import { compute } from './compute'
import { definition } from './definition'
import { deviations } from './deviations'
import { en } from './texts.en'

/** Erfundene Beispielwerte; sie stammen aus keiner Prüfung. */
const sample: CellMap = {
  C4: 'Beispiel – EFRE-Programm',
  C5: '2025/2026',
  C6: 'Zahlungsantrag des Begünstigten',
  C7: 48500000,
  C8: 420,
  C9: 6200000,
  C10: 4,
  C11: 2,
  C14: 'mittel',
  C15: 0.7,
  C16: 'zweiseitig',
  C19: 0.02,
  C22: 0.007,
  C25: 9000,
  C27: 2,
  C28: 'Nein',
  C29: 'Nein',
  C36: 3900000,
  C37: 21000,
  C38: 2600,
  C39: 2400,
  C40: 18400,
  C45: 0,
  C46: 0,
}

/** Hinweise der Webfassung zu Blatt 08; sie verändern kein Rechenergebnis. */
function webHints(inputs: CellMap, results: CellMap, context?: SheetContext): WebHint[] {
  const hints: WebHint[] = []
  const { C34: size, C13: units } = results
  if (isNumber(size) && isNumber(units) && gt(size, units)) {
    hints.push({ id: 'size-exceeds-population', tone: 'warning', text: 'Stichprobenumfang übersteigt die Anzahl der Einheiten der Grundgesamtheit' })
  }
  if (sameNumber(results.C15, 0.95)) {
    hints.push({ id: 'confidence-outside-annex', tone: 'warning', text: 'Konfidenzniveau 95 % liegt außerhalb der Tabelle in Anhang I' })
  }
  return [...hints, ...exclusionReference(context)]
}

/**
 * Fehlt die Standardabweichung der Variablen q in der Stichprobe (C39), rechnet
 * die Vorlage die Genauigkeit mit 0; die Webfassung zeigt den Wert und weist ihn aus.
 */
function zeroAssumed(results: CellMap): ZeroAssumption[] {
  if (!isBlank(results.C39) || !isNumber(results.C44)) return []
  return [{ input: 'C39', cells: precisionCells(43) }]
}

export const sheet = defineSheet({ id: '08_SRS_1Z', definition, compute, sample: { inputs: sample }, deviations, webHints, zeroAssumed, translations: { en } })
