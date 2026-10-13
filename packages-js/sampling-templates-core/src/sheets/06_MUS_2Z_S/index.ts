/** Blatt 06_MUS_2Z_S: MUS-Standardansatz, zwei Stichprobenzeiträume, geschichtet. */
import { eq, gt, isBlank, isNumber, le, sameNumber } from '../../excel/index'
import { defineSheet, type ZeroAssumption } from '../../model/sheet'
import { STRATA_COLUMNS, TEMPLATE_STRATA, countRow, stratumCell, usedStrata } from '../../model/strata'
import type { CellMap, WebHint } from '../../model/types'
import { approachOf, errorDependents, limitWithoutSize, partialErrorSums } from '../shared/mus'
import { compute } from './compute'
import { definition } from './definition'
import { deviations } from './deviations'
import { en } from './texts.en'

/** Erfundene Beispielwerte mit drei Schichten; sie stammen aus keiner Prüfung. */
const sample: CellMap = {
  C4: 'Beispiel – EFRE-Programm',
  C5: '2025/2026',
  C6: 'Zahlungsantrag des Begünstigten',
  D8: 12000000, E8: 9000000, F8: 5000000,
  D9: 11000000, E9: 8000000, F9: 4500000,
  D10: 110, E10: 80, F10: 40,
  C12: 'mittel', C13: 0.7, C14: 'zweiseitig', C17: 0.02, C20: 0.007,
  D24: 0.1, E24: 0.14, F24: 0.12,
  D25: 0.1, E25: 0.14, F25: 0.12,
  C28: 'Standard (Art. 5 Abs. 6 Buchst. a)', C30: 2, C31: 'Nein', C32: 'Nein',
  D41: 1, E41: 1, F41: 1,
  D42: 1400000, E42: 1000000, F42: 600000,
  D47: 4000, E47: 0, F47: 2500,
  D48: 0.15, E48: 0.12, F48: 0.06,
  D49: 0.04, E49: 0.05, F49: 0.045,
  D51: 11500000, E51: 8400000, F51: 4300000,
  D52: 115, E52: 84, F52: 38,
  D53: 0.1, E53: 0.13, F53: 0.12,
  D75: 1, E75: 1, F75: 0,
  D76: 1200000, E76: 900000, F76: 0,
  D81: 0, E81: 3000, F81: 0,
  D82: 0.1, E82: 0.11, F82: 0.05,
  D83: 0.035, E83: 0.05, F83: 0.04,
  C91: 0, C92: 0,
}

/** Hinweise je Schicht tragen die Schichtnummer im Text und in der Kennung (`…-<n>`). */
function stratumHints(id: string, tone: WebHint['tone'], text: string, applies: (column: string) => boolean): WebHint[] {
  return STRATA_COLUMNS.flatMap((column, index) => (applies(column) ? [{ id: `${id}-${index + 1}`, tone, text: `Schicht ${index + 1}: ${text}` }] : []))
}

/** Texte der Hinweise je Schicht (deutscher Wortlaut ohne die vorangestellte Schichtnummer). */
export const STRATUM_HINTS = {
  'size-exceeds-population-2': 'Stichprobenumfang für Zeitraum 2 übersteigt die Anzahl der Einheiten der Schicht',
  'no-planned-size': 'ohne Prognose für Zeitraum 2 gibt es keinen Planumfang; bei diesem Ansatz bleibt der Umfang der Schicht für Zeitraum 2 offen',
} as const

/** Schichten, deren Umfang für Zeitraum 2 die Anzahl ihrer Einheiten übersteigt, und Schichten ohne Planumfang bei einem Ansatz, der auf ihm aufbaut. */
function strataHints(results: CellMap): WebHint[] {
  const value = (column: string, row: number): CellMap[string] => results[stratumCell(column, row)] ?? null
  const planned = ['increase', 'none'].includes(approachOf(results.C28))
  return [
    ...stratumHints('size-exceeds-population-2', 'warning', STRATUM_HINTS['size-exceeds-population-2'], (column) => {
      const [size, units] = [value(column, 69), value(column, 52)]
      return isNumber(size) && isNumber(units) && gt(size, units)
    }),
    ...stratumHints('no-planned-size', 'warning', STRATUM_HINTS['no-planned-size'], (column) => planned && !isBlank(value(column, 51)) && isBlank(value(column, 9))),
  ]
}

