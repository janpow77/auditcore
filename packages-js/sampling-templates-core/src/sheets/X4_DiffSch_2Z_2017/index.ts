/** Blatt X4_DiffSch_2Z_2017: Differenzschätzung über zwei Zeiträume der Vorlage von 2017 (weitere Methode nach Art. 79). */
import { isBlank, isNumber } from '../../excel/index'
import { defineSheet, type ZeroAssumption } from '../../model/sheet'
import type { CellMap, WebHint } from '../../model/types'
import { belowThreeUnits, negativeSize, partialErrorSums, sizeExceedsPopulation, tolerableNotAboveAnticipated } from '../shared/legacy'
import { compute } from './compute'
import { definition } from './definition'
import { deviations } from './deviations'
import { en } from './texts.en'

/** Erfundene Beispielwerte für beide Zeiträume; sie stammen aus keiner Prüfung. */
const sample: CellMap = {
  C2: 'Vorhaben',
  C3: 26000000, C4: 22500000, C5: 230, C6: 190, C7: 9000, C8: 9500, C10: 0.9, C12: 0.005,
  C20: 4800000, C21: 21000, C22: 2700,
  C23: 9800, C25: 23100000, C26: 205, C27: 0.006,
  C33: 2600000, C34: 14000, C35: 3100,
}

const FIRST = 'TE ≤ AE im ersten Zeitraum: Die Altvorlage prüft das nicht; der ausgewiesene Stichprobenumfang ist nicht belastbar'
const SECOND = 'TE ≤ AE im zweiten Zeitraum: Die Altvorlage prüft das nicht; der neu berechnete Stichprobenumfang ist nicht belastbar'
const NEGATIVE = 'Negativer Nenner bei der Neuberechnung des Stichprobenumfangs für den zweiten Zeitraum: Die Altvorlage prüft das nicht; Umfang und Folgegrößen sind nicht belastbar'

/** Hinweise der Webfassung zu Blatt X4; sie verändern kein Rechenergebnis. */
function webHints(inputs: CellMap, results: CellMap): WebHint[] {
  const hints: WebHint[] = [
    ...tolerableNotAboveAnticipated(results.C15, results.C13, FIRST, 'tolerable-error-not-above-anticipated-1'),
    ...tolerableNotAboveAnticipated(results.C30, results.C28, SECOND, 'tolerable-error-not-above-anticipated-2'),
  ]
  hints.push(
    ...negativeSize(results.C31, 'negative-denominator', NEGATIVE),
    ...sizeExceedsPopulation(results.C17, results.C5),
    ...(sizeExceedsPopulation(results.C31, results.C26).length ? [{ id: 'size-exceeds-population-2', tone: 'warning' as const, text: 'Neu berechneter Stichprobenumfang übersteigt die Anzahl der Einheiten des zweiten Zeitraums' }] : []),
    ...belowThreeUnits([results.C17, results.C18, results.C31], 'Stichprobe eines Zeitraums mit weniger als drei Einheiten (Fußnote der Altvorlage: mindestens 3)'),
  )
  return hints
}

/**
 * Mit 0 gerechnete Eingaben. Fehler der Stichprobe eines Zeitraums (C21, C34;
 * `partialErrorSum`): Trägt der andere Zeitraum einen, zählt der fehlende in
 * der Vorlage 0. Standardabweichung der Fehler in der Stichprobe des zweiten
 * Zeitraums (C35; `sampleDeviation`): Ihr Beitrag zur Genauigkeit zählt 0. Die
 * Webfassung zeigt die Werte und weist beides aus. Die Standardabweichung des
 * ersten Zeitraums (C22) ist dagegen Pflichteingabe: Sie geht in die
 * Neuberechnung des Umfangs (C31) ein.
 */
function zeroAssumed(results: CellMap): ZeroAssumption[] {
  const assumed: ZeroAssumption[] = isNumber(results.C36) ? partialErrorSums(results, ['C21', 'C34'], () => ['C36', 'C37', 'C38', 'C41', 'C42']) : []
  if (isBlank(results.C35) && isNumber(results.C39)) assumed.push({ input: 'C35', cells: ['C39', 'C40', 'C41', 'C42'] })
  return assumed
}

export const sheet = defineSheet({ id: 'X4_DiffSch_2Z_2017', definition, compute, sample: { inputs: sample }, deviations, webHints, zeroAssumed, translations: { en } })
