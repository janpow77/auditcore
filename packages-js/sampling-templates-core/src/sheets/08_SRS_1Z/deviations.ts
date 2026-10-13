/**
 * Begründete Abweichungen des Blatts 08 vom Verhalten der Vorlage bei leeren
 * Eingaben. Fehlt eine Pflichteingabe, zeigt die Webfassung „Angabe fehlt“
 * (`null`), nie einen anderen Wert als die Vorlage. Dazu ein Wert ohne Grundlage
 * (`kind: 'withoutBasis'`): die Hochrechnung 0 der Zufallsschicht ohne
 * Fehlersumme. Jede Zeile ist durch mindestens einen Golden-Fall belegt
 * (test/deviations.spec.ts).
 *
 * Werte ohne Grundlage lässt die Webfassung offen, solange eine Pflichteingabe
 * fehlt; bei vollständigen Pflichteingaben zeigt sie sie wie die Vorlage und
 * weist sie mit einem Hinweis in Warnfarbe aus (`evaluateSheet`, Hinweis
 * `without-basis`); die Würdigung ist dann nicht uneingeschränkt grün.
 */
import type { CellAddress, Deviation } from '../../model/types'

function entries(cells: readonly CellAddress[], whenEmpty: readonly CellAddress[], template: string, reason: string): Deviation[] {
  return cells.map((cell) => ({ cell, whenEmpty, template, reason }))
}

const BOOK_VALUE = 'Ohne Buchwert der Grundgesamtheit gibt es keine Bezugsgröße; ein Ergebnis auf Grundlage von 0 € wäre irreführend.'
const UNITS = 'Ohne Angabe ist die Anzahl der Einheiten der Grundgesamtheit unbekannt, nicht null.'
const SIZE = 'Ohne Anzahl der Einheiten, voraussichtliche Fehlerquote und Standardabweichung ist der Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen.'
/** Eingaben, ohne die der rechnerische Umfang offen ist. */
const SIZE_INPUTS = ['C8', 'C22', 'C25']

export const deviations: readonly Deviation[] = [
  ...entries(['C7', 'N4'], ['C7'], '0 (Verknüpfung auf das leere Blatt 02)', BOOK_VALUE),
  ...entries(['C8'], ['C8'], '0 (Verknüpfung auf das leere Blatt 02)', UNITS),
  ...entries(['C12'], ['C7'], '0 € abzüglich des Buchwerts der umfassenden Schicht', BOOK_VALUE),
  ...entries(['C13'], ['C8'], '0 abzüglich der Einheiten der umfassenden Schicht', UNITS),
  ...entries(['C21'], ['C7', 'C19'], '0,00 € (leere Zelle zählt als 0)', 'Der zulässige Fehler setzt Buchwert und Wesentlichkeitsschwelle voraus.'),
  ...entries(['C23'], ['C7', 'C22'], '0,00 € (leere Zelle zählt als 0)', 'Der voraussichtliche Fehler setzt Buchwert und voraussichtliche Fehlerquote voraus.'),
  ...entries(['C26'], SIZE_INPUTS, 'Umfang mit N_s ≤ 0, AE = 0 bzw. σ_e = 0 (z. B. 0, 1 oder 16)', SIZE),
  ...entries(['C34', 'C35', 'N10'], SIZE_INPUTS, 'Mindestumfang bzw. der mit 0 berechnete Umfang, gegebenenfalls begrenzt', SIZE),
  ...entries(['C42', 'C43', 'N5'], ['C7'], 'Hochrechnung auf Grundlage von 0 € abzüglich des Buchwerts der umfassenden Schicht (negativer Betrag)', BOOK_VALUE),
  ...entries(['C44', 'N7', 'C49', 'C52', 'C53'], SIZE_INPUTS, 'Wert auf Grundlage des mit 0 gerechneten Umfangs bzw. einer Zufallsschicht mit N_s ≤ 0', SIZE),
  ...entries(['C47', 'C48'], ['C7', ...SIZE_INPUTS], 'Wert auf Grundlage des mit 0 gerechneten Buchwerts bzw. Umfangs', SIZE),
  {
    cell: 'C42',
    whenEmpty: ['C37'],
    template: '0,00 € (die Fehlersumme der Stichprobe fehlt; N(…) zählt sie als 0)',
    reason: 'Ohne Fehlersumme der Stichprobe gibt es nichts hochzurechnen; ein extrapolierter Fehler von 0 € sähe wie ein Prüfergebnis aus.',
    kind: 'withoutBasis',
  },
]
