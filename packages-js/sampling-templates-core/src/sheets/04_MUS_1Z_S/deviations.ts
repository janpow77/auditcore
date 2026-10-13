/**
 * Begründete Abweichungen des Blatts 04 bei leeren Eingaben. Wie in Blatt 03
 * zeigt die Webfassung „Angabe fehlt“, wo die Vorlage mit 0 weiterrechnet;
 * hier kommen die Schichtzeilen dazu. Sie gelten für alle Schichtspalten; durch
 * Golden-Fälle belegt sind die sieben der Vorlage (D–J).
 */
import { STRATA_COLUMNS, stratumCell } from '../../model/strata'
import type { Deviation } from '../../model/types'

function entries(cells: readonly string[], whenEmpty: readonly string[], template: string, reason: string): Deviation[] {
  return cells.map((cell) => ({ cell, whenEmpty, template, reason }))
}

/** Zellen einer Schichtzeile über alle Schichtspalten (Vorlage D–J, Webfassung zusätzlich AA–AM). */
const row = (number: number): string[] => STRATA_COLUMNS.map((column) => stratumCell(column, number))

const SIGMA = row(24)
const SIZE_INPUTS = ['C20', ...SIGMA]
const SIZE = 'Ohne voraussichtliche Fehlerquote und Standardabweichung jeder belegten Schicht ist der Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen.'
const SIZE_TEMPLATE = 'Wert auf Grundlage des mit AE = 0 bzw. σ_rh = 0 berechneten Umfangs (mindestens 30)'

/** Summe einer Schichtzeile, in der keine Schicht einen Wert trägt: Die Vorlage zeigt 0. */
function emptyTotal(cell: string, cells: number): Deviation {
  return {
    cell,
    whenEmpty: row(cells),
    template: '0 (Summe über Schichten ohne Wert)',
    reason: 'Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus.',
    kind: 'withoutBasis',
  }
}

/** Summenzellen mit der Schichtzeile, deren Werte sie summieren (Hilfszeilen 25 und 52: die Buchwerte der Schichten). */
const TOTALS: readonly (readonly [cell: string, row: number])[] = [
  ['C9', 9], ['C10', 10], ['C25', 9], ['C35', 35], ['C37', 37], ['C38', 38], ['C39', 39], ['C40', 40], ['C43', 43],
  ['C45', 45], ['C46', 46], ['C49', 49], ['C50', 50], ['C51', 51], ['C52', 9], ['N4', 9], ['N10', 35],
]

/** Zellen, die auf einer Summe ohne Summanden aufbauen: Die Vorlage rechnet mit deren 0 weiter. */
function withoutTotal(cells: readonly string[], total: string, template: string): Deviation[] {
  return cells.map((cell) => ({
    cell,
    whenEmpty: [total],
    template,
    reason: 'Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt.',
    kind: 'withoutBasis',
  }))
}

export const deviations: readonly Deviation[] = [
  ...TOTALS.map(([cell, cells]) => emptyTotal(cell, cells)),
  ...withoutTotal(['C11', 'C19', 'C21'], 'C9', '0 € (Summe der Buchwerte ohne belegte Schicht)'),
  ...withoutTotal(['N6'], 'C49', '0 € (Summe ohne belegte Schicht)'),
  ...withoutTotal(['C53', 'C57', 'C58', 'C60', 'C61', 'C62', 'C63', 'N5', 'N11'], 'C51', 'Hochrechnung und Würdigung auf Grundlage eines extrapolierten Fehlers von 0 €, obwohl keine Schicht einen Stichprobenumfang hat (z. B. bei „TE ≤ AE“)'),
  ...entries(['C11'], ['02_Grundgesamtheit!C51'], 'Summe der Schichten abzüglich 0 € (leeres Blatt 02)', 'Ohne angepasste Grundgesamtheit in Blatt 02 gibt es nichts abzugleichen.'),
  ...entries(['C19'], ['C17'], '0,00 € (leere Zelle zählt als 0)', 'Der zulässige Fehler setzt die Wesentlichkeitsschwelle voraus.'),
  ...entries(['C21'], ['C20'], '0,00 € (leere Zelle zählt als 0)', 'Der voraussichtliche Fehler setzt die voraussichtliche Fehlerquote voraus.'),
  ...STRATA_COLUMNS.flatMap((column) =>
    entries([stratumCell(column, 25)], [stratumCell(column, 24)], '0 (σ_rh einer belegten Schicht zählt als 0)', 'Fehlt die Standardabweichung einer belegten Schicht, ist die gewichtete Standardabweichung nicht bestimmt.'),
  ),
  ...entries(['C25', 'C26'], SIGMA, 'Wert ohne den Beitrag der Schicht mit fehlender Standardabweichung', 'Fehlt die Standardabweichung einer belegten Schicht, ist die gewichtete Standardabweichung nicht bestimmt.'),
  ...STRATA_COLUMNS.map((column): Deviation => ({
    cell: stratumCell(column, 41),
    whenEmpty: [stratumCell(column, 40)],
    template: '„✔ ≥ 3“ (Excel wertet die leere Textzelle im Vergleich größer als jede Zahl)',
    reason: 'Ohne Einheiten der Zufallsschicht gibt es nichts zu prüfen; ein bestandener Prüfhinweis wäre irreführend.',
    kind: 'withoutBasis',
  })),
  ...entries(
    ['C27', 'C33', 'C35', 'C40', 'C50', 'C51', 'C52', 'C53', 'C54', 'C57', 'C58', 'C59', 'C60', 'C61', 'C62', 'C63', 'N5', 'N7', 'N10', 'N11', ...row(35), ...row(36), ...row(40), ...row(41), ...row(42), ...row(50), ...row(51), ...row(52)],
    SIZE_INPUTS,
    SIZE_TEMPLATE,
    SIZE,
  ),
]
