/** Blatt 14_NS_GW_S: nichtstatistisches Verfahren, Auswahl mit gleicher Wahrscheinlichkeit, geschichtet. */
import { defineSheet, type ZeroAssumption } from '../../model/sheet'
import type { CellMap, WebHint } from '../../model/types'
import { exceeds, hintIf, strataHints, strataZeroAssumed, type StrataRows } from '../shared/nonstatistical'
import { compute } from './compute'
import { definition } from './definition'
import { deviations } from './deviations'
import { en } from './texts.en'

/** Schichtzeilen des Blatts: belegt ist eine Schicht mit Anzahl der Einheiten (Zeile 11). */
const ROWS: StrataRows = { key: 11, inputs: [12, 24, 25], errors: 25, projected: 27, total: 'C29' }

/** Erfundene Beispielwerte mit drei Schichten; sie stammen aus keiner Prüfung. */
const sample: CellMap = {
  C4: 'Beispiel – EFRE-Programm',
  C5: '2025/2026',
  C6: 'Vorhaben',
  C8: 620000,
  C9: 4,
  D11: 80, E11: 60, F11: 36,
  D12: 1900000, E12: 1500000, F12: 830000,
  C16: 22,
  C22: 1200,
  D24: 290000, E24: 230000, F24: 120000,
  D25: 2400, E25: 1900, F25: 1000,
  C30: 0,
  C31: 0,
  C34: 0.02,
}

/** Hinweise der Webfassung zu Blatt 14; sie verändern kein Rechenergebnis. */
function webHints(inputs: CellMap, results: CellMap): WebHint[] {
  return [
    ...hintIf(exceeds(results.C18, results.C16), 'strata-sum-exceeds-size'),
    ...hintIf(exceeds(results.C19, results.C14), 'size-exceeds-population'),
    ...strataHints(inputs, results, ROWS),
  ]
}

/**
 * Fehlt die Fehlersumme einer belegten Schicht (Zeile 25), während eine andere
 * Schicht eine trägt, rechnet die Vorlage ihren Fehler mit 0 (Zeile 27) –
 * Fallart `partialErrorSum` der Richtlinie.
 */
function zeroAssumed(results: CellMap): ZeroAssumption[] {
  return strataZeroAssumed(results, ROWS, ['C27', 'C29', 'C32', 'C33', 'C35', 'N5', 'N11'])
}

export const sheet = defineSheet({ id: '14_NS_GW_S', definition, compute, sample: { inputs: sample }, deviations, webHints, zeroAssumed, translations: { en } })
