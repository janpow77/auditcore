/**
 * Begründete Abweichungen des Blatts 12 vom Verhalten der Vorlage bei leeren
 * Eingaben. Fehlt eine Pflichteingabe, zeigt die Webfassung „Angabe fehlt“
 * (`null`), nie einen anderen Wert als die Vorlage. `whenEmpty` nennt je Zelle die Eingaben,
 * deren Fehlen die Zelle leert – unmittelbar oder über Zwischenzellen; die
 * Listen folgen deshalb dem Aufbau der Formeln. Wo die Vorlage bei einer
 * fehlenden Eingabe selbst nichts zeigt (z. B. Division durch 0 bei leerer
 * Summe der Buchwerte der Stichprobe), steht die Eingabe nicht in der Liste.
 * Dazu die Werte ohne Grundlage (`kind: 'withoutBasis'`): der anzuwendende Umfang
 * für Zeitraum 2 aus der bloßen Untergrenze 3 und die Hochrechnung 0, solange
 * kein Zeitraum eine Fehlersumme trägt.
 * Werte ohne Grundlage lässt die Webfassung offen, solange eine Pflichteingabe
 * fehlt; bei vollständigen Pflichteingaben zeigt sie sie wie die Vorlage und
 * weist sie mit einem Hinweis in Warnfarbe aus (`evaluateSheet`, Hinweis
 * `without-basis`); die Würdigung ist dann nicht uneingeschränkt grün.
 * Jede Zeile ist durch mindestens einen Golden-Fall belegt (test/deviations.spec.ts).
 */
import type { CellAddress, Deviation } from '../../model/types'

function entries(cells: readonly CellAddress[], whenEmpty: readonly CellAddress[], template: string, reason: string, kind?: Deviation['kind']): Deviation[] {
  return cells.map((cell) => ({ cell, whenEmpty, template, reason, ...(kind ? { kind } : {}) }))
}

// Eingaben, von denen die Zwischengrößen abhängen (in Blattreihenfolge).
/** Prognostizierter Buchwert des Geschäftsjahres (C18). */
const FORECAST_BOOK_VALUE = ['C7', 'C14', 'C16']
/** Prognostizierte Anzahl der Einheiten der Zufallsschichten (C19). */
const FORECAST_UNITS = ['C8', 'C15', 'C17']
/** Rechnerischer und anzuwendender Gesamtumfang und seine Aufteilung (C36, C44–C47). */
const FIRST = [...FORECAST_BOOK_VALUE, ...FORECAST_UNITS, 'C28', 'C31', 'C32', 'C33']
/** Aktualisierter Buchwert des Geschäftsjahres nach Zeitraum 1 (C65). */
const UPDATED_BOOK_VALUE = ['C7', 'C53', 'C60']
/** Gewichtete Standardabweichung der Zeiträume 2 und 3 (C70). */
const REMAINING_DEVIATION = ['C54', 'C61', 'C62', 'C63']
/** Nenner der Standardneuberechnung nach Zeitraum 1 (C71). */
const DENOMINATOR_SECOND = [...FIRST, 'C25', 'C53', 'C60']
/** Ergebnis der ersten Neuberechnung in allen Ansätzen (C72–C74, C80, C84–C86). */
const SECOND = [...DENOMINATOR_SECOND, ...REMAINING_DEVIATION]
/** Globale gewichtete Standardabweichung nach Zeitraum 1 (C76). */
const GLOBAL_DEVIATION_SECOND = ['C8', 'C31', ...REMAINING_DEVIATION]
/** Globaler Gesamtumfang nach Zeitraum 1 (C77, C79, C81, C82). */
const GLOBAL_SECOND = [...UPDATED_BOOK_VALUE, 'C25', 'C28', ...GLOBAL_DEVIATION_SECOND]
/** Buchwert des Geschäftsjahres (C101). */
const BOOK_VALUE = ['C7', 'C53', 'C92']
/** Nenner der Standardneuberechnung nach Zeitraum 2 (C105). */
const DENOMINATOR_THIRD = [...SECOND, 'C92']
/** Endgültige Umfänge und alles, was von ihnen abhängt (C106, C112–C120, Genauigkeit). */
const THIRD = [...DENOMINATOR_THIRD, 'C93', 'C99']
/** Globale gewichtete Standardabweichung nach Zeitraum 2 (C108). */
const GLOBAL_DEVIATION_THIRD = ['C8', 'C31', 'C54', 'C62', 'C93', 'C99']
/** Globaler Gesamtumfang nach Zeitraum 2 (C109, C111, C114). */
const GLOBAL_THIRD = [...BOOK_VALUE, 'C25', 'C28', ...GLOBAL_DEVIATION_THIRD]

