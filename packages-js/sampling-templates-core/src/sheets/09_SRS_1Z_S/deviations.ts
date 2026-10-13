/**
 * Begründete Abweichungen des Blatts 09 bei leeren Eingaben. Wie in den
 * Blättern 04 und 08 zeigt die Webfassung „Angabe fehlt“, wo die Vorlage mit 0
 * weiterrechnet, und lässt Werte ohne Grundlage offen (`kind: 'withoutBasis'`):
 * Summen über Schichtzeilen ohne Summanden samt allem, was auf ihnen aufbaut,
 * den Prüfhinweis „✔ ≥ 3“ ohne Umfang je Schicht und die Hochrechnung 0, solange
 * keine Schicht eine Fehlersumme trägt. Geführt über alle Schichtspalten des
 * Blatts (D–J der Vorlage und AA–AM der Webfassung).
 */
import { STRATA_COLUMNS, stratumCell } from '../../model/strata'
import type { Deviation } from '../../model/types'

function entries(cells: readonly string[], whenEmpty: readonly string[], template: string, reason: string, kind?: Deviation['kind']): Deviation[] {
  return cells.map((cell) => ({ cell, whenEmpty, template, reason, ...(kind ? { kind } : {}) }))
}

/** Zellen einer Schichtzeile über alle Schichtspalten. */
const row = (number: number): string[] => STRATA_COLUMNS.map((column) => stratumCell(column, number))

/** Je Schichtspalte eine Zeile: Zelle der Schicht, leer ist die Zelle derselben Schicht in `inputRow`. */
function perStratum(cellRow: number, inputRow: number, template: string, reason: string, kind?: Deviation['kind']): Deviation[] {
  return STRATA_COLUMNS.flatMap((column) => entries([stratumCell(column, cellRow)], [stratumCell(column, inputRow)], template, reason, kind))
}

const SIGMA = row(28)
const BOOK_VALUES = row(13)
const SIZE_INPUTS = ['C24', ...SIGMA]
const SIGMA_REASON = 'Fehlt die Standardabweichung einer belegten Schicht, ist die gewichtete Standardabweichung nicht bestimmt.'
const SIZE = 'Ohne voraussichtliche Fehlerquote und Standardabweichung jeder belegten Schicht ist der Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen.'
const SIZE_TEMPLATE = 'Wert auf Grundlage des mit AE = 0 bzw. σ_eh = 0 berechneten Umfangs (mindestens der Mindestumfang)'
const BOOK_VALUE = 'Fehlt der Buchwert einer belegten Schicht, lässt sich ihr Fehler nicht hochrechnen; die Vorlage rechnet für diese Schicht mit 0 €.'
const BOOK_VALUE_TEMPLATE = 'Wert ohne den Beitrag der Schicht mit fehlendem Buchwert'
const EMPTY_TOTAL = 'Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus.'
const ON_TOTAL = 'Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt.'
const NO_ERROR_SUM = 'Solange keine Schicht eine Fehlersumme trägt, gibt es nichts hochzurechnen; ein extrapolierter Fehler von 0 € sähe wie ein Prüfergebnis aus.'

/** Summenzellen mit der Schichtzeile, deren Werte sie summieren (Hilfszeilen 29 und 50: die Anzahl der Einheiten). */
const TOTALS: readonly (readonly [cell: string, row: number])[] = [['C12', 12], ['C13', 13], ['C29', 12], ['C41', 41], ['C45', 45], ['C46', 46], ['C50', 12]]

/** Werte ohne Grundlage (`unfounded`, `totalRow`): Die Webfassung zeigt sie nach der geltenden Richtlinie nicht. */
const withoutBasis: readonly Deviation[] = [
  ...TOTALS.flatMap(([cell, cells]) => entries([cell], row(cells), '0 (Summe über Schichten ohne Wert)', EMPTY_TOTAL, 'withoutBasis')),
  ...entries(['C14', 'N4', 'C15', 'C23', 'C25'], ['C13'], 'Wert auf Grundlage einer Summe der Buchwerte von 0 € (nur die umfassende Schicht)', ON_TOTAL, 'withoutBasis'),
  ...entries(['C26', 'C31', 'C39', 'C53', 'N7', 'C58', ...row(41)], ['C13'], 'Stichprobenumfang und Genauigkeit auf Grundlage eines zulässigen Fehlers ohne die Buchwerte der Zufallsschichten', ON_TOTAL, 'withoutBasis'),
  ...entries(['N10'], ['C41'], 'Einheiten der umfassenden Schicht bzw. 0 (Summe der Schichtumfänge ohne Umfang je Schicht)', ON_TOTAL, 'withoutBasis'),
  ...perStratum(
    42,
    41,
    '„✔ ≥ 3“ (Excel wertet die leere Textzelle im Vergleich größer als jede Zahl)',
    'Ohne Stichprobenumfang der Schicht gibt es nichts zu prüfen; ein bestandener Prüfhinweis wäre irreführend.',
    'withoutBasis',
  ),
  ...entries(['C49', ...row(49)], ['C46'], '0,00 € (keine Schicht trägt eine Fehlersumme)', NO_ERROR_SUM, 'withoutBasis'),
]

export const deviations: readonly Deviation[] = [
  ...entries(['C15'], ['02_Grundgesamtheit!C51'], 'Buchwert der Grundgesamtheit abzüglich 0 € (leeres Blatt 02)', 'Ohne angepasste Grundgesamtheit in Blatt 02 gibt es nichts abzugleichen.'),
  ...entries(['C23'], ['C21'], '0,00 € (leere Zelle zählt als 0)', 'Der zulässige Fehler setzt die Wesentlichkeitsschwelle voraus.'),
  ...entries(['C25'], ['C24'], '0,00 € (leere Zelle zählt als 0)', 'Der voraussichtliche Fehler setzt die voraussichtliche Fehlerquote voraus.'),
  ...perStratum(29, 28, '0 (σ_eh einer belegten Schicht zählt als 0)', SIGMA_REASON),
  ...entries(['C29', 'C30'], SIGMA, 'Wert ohne den Beitrag der Schicht mit fehlender Standardabweichung', SIGMA_REASON),
  ...entries(['C31', 'C39', 'C41', 'N10', 'C53', 'N7', 'C58', ...row(41), ...row(42)], SIZE_INPUTS, SIZE_TEMPLATE, SIZE),
  ...perStratum(49, 13, '0 € (Buchwert einer belegten Schicht zählt als 0)', BOOK_VALUE),
  ...entries(['C49', 'C52', 'N5', 'C59', 'C60', 'N11'], BOOK_VALUES, BOOK_VALUE_TEMPLATE, BOOK_VALUE),
  ...entries(['C56', 'C57', 'C61', 'C62'], [...SIZE_INPUTS, ...BOOK_VALUES], 'Wert auf Grundlage des mit 0 berechneten Umfangs bzw. ohne den Beitrag der Schicht mit fehlendem Buchwert', SIZE),
  ...withoutBasis,
]
