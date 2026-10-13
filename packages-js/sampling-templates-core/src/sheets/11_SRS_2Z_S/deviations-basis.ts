/**
 * Werte ohne Grundlage in Blatt 11 (`kind: 'withoutBasis'`): Die Vorlage zeigt
 * sie, obwohl die summierte bzw. geprüfte Größe fehlt (`unfounded`, `totalRow`).
 * Die Webfassung lässt sie offen, solange eine Pflichteingabe fehlt; bei
 * vollständigen Pflichteingaben zeigt sie sie wie die Vorlage und weist sie mit
 * einem Hinweis in Warnfarbe aus (`evaluateSheet`, Hinweis `without-basis`); die
 * Würdigung ist dann nicht uneingeschränkt grün. Das sind die
 * Summen über Schichtzeilen ohne Summanden samt allem, was auf ihnen aufbaut,
 * die Prüfhinweise „✔ ≥ 3“ ohne Umfang je Schicht, die Untergrenze 3 je Schicht
 * ohne Gesamtumfang und die Hochrechnung 0, solange keine Schicht eine
 * Fehlersumme trägt. `whenEmpty` nennt die fehlende Größe.
 */
import { STRATA_COLUMNS, stratumCell } from '../../model/strata'
import type { Deviation } from '../../model/types'

function entries(cells: readonly string[], whenEmpty: readonly string[], template: string, reason: string): Deviation[] {
  return cells.map((cell) => ({ cell, whenEmpty, template, reason, kind: 'withoutBasis' }))
}

/** Zellen einer Schichtzeile über alle Schichtspalten. */
const row = (number: number): string[] => STRATA_COLUMNS.map((column) => stratumCell(column, number))

/** Je Schichtspalte eine Zeile: Zelle der Schicht, leer ist eine der Zellen derselben Schicht (und der genannten Summen). */
function perStratum(cellRow: number, emptyRows: readonly number[], totals: readonly string[], template: string, reason: string): Deviation[] {
  return STRATA_COLUMNS.flatMap((column) => entries([stratumCell(column, cellRow)], [...emptyRows.map((empty) => stratumCell(column, empty)), ...totals], template, reason))
}

const EMPTY_TOTAL = 'Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus.'
const ON_TOTAL = 'Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt.'
const ON_TOTAL_TEMPLATE = 'Wert auf Grundlage einer Summe von 0 über Schichten ohne Wert'
const NO_SIZE = 'Ohne Stichprobenumfang der Schicht gibt es nichts zu prüfen; ein bestandener Prüfhinweis wäre irreführend.'
const NO_SIZE_TEMPLATE = '„✔ ≥ 3“ (Excel wertet die leere Textzelle im Vergleich größer als jede Zahl)'
const NO_ERROR_SUM = 'Solange keine Schicht eine Fehlersumme trägt, gibt es nichts hochzurechnen; ein extrapolierter Fehler von 0 € sähe wie ein Prüfergebnis aus.'
const ONE_PERIOD =
  'Hochrechnung und Genauigkeit gelten für das Geschäftsjahr; ist für einen der beiden Zeiträume keine Schicht belegt oder trägt keine belegte Schicht einen Wert, entstünden sie allein aus dem anderen Zeitraum bzw. aus einer Summe von 0.'
const HALF_YEAR_TEMPLATE = 'Hochrechnung bzw. Genauigkeit allein aus einem Zeitraum oder aus einer Summe von 0 (z. B. Genauigkeit 0 € ohne Umfang je Schicht bei „TE ≤ AE“)'

/** Summen der Zeiträume, auf denen die Planung (Abschnitte H bis J) aufbaut. */
const PLANNING = ['C11', 'C12', 'C13', 'C14']
/** Dazu die Ist-Werte des Zeitraums 2 (Abschnitt L). */
const YEAR = [...PLANNING, 'C57', 'C58']

