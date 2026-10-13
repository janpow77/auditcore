/**
 * Begründete Abweichungen des Blatts 03 vom Verhalten der Vorlage bei leeren
 * Eingaben. In allen Fällen zeigt die Webfassung „Angabe fehlt“ (`null`), nie
 * einen anderen Wert als die Vorlage. Jede Zeile ist durch mindestens einen
 * Golden-Fall belegt (test/deviations.spec.ts); Übersicht: docs/abweichungen.md.
 */
import type { CellAddress, Deviation } from '../../model/types'

function entries(cells: readonly CellAddress[], whenEmpty: readonly CellAddress[], template: string, reason: string): Deviation[] {
  return cells.map((cell) => ({ cell, whenEmpty, template, reason }))
}

const BOOK_VALUE = 'Ohne Buchwert der Grundgesamtheit gibt es keine Bezugsgröße; ein Ergebnis von 0 € wäre irreführend.'
const SIZE = 'Ohne voraussichtliche Fehlerquote und Standardabweichung ist der Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen.'

export const deviations: readonly Deviation[] = [
  ...entries(['C7', 'N4'], ['C7'], '0 (Verknüpfung auf das leere Blatt 02)', BOOK_VALUE),
  ...entries(['C8'], ['C8'], '0 (Verknüpfung auf das leere Blatt 02)', 'Ohne Angabe ist der Umfang der Grundgesamtheit unbekannt, nicht null.'),
  ...entries(['C16'], ['C7', 'C14'], '0,00 € (leere Zelle zählt als 0)', 'Der zulässige Fehler setzt Buchwert und Wesentlichkeitsschwelle voraus.'),
  ...entries(['C18'], ['C7', 'C17'], '0,00 € (leere Zelle zählt als 0)', 'Der voraussichtliche Fehler setzt Buchwert und voraussichtliche Fehlerquote voraus.'),
  ...entries(['C31'], ['C7'], '0 € abzüglich des Buchwerts der hochwertigen Einheiten', BOOK_VALUE),
  ...entries(['C21'], ['C17', 'C20'], 'Umfang mit AE = 0 bzw. σ_r = 0 (z. B. 0 oder 39)', SIZE),
  ...entries(['C27', 'N10'], ['C17', 'C20'], 'Mindestumfang 30 bzw. der mit AE = 0 berechnete Umfang', SIZE),
  ...entries(
    ['C28', 'C34', 'C41', 'C42', 'C43', 'C46', 'C47', 'N5', 'N7'],
    ['C7', 'C17', 'C20'],
    'Wert auf Grundlage des mit 0 gerechneten Buchwerts bzw. Umfangs (bei leerem Buchwert auch negative Beträge)',
    SIZE,
  ),
  ...entries(['C32', 'C33', 'C48', 'C49', 'C50', 'C51', 'C52', 'N11'], ['C17', 'C20'], 'Wert auf Grundlage des mit AE = 0 bzw. σ_r = 0 berechneten Umfangs', SIZE),
]
