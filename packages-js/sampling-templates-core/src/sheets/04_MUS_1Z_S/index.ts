/** Blatt 04_MUS_1Z_S: MUS-Standardansatz, ein Stichprobenzeitraum, geschichtet. */
import { gt, isBlank, isNumber, sameNumber } from '../../excel/index'
import { defineSheet, type ZeroAssumption } from '../../model/sheet'
import { STRATA_COLUMNS, TEMPLATE_STRATA, stratumCell, usedStrata } from '../../model/strata'
import type { CellMap, SheetContext, WebHint } from '../../model/types'
import { compute } from './compute'
import { definition } from './definition'
import { deviations } from './deviations'
import { en } from './texts.en'
import { annexIIIApproximation, komPlanningHints } from '../shared/kom'

/** Erfundene Beispielwerte mit drei Schichten; sie stammen aus keiner Prüfung. */
const sample: CellMap = {
  C4: 'Beispiel – EFRE-Programm',
  C5: '2025/2026',
  C6: 'Zahlungsantrag des Begünstigten',
  C7: 'zwischengeschaltete Stelle',
  D9: 24000000, E9: 16500000, F9: 8000000,
  D10: 210, E10: 150, F10: 60,
  C12: 'mittel', C13: 0.7, C14: 'zweiseitig', C17: 0.02, C20: 0.007,
  D24: 0.1, E24: 0.14, F24: 0.12,
  C28: 2, C29: 'Nein', C30: 'Nein',
  D37: 2, E37: 1, F37: 1,
  D38: 3100000, E38: 1900000, F38: 1200000,
  D43: 0, E43: 0, F43: 0,
  D45: 9200, E45: 0, F45: 9200,
  D46: 0.28, E46: 0.22, F46: 0.12,
  D47: 0.04, E47: 0.05, F47: 0.045,
  C55: 0, C56: 0,
}

/** Hinweise der Webfassung zu Blatt 04; sie verändern kein Rechenergebnis. */
function webHints(inputs: CellMap, results: CellMap, context?: SheetContext): WebHint[] {
  const hints: WebHint[] = []
  const { C33: size, C35: allocated, C10: units } = results
  if (isNumber(size) && isNumber(allocated) && gt(allocated, size)) {
    hints.push({ id: 'strata-sum-exceeds-size', tone: 'warning', text: 'Summe der aufgerundeten Schichtumfänge ist größer als der anzuwendende Stichprobenumfang' })
  }
  if (isNumber(size) && isNumber(units) && gt(units, 0) && gt(size, units)) {
    hints.push({ id: 'size-exceeds-population', tone: 'warning', text: 'Stichprobenumfang übersteigt die Anzahl der Einheiten der Grundgesamtheit' })
  }
  if (sameNumber(results.C13, 0.95)) hints.push({ id: 'confidence-outside-annex', tone: 'warning', text: 'Konfidenzniveau 95 % liegt außerhalb der Tabelle in Anhang I' })
  if (gt(usedStrata(inputs, [9]), TEMPLATE_STRATA.length)) {
    hints.push({ id: 'strata-beyond-template', tone: 'neutral', text: 'Mehr als sieben Schichten: Die Vorlage sieht sieben Spalten vor; die 8. bis 20. Schicht ist eine Erweiterung der Webfassung' })
  }
  return [...hints, ...komPlanningHints(definition, results), ...annexIIIApproximation(context, false)]
}

const used = (results: CellMap, column: string): boolean => !isBlank(results[stratumCell(column, 9)])

/**
 * Mit 0 gerechnete Eingaben (wie die Vorlage), die die Webfassung ausweist:
 * - Standardabweichung der Stichprobe einer belegten Schicht (Zeile 47): ihr
 *   Beitrag zur Genauigkeit ist 0 (Zeile 52).
 * - Summe der Fehlerquoten einer belegten Schicht (Zeile 46), während eine
 *   andere Schicht eine trägt: Die Vorlage rechnet ihre Hochrechnung mit 0 (Zeile 50).
 */
function zeroAssumed(results: CellMap): ZeroAssumption[] {
  const deviation = isNumber(results.C54)
    ? STRATA_COLUMNS.filter((column) => used(results, column) && isBlank(results[stratumCell(column, 47)])).map((column): ZeroAssumption => ({
        input: stratumCell(column, 47),
        cells: [stratumCell(column, 52), 'C52', 'C54', 'C57', 'C58', 'C59', 'C62', 'C63'],
      }))
    : []
  const errorSum = isNumber(results.C53)
    ? STRATA_COLUMNS.filter((column) => used(results, column) && isBlank(results[stratumCell(column, 46)])).map((column): ZeroAssumption => ({
        input: stratumCell(column, 46),
        cells: [stratumCell(column, 50), stratumCell(column, 51), 'C50', 'C51', 'C53', 'C57', 'C58', 'C60', 'C61', 'C62', 'C63', 'N5', 'N11'],
        kind: 'partialErrorSum',
      }))
    : []
  return [...deviation, ...errorSum]
}

export const sheet = defineSheet({ id: '04_MUS_1Z_S', definition, compute, sample: { inputs: sample }, deviations, webHints, zeroAssumed, translations: { en } })
