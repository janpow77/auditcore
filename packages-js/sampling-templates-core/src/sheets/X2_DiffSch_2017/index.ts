/** Blatt X2_DiffSch_2017: Differenzschätzung der Vorlage von 2017 (weitere Methode nach Art. 79). */
import { isBlank, isNumber } from '../../excel/index'
import { defineSheet, type ZeroAssumption } from '../../model/sheet'
import type { CellMap, WebHint } from '../../model/types'
import { TOLERABLE_HINT, sizeExceedsPopulation, tolerableNotAboveAnticipated } from '../shared/legacy'
import { compute } from './compute'
import { definition } from './definition'
import { deviations } from './deviations'
import { en } from './texts.en'

/** Erfundene Beispielwerte; sie stammen aus keiner Prüfung. */
const sample: CellMap = { C1: 48500000, C2: 'Vorhaben', C3: 420, C4: 9500, C5: 0.9, C7: 0.005, C12: 9200000, C13: 38000, C15: 2900 }

/** Hinweise der Webfassung zu Blatt X2; sie verändern kein Rechenergebnis. */
function webHints(inputs: CellMap, results: CellMap): WebHint[] {
  return [...tolerableNotAboveAnticipated(results.C10, results.C8, TOLERABLE_HINT), ...sizeExceedsPopulation(results.C11, results.C3)]
}

/**
 * Fehlt die Standardabweichung der Fehler in der Stichprobe (C15), rechnet die
 * Vorlage die Genauigkeit mit 0; die Webfassung zeigt die Werte und weist das aus.
 */
function zeroAssumed(results: CellMap): ZeroAssumption[] {
  if (!isBlank(results.C15) || !isNumber(results.C19)) return []
  return [{ input: 'C15', cells: ['C19', 'C20', 'C21', 'C22'] }]
}

export const sheet = defineSheet({ id: 'X2_DiffSch_2017', definition, compute, sample: { inputs: sample }, deviations, webHints, zeroAssumed, translations: { en } })
