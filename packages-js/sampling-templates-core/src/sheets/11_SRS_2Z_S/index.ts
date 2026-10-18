/** Blatt 11_SRS_2Z_S: einfaches Zufallsstichprobenverfahren (Verhältnisschätzung), zwei Stichprobenzeiträume, geschichtet. */
import { gt, isBlank, isNumber, sameNumber } from '../../excel/index'
import { defineSheet, type ZeroAssumption } from '../../model/sheet'
import { STRATA_COLUMNS, TEMPLATE_STRATA, stratumCell, usedStrata } from '../../model/strata'
import type { CellMap, SheetContext, WebHint } from '../../model/types'
import { NOT_APPLICABLE, precisionCells, projectionCells, recalculationOf } from '../shared/srs'
import { exclusionReference, withNotApplicableNote } from '../shared/delvo'
import { compute } from './compute'
import { definition } from './definition'
import { deviations } from './deviations'
import { en } from './texts.en'
import { UNITS, used } from './strata'
import { annexIIIApproximation, komPlanningHints } from '../shared/kom'

/** Erfundene Beispielwerte mit drei Schichten; sie stammen aus keiner Prüfung. */
const sample: CellMap = {
  C4: 'Beispiel – EFRE-Programm',
  C5: '2025/2026',
  C6: 'Zahlungsantrag des Begünstigten',
  C7: 5200000, C8: 4, C9: 2,
  D11: 120, E11: 90, F11: 40,
  D12: 11500000, E12: 8200000, F12: 3900000,
  D13: 110, E13: 80, F13: 45,
  D14: 10800000, E14: 7600000, F14: 4300000,
  C17: 'mittel', C18: 0.7, C19: 'zweiseitig', C22: 0.02, C25: 0.007,
  D29: 8000, E29: 11000, F29: 9500,
  D30: 8500, E30: 10500, F30: 9000,
  C33: 'Standard (Art. 5 Abs. 6 Buchst. a)',
  C35: 2, C36: 'Nein', C37: 'Nein',
  C47: 18400,
  D49: 1250000, E49: 910000, F49: 480000,
  D50: 6300, E50: 4100, F50: 2600,
  D51: 7600, E51: 10400, F51: 9900,
  D52: 2100, E52: 2800, F52: 2500,
  C53: 3100000, C54: 3, C55: 1,
  D57: 115, E57: 78, F57: 47,
  D58: 11200000, E58: 7300000, F58: 4500000,
  D59: 8200, E59: 10800, F59: 9100,
  C82: 7200,
  D84: 870000, E84: 560000, F84: 390000,
  D85: 4100, E85: 2700, F85: 2200,
  D86: 7900, E86: 10100, F86: 9300,
  D87: 2300, E87: 2600, F87: 2400,
  C94: 0, C95: 0,
}

/** Hinweistext zum nicht positiven Nenner; die Werte stehen bei vollständigen Pflichteingaben wie in der Vorlage (Hinweis `without-basis`). */
const NEGATIVE_DENOMINATOR =
  'Nenner der Standardneuberechnung ist nicht positiv – für Zeitraum 2 ergibt sich kein Umfang. Gesamtstichprobe, Genauigkeit und Würdigung enthalten dann – wie in der Vorlage – keinen Beitrag dieser Schicht und sind nicht belastbar; Eingaben der Neuberechnung prüfen oder einen anderen Ansatz wählen'

/**
 * Nenner der Standardneuberechnung nicht positiv: je in Zeitraum 2 belegter
 * Schicht ein Hinweis mit eigener Kennung (`negative-denominator-<Schicht>`).
 */
function negativeDenominator(results: CellMap): WebHint[] {
  if (recalculationOf(results.C33) !== 'standard' || results.C69 !== NOT_APPLICABLE) return []
  return STRATA_COLUMNS.flatMap((column, index): WebHint[] => {
    if (!used(results, column, UNITS.period2)) return []
    const stratum = index + 1
    return [{ id: `negative-denominator-${stratum}`, tone: 'warning', text: `Schicht ${stratum}: ${NEGATIVE_DENOMINATOR}` }]
  })
}