/**
 * Summenzellen mit den Schichtzeilen, deren Werte sie summieren. Hilfszeilen (31, 66, 67, 70) tragen für nicht
 * belegte Schichten 0; ihre Summe hat keinen Summanden, wenn keine Schicht belegt ist (Zeilen der Anzahl der
 * Einheiten) oder keine belegte Schicht einen Wert trägt (die Zeile selbst).
 */
const TOTALS: readonly (readonly [cell: string, rows: readonly number[]])[] = [
  ['C11', [11]], ['C12', [12]], ['C13', [13]], ['C14', [14]], ['C31', [31, 11, 13]], ['C44', [44]], ['C45', [45]], ['C49', [49]], ['C50', [50]], ['C57', [57]], ['C58', [58]],
  ['C66', [66, 11]], ['C67', [67, 57]], ['C70', [70, 11, 57]], ['C76', [76]], ['C77', [77]], ['C78', [78]], ['C84', [84]], ['C85', [85]],
]

export const withoutBasis: readonly Deviation[] = [
  ...TOTALS.flatMap(([cell, rows]) => entries([cell], rows.flatMap(row), '0 (Summe über Schichten ohne Wert)', EMPTY_TOTAL)),
  ...entries(['C15', 'C16', 'C24', 'C26', 'C27', 'C32', 'C34', 'C42', ...row(44), ...row(45), ...row(66)], PLANNING, ON_TOTAL_TEMPLATE, ON_TOTAL),
  ...entries(['C61', 'N4', 'C62', 'C63', 'C71', 'C72', 'C74', ...row(76)], YEAR, ON_TOTAL_TEMPLATE, ON_TOTAL),
  ...entries(['C68', 'C69'], [...YEAR, 'C66', 'C67'], 'Nenner bzw. Umfang des Standardansatzes auf Grundlage einer Summe von 0 (z. B. ohne Umfang je Schicht für Zeitraum 1 bei „TE ≤ AE“)', ON_TOTAL),
  ...perStratum(46, [44], [], NO_SIZE_TEMPLATE, NO_SIZE),
  ...perStratum(79, [77], [], NO_SIZE_TEMPLATE, NO_SIZE),
  ...perStratum(
    77,
    [45],
    ['C69', 'C74'],
    '3 (Untergrenze je Schicht, obwohl es keinen Gesamtumfang gibt, z. B. bei „TE ≤ AE“) bzw. Umfang auf Grundlage einer Summe von 0',
    'Ohne Gesamtumfang gibt es für Zeitraum 2 nichts aufzuteilen; die Untergrenze von 3 Einheiten je Schicht hätte als anzuwendender Umfang keine Grundlage.',
  ),
  ...perStratum(78, [44, 76], [], ON_TOTAL_TEMPLATE, ON_TOTAL),
  ...entries(['C80', 'C81', 'N10'], ['C77', 'C78'], 'Gesamtstichprobe bzw. ihr Prüfhinweis auf Grundlage einer Summe der Schichtumfänge von 0', ON_TOTAL),
  ...perStratum(89, [], ['C50', 'C85'], '0,00 € (keine Schicht trägt eine Fehlersumme)', NO_ERROR_SUM),
  ...perStratum(90, [77, 78], [], 'Beitrag zur Genauigkeit auf Grundlage eines Umfangs je Schicht, der auf einer Summe von 0 aufbaut', ON_TOTAL),
  ...entries(['C89'], ['C11', 'C57', ...row(89)], HALF_YEAR_TEMPLATE, ONE_PERIOD),
  ...entries(['C90'], ['C11', 'C57', ...row(90)], HALF_YEAR_TEMPLATE, ONE_PERIOD),
  ...entries(['C92', 'N5'], ['C89'], HALF_YEAR_TEMPLATE, ONE_PERIOD),
  ...entries(['C93', 'N7', 'C96', 'C97'], ['C89', 'C90'], HALF_YEAR_TEMPLATE, ONE_PERIOD),
  ...entries(['C98', 'C99', 'C100', 'N11', 'C101', 'C102'], [...YEAR, 'C89', 'C90'], 'Quote bzw. Würdigung auf Grundlage einer Summe von 0 über Schichten ohne Wert', ON_TOTAL),
]
