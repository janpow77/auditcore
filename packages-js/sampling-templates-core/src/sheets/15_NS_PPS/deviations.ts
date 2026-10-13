/**
 * Begründete Abweichungen des Blatts 15 vom Verhalten der Vorlage bei leeren
 * Eingaben. Fehlt eine Pflichteingabe, zeigt die Webfassung „Angabe fehlt“
 * (`null`), nie einen anderen Wert als die Vorlage. Der Wert ohne Grundlage
 * (`withoutBasis`, Hochrechnung ohne Fehlersumme) bleibt nur offen, solange eine
 * Pflichteingabe fehlt; bei vollständigen Eingaben zeigt ihn die Webfassung wie
 * die Vorlage mit Hinweis in Warnfarbe. Jede Zeile ist durch mindestens einen
 * Golden-Fall belegt (test/deviations.spec.ts); Übersicht: docs/abweichungen.md.
 */
import { PROJECTION_WITHOUT_ERRORS } from '../../model/policy'
import type { CellAddress, Deviation } from '../../model/types'

function entries(cells: readonly CellAddress[], whenEmpty: readonly CellAddress[], template: string, reason: string): Deviation[] {
  return cells.map((cell) => ({ cell, whenEmpty, template, reason }))
}

const BOOK_VALUE = 'Ohne Buchwert der Grundgesamtheit gibt es keine Bezugsgröße; ein Ergebnis auf der Grundlage von 0 € wäre irreführend.'
const UNITS = 'Ohne Angabe ist die Anzahl der Stichprobeneinheiten unbekannt, nicht null.'
const SIZE = 'Ohne Stichprobenumfang sind Zufallsschicht und Auswahlintervall nicht bestimmt; alle Folgegrößen bleiben offen.'

export const deviations: readonly Deviation[] = [
  ...entries(['C7', 'N4'], ['C7'], '0 (Verknüpfung auf das leere Blatt 02)', BOOK_VALUE),
  ...entries(['C8'], ['C8'], '0 (Verknüpfung auf das leere Blatt 02)', UNITS),
  ...entries(['C9'], ['C8'], '„✔ N < 300: zulässig …“ (0 Einheiten liegen unter 300)', UNITS),
  ...entries(['C11'], ['C8'], '0 (10 % von 0 Einheiten)', UNITS),
  ...entries(['C12'], ['C8'], '„✔ Mindesterfassung erreicht“ (gegen 0 Einheiten)', UNITS),
  ...entries(['N10'], ['C10'], '0 (leere Zelle zählt als 0)', SIZE),
  ...entries(['C13'], ['C7'], '0,00 € (0 € geteilt durch den Stichprobenumfang)', BOOK_VALUE),
  ...entries(['C16'], ['C7'], '0 € abzüglich des Buchwerts der hochwertigen Einheiten', BOOK_VALUE),
  ...entries(['C17'], ['C10'], '0 abzüglich der Anzahl hochwertiger Einheiten', SIZE),
  ...entries(['C18'], ['C10'], '„✖ < 3 Einheiten (Art. 5 Abs. 5)“ (gegen 0 bzw. eine negative Anzahl)', SIZE),
  ...entries(['C19', 'C25', 'C26', 'N5'], ['C7', 'C10'], 'Wert auf Grundlage des mit 0 gerechneten Buchwerts bzw. Stichprobenumfangs (auch negative Beträge)', 'Auswahlintervall und Hochrechnung setzen Buchwert der Grundgesamtheit und Stichprobenumfang voraus.'),
  ...entries(['C29', 'C30', 'N11'], ['C10'], 'Fehlerquote auf Grundlage des mit n = 0 gerechneten (negativen) Auswahlintervalls', SIZE),
  ...entries(['C32'], ['C10', 'C31'], 'Würdigung gegen eine Schwelle von 0 % bzw. auf Grundlage des mit n = 0 gerechneten Auswahlintervalls', 'Die Würdigung setzt die Wesentlichkeitsschwelle und den Stichprobenumfang voraus.'),
  { cell: 'C25', whenEmpty: ['C23'], ...PROJECTION_WITHOUT_ERRORS },
]
