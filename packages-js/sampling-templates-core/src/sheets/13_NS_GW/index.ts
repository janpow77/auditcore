/** Blatt 13_NS_GW: nichtstatistisches Verfahren, Auswahl mit gleicher Wahrscheinlichkeit, nicht geschichtet. */
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
  C10: 620000,
  C11: 4,
  C13: 22,
  C17: 640000,
  C18: 5300,
  C19: 1200,
  C23: 0,
  C24: 0,
  C27: 0.02,
}

/** Hinweise der Webfassung zu Blatt 13; sie verändern kein Rechenergebnis. */
function webHints(_inputs: CellMap, results: CellMap): WebHint[] {
  return hintIf(exceeds(results.C14, results.C8), 'size-exceeds-population')
}

export const sheet = defineSheet({ id: '13_NS_GW', definition, compute, sample: { inputs: sample }, deviations, webHints, translations: { en } })
