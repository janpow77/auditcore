/**
 * Begründete Abweichungen des Blatts 04 bei leeren Eingaben. Wie in Blatt 03
 * zeigt die Webfassung „Angabe fehlt“, wo die Vorlage mit 0 weiterrechnet;
 * hier kommen die Schichtzeilen dazu. Belegt sind die sieben Schichtspalten
 * der Vorlage (D–J).
 */
import { TEMPLATE_STRATA, stratumCell } from '../../model/strata'
import type { Deviation } from '../../model/types'

function entries(cells: readonly string[], whenEmpty: readonly string[], template: string, reason: string): Deviation[] {
  return cells.map((cell) => ({ cell, whenEmpty, template, reason }))
}

/** Zellen einer Schichtzeile in den Spalten der Vorlage. */
const row = (number: number): string[] => TEMPLATE_STRATA.map((column) => stratumCell(column, number))

const SIGMA = row(24)
const SIZE_INPUTS = ['C20', ...SIGMA]
const SIZE = 'Ohne voraussichtliche Fehlerquote und Standardabweichung jeder belegten Schicht ist der Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen.'
const SIZE_TEMPLATE = 'Wert auf Grundlage des mit AE = 0 bzw. σ_rh = 0 berechneten Umfangs (mindestens 30)'

export const deviations: readonly Deviation[] = [
  ...entries(['C11'], ['02_Grundgesamtheit!C51'], 'Summe der Schichten abzüglich 0 € (leeres Blatt 02)', 'Ohne angepasste Grundgesamtheit in Blatt 02 gibt es nichts abzugleichen.'),
  ...entries(['C19'], ['C17'], '0,00 € (leere Zelle zählt als 0)', 'Der zulässige Fehler setzt die Wesentlichkeitsschwelle voraus.'),
  ...entries(['C21'], ['C20'], '0,00 € (leere Zelle zählt als 0)', 'Der voraussichtliche Fehler setzt die voraussichtliche Fehlerquote voraus.'),
  ...TEMPLATE_STRATA.flatMap((column) =>
    entries([stratumCell(column, 25)], [stratumCell(column, 24)], '0 (σ_rh einer belegten Schicht zählt als 0)', 'Fehlt die Standardabweichung einer belegten Schicht, ist die gewichtete Standardabweichung nicht bestimmt.'),
  ),
  ...entries(['C25', 'C26'], SIGMA, 'Wert ohne den Beitrag der Schicht mit fehlender Standardabweichung', 'Fehlt die Standardabweichung einer belegten Schicht, ist die gewichtete Standardabweichung nicht bestimmt.'),
  ...row(41).map((cell): Deviation => ({
    cell,
    whenEmpty: ['C33'],
    template: '„✔ ≥ 3“ (Excel wertet die leere Textzelle im Vergleich größer als jede Zahl)',
    reason: 'Ohne Stichprobenumfang gibt es keine Zufallsschicht zu prüfen.',
    check: 'none',
  })),
  ...entries(
    ['C27', 'C33', 'C35', 'C40', 'C50', 'C51', 'C52', 'C53', 'C54', 'C57', 'C58', 'C59', 'C60', 'C61', 'C62', 'C63', 'N5', 'N7', 'N10', 'N11', ...row(35), ...row(36), ...row(40), ...row(42), ...row(50), ...row(51), ...row(52)],
    SIZE_INPUTS,
    SIZE_TEMPLATE,
    SIZE,
  ),
]
