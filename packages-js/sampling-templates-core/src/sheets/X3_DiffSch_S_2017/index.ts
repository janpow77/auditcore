/** Blatt X3_DiffSch_S_2017: geschichtete Differenzschätzung der Vorlage von 2017 (weitere Methode nach Art. 79). */
import { gt, isBlank, isNumber, ne, sum } from '../../excel/index'
import { defineSheet, type ZeroAssumption } from '../../model/sheet'
import { stratumCell as at } from '../../model/strata'
import type { CellMap, WebHint } from '../../model/types'
import { LEGACY_STRATA, LEGACY_TEMPLATE_STRATA, TOLERABLE_HINT, levelAdaptations, levelOutsideSteps, partialErrorSums, sizeExceedsPopulation, strataBelowThreeUnits, tolerableNotAboveAnticipated } from '../shared/legacy'
import { compute, usedStrata } from './compute'
import { definition } from './definition'
import { deviations } from './deviations'
import { en } from './texts.en'

/** Erfundene Beispielwerte mit drei Schichten; sie stammen aus keiner Prüfung. */
const sample: CellMap = {
  D2: 'Vorhaben',
  E6: 24000000, F6: 16500000, G6: 8000000,
  E7: 210, F7: 150, G7: 60,
  E8: 9000, F8: 11000, G8: 7500,
  D9: 0.9, D11: 0.005,
  E18: 4100000, F18: 2900000, G18: 1700000,
  E19: 15000, F19: 12000, G19: 4000,
  E21: 2800, F21: 3300, G21: 2100,
}

/** Summe der Schichtumfänge (Zeile 17) über die belegten Schichten. */
function allocated(results: CellMap, used: readonly string[]): number {
  return sum(used.map((column) => results[at(column, 17)]))
}

/** Hinweise der Webfassung zu Blatt X3; sie verändern kein Rechenergebnis. */
function webHints(inputs: CellMap, results: CellMap): WebHint[] {
  const used = usedStrata(results)
  const hints: WebHint[] = [...tolerableNotAboveAnticipated(results.D14, results.D12, TOLERABLE_HINT), ...sizeExceedsPopulation(results.D15, results.D3), ...levelOutsideSteps(inputs.D9)]
  if (isNumber(results.D15) && gt(allocated(results, used), results.D15)) {
    hints.push({ id: 'strata-sum-exceeds-size', tone: 'warning', text: 'Summe der aufgerundeten Schichtumfänge ist größer als der geplante Stichprobenumfang' })
  }
  hints.push(...strataBelowThreeUnits(used.map((column) => [LEGACY_STRATA.indexOf(column) + 1, results[at(column, 17)]])))
  if (used.some((column) => !LEGACY_TEMPLATE_STRATA.includes(column))) {
    hints.push({ id: 'strata-beyond-template', tone: 'neutral', text: 'Mehr als sieben Schichten: Die Vorlage sieht sieben Spalten vor; die 8. bis 20. Schicht ist eine Erweiterung der Webfassung' })
  }
  // Leere Schicht zwischen belegten: Die Schichttabelle zeigt nicht zwingend alle belegten Spalten.
  const positions = used.map((column) => LEGACY_STRATA.indexOf(column) + 1)
  if (positions.some((position, index) => ne(position, index + 1))) {
    hints.push({ id: 'strata-gap', tone: 'neutral', text: `Leere Schicht zwischen belegten Schichten: Belegt sind die Schichten ${positions.join(', ')}` })
  }
  return hints
}

/** Zellen, die vom Fehler der Stichprobe einer Schicht abhängen (Zeilen 20 und 22, Hochrechnung). */
const errorCells = (input: string): string[] => {
  const column = input.replace(/\d+$/, '')
  return [at(column, 20), at(column, 22), 'D23', 'D24', 'D25', 'D28', 'D29']
}

/**
 * Mit 0 gerechnete Eingaben belegter Schichten. Standardabweichung der Fehler
 * in der Stichprobe (Zeile 21, `sampleDeviation`): Ihr Beitrag zur Genauigkeit
 * zählt in der Vorlage 0. Fehler der Stichprobe (Zeile 19, `partialErrorSum`):
 * Trägt eine andere Schicht einen, zählt der fehlende 0. Die Webfassung zeigt
 * die Werte und weist beides aus.
 */
function zeroAssumed(results: CellMap): ZeroAssumption[] {
  const used = usedStrata(results)
  const errors = isNumber(results.D23) ? partialErrorSums(results, used.map((column) => at(column, 19)), errorCells) : []
  const deviations = isNumber(results.D26) ? used.filter((column) => isBlank(results[at(column, 21)])).map((column) => ({ input: at(column, 21), cells: ['D26', 'D27', 'D28', 'D29'] })) : []
  return [...errors, ...deviations]
}

export const sheet = defineSheet({ id: 'X3_DiffSch_S_2017', definition, compute, sample: { inputs: sample }, deviations, webHints, zeroAssumed, adapted: levelAdaptations(['D10']), translations: { en } })
