/** Blatt 16_NS_PPS_S: nichtstatistisches Verfahren, wertproportionale Auswahl (PPS), geschichtet. */
import { defineSheet, type ZeroAssumption } from '../../model/sheet'
import type { CellMap, WebHint } from '../../model/types'
import { exceeds, hintIf, strataHints, strataZeroAssumed, type StrataRows } from '../shared/nonstatistical'
import { compute } from './compute'
import { definition } from './definition'
import { deviations } from './deviations'
import { en } from './texts.en'

/** Schichtzeilen des Blatts: belegt ist eine Schicht mit Buchwert (Zeile 9). */
const ROWS: StrataRows = { key: 9, inputs: [10, 19, 20, 25, 26], errors: 26, projected: 28, total: 'C30' }

/** Erfundene Beispielwerte mit drei Schichten; sie stammen aus keiner Prüfung. */
const sample: CellMap = {
  C4: 'Beispiel – EFRE-Programm',
  C5: '2025/2026',
  C6: 'Vorhaben',
  D9: 1900000, E9: 1500000, F9: 830000,
  D10: 80, E10: 60, F10: 36,
  C13: 22,
  D19: 2, E19: 1, F19: 0,
  D20: 520000, E20: 260000, F20: 0,
  D25: 1800, E25: 0, F25: 0,
  D26: 0.062, E26: 0.048, F26: 0.021,
  C31: 0,
  C32: 0,
  C35: 0.02,
}

/** Hinweise der Webfassung zu Blatt 16; sie verändern kein Rechenergebnis. */
function webHints(inputs: CellMap, results: CellMap): WebHint[] {
  return [
    ...hintIf(exceeds(results.C15, results.C13), 'strata-sum-exceeds-size'),
    ...hintIf(exceeds(results.C15, results.C11), 'size-exceeds-population'),
    ...strataHints(inputs, results, ROWS),
  ]
}

/**
 * Fehlt die Summe der Fehlerquoten einer belegten Schicht (Zeile 26), während
 * eine andere Schicht eine trägt, rechnet die Vorlage sie mit 0 (Zeile 28) –
 * Fallart `partialErrorSum` der Richtlinie.
 */
function zeroAssumed(results: CellMap): ZeroAssumption[] {
  return strataZeroAssumed(results, ROWS, ['C28', 'C30', 'C33', 'C34', 'C36', 'N5', 'N11'])
}

export const sheet = defineSheet({ id: '16_NS_PPS_S', definition, compute, sample: { inputs: sample }, deviations, webHints, zeroAssumed, translations: { en } })