const ZERO = 'Wert mit 0 an Stelle der leeren Zelle'
const AMOUNT = 'Ohne die Buchwerte der Zeiträume gibt es keine Bezugsgröße; ein Betrag auf Grundlage von 0 € wäre irreführend.'
const UNITS = 'Ohne Angabe ist die Anzahl der Einheiten unbekannt, nicht null.'
const DEVIATION = 'Fehlt die Standardabweichung eines Zeitraums oder seine Anzahl der Einheiten, ist die gewichtete Standardabweichung nicht bestimmt.'
const FIRST_REASON = 'Ohne Buchwerte, Anzahl der Einheiten, voraussichtliche Fehlerquote und Standardabweichungen aller drei Zeiträume ist der Gesamtumfang nicht bestimmt; alle Folgegrößen bleiben offen.'
const FIRST_TEMPLATE = 'Wert auf Grundlage des mit 0 gerechneten Buchwerts, N = 0, AE = 0 bzw. σ_e = 0 (Gesamtumfang mindestens der Mindestumfang)'
const SECOND_REASON = 'Ohne die Ist-Werte des Zeitraums 2 und die aktualisierten Prognosen und Standardabweichungen ist die Neuberechnung nach Zeitraum 1 nicht bestimmt; die Folgegrößen bleiben offen.'
const SECOND_TEMPLATE = 'Wert auf Grundlage der mit 0 gerechneten Angabe (z. B. Umfang 0 oder 3, „✖ nicht anwendbar (Nenner ≤ 0)“)'
const THIRD_REASON = 'Ohne die Ist-Werte des Zeitraums 3 und die aktualisierte Standardabweichung ist die Neuberechnung nach Zeitraum 2 nicht bestimmt; endgültige Umfänge, Genauigkeit und Würdigung bleiben offen.'
const THIRD_TEMPLATE = 'Wert auf Grundlage der mit 0 gerechneten Angabe (z. B. Umfang 3, Auffüllung auf 30, Genauigkeit ohne den Beitrag des Zeitraums)'
const FLOOR_REASON =
  'Ohne gewählten Umfang für Zeitraum 2 bleibt in der Vorlage nur die Untergrenze von 3 Einheiten (MAX übergeht den leeren Bezug); als anzuwendender Umfang hätte sie keine Grundlage.'

/** Werte ohne Grundlage (`unfounded`): offen, solange eine Pflichteingabe fehlt; bei vollständigen Pflichteingaben wie die Vorlage mit Hinweis. */
const withoutBasis: readonly Deviation[] = [
  // Gewählter Umfang je nach Ansatz der Neuberechnung: Standard C73, Global C81, Erhöhung C83, keine Neuberechnung C46.
  ...entries(['C84'], ['C73', 'C81', 'C83', 'C46'], '3 (Untergrenze, obwohl für Zeitraum 2 kein Umfang bestimmt ist, z. B. beim leeren Formular oder bei „TE ≤ AE“)', FLOOR_REASON, 'withoutBasis'),
  ...entries(['C113', 'C117'], ['C84'], 'Wert auf Grundlage eines Umfangs von 3 Einheiten für Zeitraum 2, der nur die Untergrenze ist', FLOOR_REASON, 'withoutBasis'),
  ...entries(
    ['C127'],
    ['C49', 'C88', 'C122'],
    '0,00 € (kein Zeitraum trägt eine Fehlersumme)',
    'Solange kein Zeitraum eine Fehlersumme trägt, gibt es nichts hochzurechnen; ein extrapolierter Fehler von 0 € sähe wie ein Prüfergebnis aus.',
    'withoutBasis',
  ),
]