/** Hinweise zu den Umfängen: Summe der aufgerundeten Schichtumfänge, Einheiten je Schicht, negativer Nenner. */
function sizeHints(results: CellMap): WebHint[] {
  const hints: WebHint[] = limitWithoutSize(results, 'C34', 'C29', 'C35')
  const { C35: size, C37: first, C38: second } = results
  if (isNumber(size) && isNumber(first) && isNumber(second) && gt(first + second, size)) {
    hints.push({ id: 'strata-sum-exceeds-size', tone: 'warning', text: 'Summe der aufgerundeten Schichtumfänge ist größer als der anzuwendende Stichprobenumfang' })
  }
  hints.push(...strataHints(results))
  if (approachOf(results.C28) === 'standard' && isNumber(results.C62) && le(results.C62, 0)) {
    hints.push({ id: 'negative-denominator', tone: 'warning', text: 'Nenner der Standardneuberechnung ist nicht positiv: Der Standardansatz liefert für Zeitraum 2 keinen Umfang je Schicht. Globale Neuberechnung wählen' })
  }
  return hints
}

/** Hinweise der Webfassung zu Blatt 06; sie verändern kein Rechenergebnis. */
function webHints(inputs: CellMap, results: CellMap): WebHint[] {
  const hints = sizeHints(results)
  if (isNumber(results.C8) && gt(results.C8, 0) && eq(countRow(results, 51), 0)) {
    hints.push({ id: 'second-period-empty', tone: 'warning', text: 'Für Zeitraum 2 ist kein Ist-Buchwert eingetragen: Neuberechnung, Hochrechnung und Gesamtfehlerquote bleiben offen (die Vorlage rechnet allein mit Zeitraum 1 weiter)' })
  }
  if (sameNumber(results.C13, 0.95)) hints.push({ id: 'confidence-outside-annex', tone: 'warning', text: 'Konfidenzniveau 95 % liegt außerhalb der Tabelle in Anhang I' })
  if (gt(usedStrata(inputs, [8, 9, 51]), TEMPLATE_STRATA.length)) {
    hints.push({ id: 'strata-beyond-template', tone: 'neutral', text: 'Mehr als sieben Schichten: Die Vorlage sieht sieben Spalten vor; die 8. bis 20. Schicht ist eine Erweiterung der Webfassung' })
  }
  return hints
}

/** Zellen, die von der Genauigkeit abhängen (ohne die Hilfszelle der Schicht). */
const PRECISION_CELLS = ['C88', 'C90', 'C93', 'C94', 'C95', 'C98', 'C99']

/** Zellen, die von der Summe der Fehlerquoten einer Schicht abhängen (ohne die Zelle der Schicht in Zeile 87). */
const ERROR_CELLS = ['C87', ...errorDependents(89)]
/** Zeile des Buchwerts, der die Schicht im Zeitraum belegt, mit der Zeile der Eingabe, die dann gebraucht wird. */
type Pair = readonly [used: number, input: number]
const SAMPLE_DEVIATIONS: readonly Pair[] = [[8, 49], [51, 83]]
const ERROR_RATE_SUMS: readonly Pair[] = [[8, 48], [51, 82]]

/** Leere Eingaben belegter Schichten: Zelle der Eingabe und Spalte der Schicht. */
function missingInputs(results: CellMap, pairs: readonly Pair[]): (readonly [input: string, column: string])[] {
  const blank = (column: string, row: number): boolean => isBlank(results[stratumCell(column, row)])
  return STRATA_COLUMNS.flatMap((column) => pairs.filter(([used, input]) => !blank(column, used) && blank(column, input)).map(([, input]) => [stratumCell(column, input), column] as const))
}

/**
 * Fehlt die Standardabweichung der Stichprobe einer belegten Schicht (Zeile 49
 * für Zeitraum 1, Zeile 83 für Zeitraum 2), setzt die Vorlage ihren Beitrag zur
 * Genauigkeit auf 0 (Zeile 88). Fehlt die Summe der Fehlerquoten einer belegten
 * Schicht (Zeilen 48, 82), während eine andere eingetragen ist, rechnet sie
 * deren Beitrag zur Hochrechnung mit 0 (Zeile 87).
 */
function zeroAssumed(results: CellMap): ZeroAssumption[] {
  const sums = partialErrorSums(results, 'C89', missingInputs(results, ERROR_RATE_SUMS).map(([input, column]) => [input, [stratumCell(column, 87), ...ERROR_CELLS]] as const))
  if (!isNumber(results.C90)) return sums
  return [...missingInputs(results, SAMPLE_DEVIATIONS).map(([input, column]) => ({ input, cells: [stratumCell(column, 88), ...PRECISION_CELLS] })), ...sums]
}

export const sheet = defineSheet({ id: '06_MUS_2Z_S', definition, compute, sample: { inputs: sample }, deviations, webHints, zeroAssumed, translations: { en } })
