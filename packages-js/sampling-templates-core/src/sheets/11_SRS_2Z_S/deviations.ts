/**
 * Begründete Abweichungen des Blatts 11 bei leeren Eingaben. Wie in den Blättern
 * 04, 08 und 09 zeigt die Webfassung „Angabe fehlt“ (`null`), wo die Vorlage ohne
 * eine Pflichteingabe mit 0 weiterrechnet, nie einen anderen Wert. `whenEmpty` nennt je Zelle die
 * Eingaben, deren Fehlen sie leert (auch mittelbar über Zwischenzellen); alle
 * bestehen die Gegenprobe mit 0. Die Standardabweichung der Stichprobe für die
 * Neuberechnung (Zeile 51) steht nicht in den Listen: Leer verzweigt die Vorlage
 * auf σ (Zeile 29). Die Werte ohne Grundlage stehen in `deviations-basis.ts`
 * (offen nur, solange eine Pflichteingabe fehlt; sonst wie die Vorlage mit Hinweis).
 * Geführt über alle Schichtspalten des Blatts (D–J der Vorlage, AA–AM der Webfassung).
 */
import { STRATA_COLUMNS, stratumCell } from '../../model/strata'
import type { Deviation } from '../../model/types'
import { withoutBasis } from './deviations-basis'

function entries(cells: readonly string[], whenEmpty: readonly string[], template: string, reason: string): Deviation[] {
  return cells.map((cell) => ({ cell, whenEmpty, template, reason }))
}

/** Zellen einer Schichtzeile über alle Schichtspalten. */
const row = (number: number): string[] => STRATA_COLUMNS.map((column) => stratumCell(column, number))

/** Je Schichtspalte eine Zeile: Zelle der Schicht, leer ist eine ihrer Eingaben. */
function perStratum(cellRow: number, inputRows: readonly number[], template: string, reason: string): Deviation[] {
  return STRATA_COLUMNS.flatMap((column) => entries([stratumCell(column, cellRow)], inputRows.map((input) => stratumCell(column, input)), template, reason))
}

const SIGMA1 = row(29)
const SIGMA2_FORECAST = row(30)
const SIGMA2 = row(59)
const BOOK_VALUES = [...row(12), ...row(58)]
/** Gesamtumfang „Erster Zeitraum“ (C34) und seine Aufteilung. */
const FIRST = ['C25', ...SIGMA1, ...SIGMA2_FORECAST]
/** Globaler Ansatz (C72): ohne die Prognose σ_eh2 aus Abschnitt I. */
const GLOBAL = ['C22', 'C25', ...SIGMA1, ...SIGMA2]
/** Alle Eingaben, von denen ein endgültiger Umfang abhängen kann. */
const ALL = ['C22', ...FIRST, ...SIGMA2]

const ZERO = '0,00 € (leere Zelle zählt als 0)'
const SIGMA_TEMPLATE = 'Wert mit σ = 0 für die Schicht mit fehlender Standardabweichung'
const SIGMA_REASON = 'Fehlt die Standardabweichung einer für den Zeitraum belegten Schicht, ist die Streuung nicht bestimmt; 0 wäre eine Annahme zugunsten eines kleineren Umfangs.'
const FIRST_TEMPLATE = 'Wert auf Grundlage des mit AE = 0 bzw. σ_eh = 0 berechneten Gesamtumfangs (mindestens der Mindestumfang)'
const FIRST_REASON = 'Ohne voraussichtliche Fehlerquote und Standardabweichung jeder belegten Schicht ist der Gesamtumfang nicht bestimmt; seine Aufteilung und alle Folgegrößen bleiben offen.'
const SECOND_TEMPLATE = 'Wert auf Grundlage von TE = 0, AE = 0 bzw. σ_eh = 0 (z. B. Umfang 3 je Schicht oder der Mindestumfang)'
const SECOND_REASON = 'Ohne Signifikanzschwelle, voraussichtliche Fehlerquote und Standardabweichung jeder belegten Schicht ist die Neuberechnung für Zeitraum 2 nicht bestimmt; die endgültigen Umfänge und die Genauigkeit bleiben offen.'
const BOOK_VALUE_TEMPLATE = 'Wert ohne den Beitrag der Schicht mit fehlendem Buchwert'
const BOOK_VALUE_REASON = 'Fehlt der Buchwert einer belegten Schicht, lässt sich ihr Fehler nicht hochrechnen; die Vorlage rechnet für diese Schicht mit 0 €.'