export const deviations: readonly Deviation[] = [
  ...entries(['C12'], ['C7'], '0 € abzüglich des Buchwerts der umfassenden Schicht', AMOUNT),
  ...entries(['C13'], ['C8'], '0 abzüglich der Einheiten der umfassenden Schicht', UNITS),
  ...entries(['C18'], FORECAST_BOOK_VALUE, ZERO, AMOUNT),
  ...entries(['C19'], FORECAST_UNITS, ZERO, UNITS),
  ...entries(['C27'], [...FORECAST_BOOK_VALUE, 'C25'], ZERO, 'Der zulässige Fehler setzt die Buchwerte aller Zeiträume und die Signifikanzschwelle voraus.'),
  ...entries(['C29'], [...FORECAST_BOOK_VALUE, 'C28'], ZERO, 'Der voraussichtliche Fehler setzt die Buchwerte aller Zeiträume und die voraussichtliche Fehlerquote voraus.'),
  ...entries(['C30'], FORECAST_BOOK_VALUE, 'Prüfhinweis auf Grundlage der vorhandenen Buchwerte', AMOUNT),
  ...entries(['C34'], [...FORECAST_UNITS, 'C31', 'C32', 'C33'], 'gewichtete Standardabweichung mit 0 an Stelle der leeren Zelle', DEVIATION),
  ...entries(['C36', 'C44', 'C45', 'C46', 'C47', 'C83'], FIRST, FIRST_TEMPLATE, FIRST_REASON),
  ...entries(['C58'], ['C53'], '0 € abzüglich des Buchwerts der umfassenden Schicht', AMOUNT),
  ...entries(['C59'], ['C54'], '0 abzüglich der Einheiten der umfassenden Schicht', UNITS),
  ...entries(['C65'], UPDATED_BOOK_VALUE, ZERO, AMOUNT),
  ...entries(['C66'], [...UPDATED_BOOK_VALUE, 'C25'], ZERO, 'Der aktualisierte zulässige Fehler setzt die Buchwerte aller Zeiträume und die Signifikanzschwelle voraus.'),
  ...entries(['C67'], [...UPDATED_BOOK_VALUE, 'C28'], ZERO, 'Der aktualisierte voraussichtliche Fehler setzt die Buchwerte aller Zeiträume und eine voraussichtliche Fehlerquote voraus.'),
  ...entries(['C68'], ['C31'], '0,00 € (leere Zelle zählt als 0)', 'Ohne Standardabweichung der Stichprobe und ohne voraussichtliche Standardabweichung gibt es keinen Wert für Zeitraum 1.'),
  ...entries(['C69'], ['C54', 'C61'], ZERO, UNITS),
  ...entries(['C70'], REMAINING_DEVIATION, 'gewichtete Standardabweichung mit 0 an Stelle der leeren Zelle', DEVIATION),
  ...entries(['C71'], DENOMINATOR_SECOND, 'Nenner auf Grundlage der mit 0 gerechneten Angabe', SECOND_REASON),
  ...entries(['C72', 'C73', 'C74', 'C80', 'C84', 'C85', 'C86', 'C115'], SECOND, SECOND_TEMPLATE, SECOND_REASON),
  ...entries(['C75'], ['C8', 'C54', 'C61'], ZERO, UNITS),
  ...entries(['C76'], GLOBAL_DEVIATION_SECOND, 'gewichtete Standardabweichung mit 0 an Stelle der leeren Zelle', DEVIATION),
  ...entries(['C77', 'C79', 'C81', 'C82'], GLOBAL_SECOND, 'Umfang auf Grundlage der mit 0 gerechneten Angabe (mindestens der Mindestumfang, gegebenenfalls begrenzt)', SECOND_REASON),
  ...entries(['C97'], ['C92'], '0 € abzüglich des Buchwerts der umfassenden Schicht', AMOUNT),
  ...entries(['C98'], ['C93'], '0 abzüglich der Einheiten der umfassenden Schicht', UNITS),
  ...entries(['C101', 'N4'], BOOK_VALUE, ZERO, AMOUNT),
  ...entries(['C102'], [...BOOK_VALUE, 'C25'], ZERO, 'Der endgültige zulässige Fehler setzt die Buchwerte aller Zeiträume und die Signifikanzschwelle voraus.'),
  ...entries(['C103'], [...BOOK_VALUE, 'C28'], ZERO, 'Der endgültige voraussichtliche Fehler setzt die Buchwerte aller Zeiträume und eine voraussichtliche Fehlerquote voraus.'),
  ...entries(['C104'], ['C62'], '0,00 € (leere Zelle zählt als 0)', 'Ohne Standardabweichung der Stichprobe und ohne aktualisierte Standardabweichung gibt es keinen Wert für Zeitraum 2.'),
  ...entries(['C105'], DENOMINATOR_THIRD, 'Nenner auf Grundlage der mit 0 gerechneten Angabe', THIRD_REASON),
  ...entries(['C107'], ['C8', 'C54', 'C93'], ZERO, UNITS),
  ...entries(['C108'], GLOBAL_DEVIATION_THIRD, 'gewichtete Standardabweichung mit 0 an Stelle der leeren Zelle', DEVIATION),
  ...entries(['C109', 'C111', 'C114'], GLOBAL_THIRD, 'Umfang auf Grundlage der mit 0 gerechneten Angabe (mindestens der Mindestumfang, gegebenenfalls begrenzt)', THIRD_REASON),
  ...entries(['C106', 'C112', 'C113', 'C116', 'C117', 'C118', 'C119', 'C120', 'N10'], THIRD, THIRD_TEMPLATE, THIRD_REASON),
  ...entries(['C127', 'C128', 'C135', 'C136', 'N5', 'N11'], BOOK_VALUE, 'Hochrechnung auf Grundlage eines mit 0 € gerechneten Buchwerts (bei umfassender Schicht ein negativer Betrag)', AMOUNT),
  ...entries(['C129', 'C132', 'C133', 'C134', 'C137', 'C138', 'N7'], THIRD, THIRD_TEMPLATE, THIRD_REASON),
  ...withoutBasis,
]
