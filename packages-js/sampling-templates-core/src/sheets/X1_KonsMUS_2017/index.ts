/** Blatt X1_KonsMUS_2017: konservativer MUS-Ansatz der Vorlage von 2017 (weitere Methode nach Art. 79). */
import { isNumber } from '../../excel/index'
import { defineSheet } from '../../model/sheet'
import type { CellMap, WebHint } from '../../model/types'
import { sizeExceedsPopulation, tolerableNotAboveAnticipated } from '../shared/legacy'
import { compute } from './compute'
import { definition } from './definition'
import { deviations } from './deviations'
import { en } from './texts.en'

/** Erfundene Beispielwerte; sie stammen aus keiner Prüfung. */
const sample: CellMap = { C1: 48500000, C2: 'Vorhaben', C3: 420, C4: 0.9, C7: 0.005, C13: 18400, C14: 0.62, C16: 95000 }

/** Hinweise der Webfassung zu Blatt X1; sie verändern kein Rechenergebnis. */
function webHints(inputs: CellMap, results: CellMap): WebHint[] {
  const { C8: anticipated, C6: expansion } = results
  const expanded = isNumber(anticipated) && isNumber(expansion) ? anticipated * expansion : null
  return [
    ...tolerableNotAboveAnticipated(results.C10, expanded, 'TE ≤ AE × EF: Die Altvorlage prüft das nicht. Stichprobenumfang und Folgegrößen sind, soweit wie in der Vorlage gezeigt, nicht belastbar; bitte die erwartete Fehlerquote prüfen'),
    ...sizeExceedsPopulation(results.C11, results.C3),
  ]
}

export const sheet = defineSheet({ id: 'X1_KonsMUS_2017', definition, compute, sample: { inputs: sample }, deviations, webHints, translations: { en } })
