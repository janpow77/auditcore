/** Blatt 09_SRS_1Z_S: einfaches Zufallsstichprobenverfahren (Verhältnisschätzung), ein Stichprobenzeitraum, geschichtet. */
import { gt, isBlank, isNumber, sameNumber } from '../../excel/index'
import { defineSheet, type ZeroAssumption } from '../../model/sheet'
import { STRATA_COLUMNS, TEMPLATE_STRATA, stratumCell, usedStrata } from '../../model/strata'
import type { CellMap, SheetContext, WebHint } from '../../model/types'
import { precisionCells, projectionCells } from '../shared/srs'
import { exclusionReference } from '../shared/delvo'
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
  C8: 6200000, C9: 4, C10: 2,
  D12: 206, E12: 150, F12: 60,
  D13: 20900000, E13: 14600000, F13: 6800000,
  C16: 'mittel', C17: 0.7, C18: 'zweiseitig', C21: 0.02, C24: 0.007,
  D28: 8000, E28: 11000, F28: 9500,
  C32: 2, C33: 'Nein', C34: 'Nein',
  C43: 18400,
  D45: 2100000, E45: 1400000, F45: 700000,
  D46: 10500, E46: 6200, F46: 4300,
  D47: 2200, E47: 2900, F47: 2500,
  C54: 0, C55: 0,
}

/** Hinweise der Webfassung zu Blatt 09; sie verändern kein Rechenergebnis. */
function webHints(inputs: CellMap, results: CellMap, context?: SheetContext): WebHint[] {
  const hints: WebHint[] = []
  const { C39: size, C41: allocated, C12: units } = results
  if (isNumber(size) && isNumber(allocated) && gt(allocated, size)) {
    hints.push({ id: 'strata-sum-exceeds-size', tone: 'warning', text: 'Summe der aufgerundeten Schichtumfänge ist größer als der anzuwendende Stichprobenumfang' })
  }
  if (isNumber(size) && isNumber(units) && gt(units, 0) && gt(size, units)) {
    hints.push({ id: 'size-exceeds-population', tone: 'warning', text: 'Stichprobenumfang übersteigt die Anzahl der Einheiten der Grundgesamtheit' })
  }
  if (sameNumber(results.C17, 0.95)) hints.push({ id: 'confidence-outside-annex', tone: 'warning', text: 'Konfidenzniveau 95 % liegt außerhalb der Tabelle in Anhang I' })
  if (gt(usedStrata(inputs, [12]), TEMPLATE_STRATA.length)) {
    hints.push({ id: 'strata-beyond-template', tone: 'neutral', text: 'Mehr als sieben Schichten: Die Vorlage sieht sieben Spalten vor; die 8. bis 20. Schicht ist eine Erweiterung der Webfassung' })
  }
  return [...hints, ...komPlanningHints(definition, results), ...exclusionReference(context), ...annexIIIApproximation(context, true)]
}

/** Belegte Schichten, deren Eingabe in `row` fehlt. */
function lackingStrata(results: CellMap, row: number): string[] {
  return STRATA_COLUMNS.filter((column) => !isBlank(results[stratumCell(column, 12)]) && isBlank(results[stratumCell(column, row)]))
}

/**
 * Mit 0 gerechnete Eingaben belegter Schichten: Fehlt die Standardabweichung der
 * Variablen q (Zeile 47), setzt die Vorlage ihren Beitrag zur Genauigkeit auf 0
 * (Zeile 50). Fehlt die Fehlersumme (Zeile 46), während eine andere Schicht eine
 * trägt, zählt sie in der Hochrechnung 0 (`N(…)` in Zeile 49).
 */
function zeroAssumed(results: CellMap): ZeroAssumption[] {
  const precision = isNumber(results.C53) ? lackingStrata(results, 47) : []
  const projection = isNumber(results.C52) ? lackingStrata(results, 46) : []
  return [
    ...precision.map((column): ZeroAssumption => ({ input: stratumCell(column, 47), cells: [stratumCell(column, 50), 'C50', ...precisionCells(52)] })),
    ...projection.map((column): ZeroAssumption => {
      const projected = stratumCell(column, 49)
      return { input: stratumCell(column, 46), cells: [...(isNumber(results[projected]) ? [projected] : []), 'C49', ...projectionCells(52)], kind: 'partialErrorSum' }
    }),
  ]
}

export const sheet = defineSheet({ id: '09_SRS_1Z_S', definition, compute, sample: { inputs: sample }, deviations, webHints, zeroAssumed, translations: { en } })