export const deviations: readonly Deviation[] = [
  ...entries(['C24', 'C62'], ['C22'], ZERO, 'Der zulässige Fehler setzt die Signifikanzschwelle voraus.'),
  ...entries(['C26', 'C63'], ['C25'], ZERO, 'Der voraussichtliche Fehler setzt die voraussichtliche Fehlerquote voraus.'),
  ...perStratum(31, [29, 30], '0 bzw. nur der Beitrag des anderen Zeitraums (σ_eh einer belegten Schicht zählt als 0)', SIGMA_REASON),
  ...entries(['C31', 'C32'], [...SIGMA1, ...SIGMA2_FORECAST], SIGMA_TEMPLATE, SIGMA_REASON),
  ...entries(['C34', 'C42', 'C44', 'C45', 'C66', ...row(44), ...row(45), ...row(46), ...row(66)], FIRST, FIRST_TEMPLATE, FIRST_REASON),
  // Eine Zeile für alle Schichten: Die Zellen nicht belegter Schichten sind leer; je Schicht eine eigene Liste hieße je Schicht eine Gegenrechnung.
  ...entries(row(65), SIGMA1, '0 (weder s_eh noch σ_eh1 angegeben; die leere Zelle zählt als 0)', SIGMA_REASON),
  ...perStratum(67, [59], '0 (σ_eh2 einer belegten Schicht zählt als 0)', SIGMA_REASON),
  ...entries(['C67'], SIGMA2, SIGMA_TEMPLATE, SIGMA_REASON),
  ...entries(['C68'], ['C22', ...FIRST], 'Nenner auf Grundlage von TE = 0, AE = 0 bzw. des mit 0 berechneten Umfangs für Zeitraum 1', SECOND_REASON),
  ...entries(['C69'], ALL, SECOND_TEMPLATE, SECOND_REASON),
  ...perStratum(70, [29, 59], '0 bzw. nur der Beitrag des anderen Zeitraums (Standardabweichung einer belegten Schicht zählt als 0)', SIGMA_REASON),
  ...entries(['C70'], [...SIGMA1, ...SIGMA2], SIGMA_TEMPLATE, SIGMA_REASON),
  ...entries(['C72', 'C74'], GLOBAL, SECOND_TEMPLATE, SECOND_REASON),
  ...entries(['C76', 'C77', 'C78', 'C80', 'C81', 'N10', ...row(76), ...row(77), ...row(78), ...row(79)], ALL, SECOND_TEMPLATE, SECOND_REASON),
  ...perStratum(89, [12, 58], '0 € bzw. nur der Beitrag des anderen Zeitraums (Buchwert einer belegten Schicht zählt als 0)', BOOK_VALUE_REASON),
  ...entries(['C89', 'C92', 'N5', 'C99', 'C100', 'N11'], BOOK_VALUES, BOOK_VALUE_TEMPLATE, BOOK_VALUE_REASON),
  ...entries(['C90', 'C93', 'N7', 'C98', ...row(90)], ALL, 'Wert auf Grundlage der mit 0 berechneten Umfänge je Schicht', SECOND_REASON),
  ...entries(['C96', 'C97', 'C101', 'C102'], [...ALL, ...BOOK_VALUES], 'Wert auf Grundlage der mit 0 berechneten Umfänge bzw. ohne den Beitrag der Schicht mit fehlendem Buchwert', SECOND_REASON),
  ...withoutBasis,
]
