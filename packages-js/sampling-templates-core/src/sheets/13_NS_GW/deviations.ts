/**
 * Begründete Abweichungen des Blatts 13 vom Verhalten der Vorlage bei leeren
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
const SAMPLE = 'Ohne Umfang der Zufallsstichprobe ist die Gesamtstichprobe nicht bestimmt.'

export const deviations: readonly Deviation[] = [
  ...entries(['C7', 'N4'], ['C7'], '0 (Verknüpfung auf das leere Blatt 02)', BOOK_VALUE),
  ...entries(['C8'], ['C8'], '0 (Verknüpfung auf das leere Blatt 02)', UNITS),
  ...entries(['C9'], ['C8'], '„✔ N < 300: zulässig …“ (0 Einheiten liegen unter 300)', UNITS),
  ...entries(['C12'], ['C7'], '0 € abzüglich des Buchwerts der umfassenden Schicht', BOOK_VALUE),
  ...entries(['C14', 'N10'], ['C13'], 'nur die Einheiten der umfassenden Schicht bzw. 0 (leere Zelle zählt als 0)', SAMPLE),
  ...entries(['C15'], ['C8'], '0 (10 % von 0 Einheiten)', UNITS),
  ...entries(['C16'], ['C8', 'C13'], 'Prüfhinweis auf der Grundlage von 0 Einheiten der Grundgesamtheit bzw. der Zufallsstichprobe', 'Die Prüfung der Mindesterfassung setzt die Anzahl der Stichprobeneinheiten und den Umfang der Zufallsstichprobe voraus.'),
  ...entries(['C21', 'C22', 'N5'], ['C7'], 'Hochrechnung mit dem negativen Buchwert der Zufallsschicht (0 € abzüglich umfassende Schicht) bzw. 0 €', BOOK_VALUE),
  ...entries(['C28'], ['C27'], 'Würdigung gegen eine Schwelle von 0 %', 'Die Würdigung setzt die Wesentlichkeitsschwelle voraus.'),
  { cell: 'C21', whenEmpty: ['C18'], ...PROJECTION_WITHOUT_ERRORS },
]
