/** Blatt 15_NS_PPS: nichtstatistisches Verfahren, wertproportionale Auswahl (PPS), nicht geschichtet. */
import { defineSheet } from '../../model/sheet'
import type { CellMap, WebHint } from '../../model/types'
import { exceeds, hintIf } from '../shared/nonstatistical'
import { compute } from './compute'
import { definition } from './definition'
import { deviations } from './deviations'
import { en } from './texts.en'

/** Erfundene Beispielwerte; sie stammen aus keiner Prüfung. */
const sample: CellMap = {
  C4: 'Beispiel – EFRE-Programm',
  C5: '2025/2026',
  C6: 'Vorhaben',
  C7: 4850000,
  C8: 180,
  C10: 24,
  C14: 3,
  C15: 1150000,
  C20: 0,
  C22: 2400,
  C23: 0.085,
  C27: 0,
  C28: 0,
  C31: 0.02,
}

/** Hinweise der Webfassung zu Blatt 15; sie verändern kein Rechenergebnis. */
function webHints(_inputs: CellMap, results: CellMap): WebHint[] {
  return hintIf(exceeds(results.C10, results.C8), 'size-exceeds-population')
}

export const sheet = defineSheet({ id: '15_NS_PPS', definition, compute, sample: { inputs: sample }, deviations, webHints, translations: { en } })
