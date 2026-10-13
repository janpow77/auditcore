/** Blatt 17_Unterstichprobe: Fehler einer Stichprobeneinheit aus einer Unterstichprobe; in der Webfassung eine Liste von Einheiten. */
import { isNumber, sameText } from '../../excel/index'
import { defineSheet, type SubsampleTotals } from '../../model/sheet'
import type { CellMap, SheetContext } from '../../model/types'
import { compute } from './compute'
import { definition } from './definition'
import { deviations } from './deviations'

/** Erfundene Beispieleinheit; sie stammt aus keiner Prüfung. */
const sample: CellMap = { C5: 'Beispiel-Vorhaben 17', C6: 250000, C7: 140, C10: 30, C11: 61000, C12: 915, W5: 'Zufallsschicht', W6: 'Variante 1' }

const add = (total: number | null, value: number): number => (total ?? 0) + value

/**
 * Summen über alle Einheiten: Fehler der hochwertigen Einheiten (ΣE_e) sowie
 * Fehlerquoten, Fehler und Buchwerte der Einheiten der Zufallsschicht.
 * Einheiten ohne bestimmbaren Fehler zählen als unvollständig und gehen nicht ein.
 */
function totals(rows: readonly CellMap[], context: SheetContext): SubsampleTotals {
  const sums: { -readonly [K in keyof SubsampleTotals]: SubsampleTotals[K] } = { highValueErrors: null, errorRateSum: null, errorSum: null, bookValueSum: null, units: rows.length, incomplete: 0 }
  for (const row of rows) {
    const cells = compute(row, context)
    const { W7: error, W8: rate, C6: bookValue } = cells
    if (!isNumber(error) || !isNumber(rate) || !isNumber(bookValue)) sums.incomplete += 1
    else if (sameText(cells.W5, 'hochwertige Einheit')) sums.highValueErrors = add(sums.highValueErrors, error)
    else {
      sums.errorRateSum = add(sums.errorRateSum, rate)
      sums.errorSum = add(sums.errorSum, error)
      sums.bookValueSum = add(sums.bookValueSum, bookValue)
    }
  }
  return sums
}

export const sheet = defineSheet({ id: '17_Unterstichprobe', definition, compute, sample: { inputs: sample }, deviations, totals })