/** Hinweise der Webfassung zu Blatt 11; sie verändern kein Rechenergebnis. */
function webHints(inputs: CellMap, results: CellMap, context?: SheetContext): WebHint[] {
  const hints: WebHint[] = []
  const { C42: size, C44: first, C45: second } = results
  if (isNumber(size) && isNumber(first) && isNumber(second) && gt(first + second, size)) {
    hints.push({ id: 'strata-sum-exceeds-size', tone: 'warning', text: 'Summe der aufgerundeten Schichtumfänge ist größer als der anzuwendende Stichprobenumfang' })
  }
  hints.push(...negativeDenominator(results))
  if (sameNumber(results.C18, 0.95)) hints.push({ id: 'confidence-outside-annex', tone: 'warning', text: 'Konfidenzniveau 95 % liegt außerhalb der Tabelle in Anhang I' })
  if (gt(usedStrata(inputs, [UNITS.period1, UNITS.forecast2, UNITS.period2]), TEMPLATE_STRATA.length)) {
    hints.push({ id: 'strata-beyond-template', tone: 'neutral', text: 'Mehr als sieben Schichten: Die Vorlage sieht sieben Spalten vor; die 8. bis 20. Schicht ist eine Erweiterung der Webfassung' })
  }
  return withNotApplicableNote([...hints, ...komPlanningHints(definition, results), ...exclusionReference(context), ...annexIIIApproximation(context, true)])
}

/** Je Zeitraum: Zeile der Einheiten, der Standardabweichung der Variablen q (s_qh) und der Fehlersumme (Σ E_i). */
const PERIODS = [
  { units: UNITS.period1, ratioDeviation: 52, errorSum: 50 },
  { units: UNITS.period2, ratioDeviation: 87, errorSum: 85 },
] as const

/** Eingaben einer Zeile, die für eine im Zeitraum belegte Schicht fehlen. */
function lacking(results: CellMap, column: string, row: 'ratioDeviation' | 'errorSum'): string[] {
  return PERIODS.filter((period) => used(results, column, period.units) && isBlank(results[stratumCell(column, period[row])])).map((period) => stratumCell(column, period[row]))
}

/**
 * Mit 0 gerechnete Eingaben belegter Schichten: Fehlt die Standardabweichung der
 * Variablen q (Zeile 52 für Zeitraum 1, Zeile 87 für Zeitraum 2), setzt die
 * Vorlage ihren Beitrag zur Genauigkeit auf 0 (Zeile 90). Fehlt die Fehlersumme
 * (Zeile 50 bzw. 85), während eine andere Schicht oder der andere Zeitraum eine
 * trägt, zählt sie in der Hochrechnung 0 (`N(…)` in Zeile 89).
 */
function zeroAssumed(results: CellMap): ZeroAssumption[] {
  const precision = isNumber(results.C93)
  const projection = isNumber(results.C92)
  return STRATA_COLUMNS.flatMap((column): ZeroAssumption[] => {
    const projected = stratumCell(column, 89)
    return [
      ...(precision ? lacking(results, column, 'ratioDeviation') : []).map((input): ZeroAssumption => ({ input, cells: [stratumCell(column, 90), 'C90', ...precisionCells(92)] })),
      ...(projection ? lacking(results, column, 'errorSum') : []).map(
        (input): ZeroAssumption => ({ input, cells: [...(isNumber(results[projected]) ? [projected] : []), 'C89', ...projectionCells(92)], kind: 'partialErrorSum' }),
      ),
    ]
  })
}

export const sheet = defineSheet({ id: '11_SRS_2Z_S', definition, compute, sample: { inputs: sample }, deviations, webHints, zeroAssumed, translations: { en } })
