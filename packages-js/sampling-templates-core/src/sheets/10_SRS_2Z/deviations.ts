/**
 * Begründete Abweichungen des Blatts 10 vom Verhalten der Vorlage bei leeren
 * Eingaben. In allen Fällen zeigt die Webfassung „Angabe fehlt“ (`null`), nie
 * einen anderen Wert als die Vorlage. `whenEmpty` nennt je Zelle die Eingaben,
 * deren Fehlen in den Golden-Fällen die Abweichung auslöst – jede ist durch
 * einen Fall „alles ausgefüllt außer …“ belegt. Wo die Vorlage bei einer
 * fehlenden Eingabe selbst nichts zeigt (z. B. C33 ohne Wesentlichkeitsschwelle),
 * steht die Eingabe nicht in der Liste. Dazu die Werte ohne Grundlage
 * (`kind: 'withoutBasis'`): der anzuwendende Umfang für Zeitraum 2 aus den bloßen
 * Untergrenzen und die Hochrechnung 0, solange kein Zeitraum eine Fehlersumme trägt.
 */
import type { CellAddress, Deviation } from '../../model/types'

function entries(cells: readonly CellAddress[], whenEmpty: readonly CellAddress[], template: string, reason: string, kind?: Deviation['kind']): Deviation[] {
  return cells.map((cell) => ({ cell, whenEmpty, template, reason, ...(kind ? { kind } : {}) }))
}

const ZERO = '0 bzw. der Wert mit 0 an Stelle der leeren Zelle'
const BOOK_VALUE = 'Ohne die Buchwerte der Zeiträume gibt es keine Bezugsgröße; ein Betrag auf Grundlage von 0 € wäre irreführend.'
const UNITS = 'Ohne Angabe ist die Anzahl der Einheiten eines Zeitraums unbekannt, nicht null.'
const DEVIATION = 'Die gewichtete Standardabweichung setzt Anzahl der Einheiten und Standardabweichung beider Zeiträume voraus.'
const FIRST = 'Ohne Buchwerte, Anzahl der Einheiten, voraussichtliche Fehlerquote und Standardabweichungen beider Zeiträume ist der Gesamtumfang nicht bestimmt; alle Folgegrößen bleiben offen.'
const FIRST_TEMPLATE = 'Wert auf Grundlage von BV = 0, N = 0, AE = 0 bzw. σ_e = 0 (z. B. Mindestumfang oder begrenzter Umfang)'
const SECOND = 'Ohne Ist-Werte und aktualisierte Standardabweichung des zweiten Zeitraums ist die Neuberechnung nicht bestimmt; die Folgegrößen bleiben offen.'
const SECOND_TEMPLATE = 'Wert auf Grundlage von BV₂ = 0, N₂ = 0 bzw. σ_e2 = 0 (z. B. Umfang 0, 3 oder Auffüllung auf 30)'
const FLOOR_REASON =
  'Ergibt die Standardneuberechnung keinen Umfang, ohne dass ihr Nenner als nicht positiv ausgewiesen ist, bleiben in der Vorlage nur die Untergrenzen (MAX übergeht den leeren Bezug); als anzuwendender Umfang hätten sie keine Grundlage.'
const FINAL = 'Ohne die Angaben zum Gesamtumfang und zur Neuberechnung für Zeitraum 2 sind die endgültigen Umfänge nicht bestimmt; Genauigkeit, Fehlergrenzen und Würdigung bleiben offen.'

/** Eingaben, von denen der Gesamtumfang des ersten Zeitraums und seine Aufteilung abhängen. */
const SIZE_INPUTS = ['C7', 'C8', 'C14', 'C15', 'C26', 'C29', 'C30']
/** Dazu die Wesentlichkeitsschwelle und die Eingaben der Neuberechnung für Zeitraum 2. */
const ALL_INPUTS = ['C7', 'C8', 'C14', 'C15', 'C23', 'C26', 'C29', 'C30', 'C49', 'C50', 'C56']

export const deviations: readonly Deviation[] = [
  ...entries(['C12'], ['C7'], '0 € abzüglich des Buchwerts der umfassenden Schicht', BOOK_VALUE),
  ...entries(['C13'], ['C8'], '0 abzüglich der Einheiten der umfassenden Schicht', UNITS),
  ...entries(['C16'], ['C7', 'C14'], ZERO, BOOK_VALUE),
  ...entries(['C17'], ['C8', 'C15'], ZERO, UNITS),
  ...entries(['C25'], ['C7', 'C14', 'C23'], ZERO, 'Der zulässige Fehler setzt beide Buchwerte und die Wesentlichkeitsschwelle voraus.'),
  ...entries(['C27'], ['C7', 'C14', 'C26'], ZERO, 'Der voraussichtliche Fehler setzt beide Buchwerte und die voraussichtliche Fehlerquote voraus.'),
  ...entries(['C28'], ['C7', 'C14'], 'Prüfhinweis auf Grundlage nur eines Buchwerts', BOOK_VALUE),
  ...entries(['C31'], ['C8', 'C15', 'C29', 'C30'], 'gewichtete Standardabweichung mit 0 an Stelle der leeren Zelle', DEVIATION),
  ...entries(['C33', 'C41', 'C42', 'C43', 'C71'], SIZE_INPUTS, FIRST_TEMPLATE, FIRST),
  ...entries(['C54'], ['C49'], '0 € abzüglich des Buchwerts der umfassenden Schicht', BOOK_VALUE),
  ...entries(['C55'], ['C50'], '0 abzüglich der Einheiten der umfassenden Schicht', UNITS),
  ...entries(['C58', 'N4'], ['C7', 'C49'], ZERO, BOOK_VALUE),
  ...entries(['C59'], ['C7', 'C23', 'C49'], ZERO, 'Der aktualisierte zulässige Fehler setzt beide Ist-Buchwerte und die Wesentlichkeitsschwelle voraus.'),
  ...entries(['C60'], ['C7', 'C26', 'C49'], ZERO, 'Der aktualisierte voraussichtliche Fehler setzt beide Ist-Buchwerte und eine voraussichtliche Fehlerquote voraus.'),
  ...entries(['C61'], ['C29'], '0,00 € (leere Zelle zählt als 0)', 'Ohne Standardabweichung der Stichprobe und ohne voraussichtliche Standardabweichung gibt es keinen Wert für Zeitraum 1.'),
  ...entries(['C62'], ['C7', 'C8', 'C14', 'C15', 'C23', 'C26', 'C29', 'C30', 'C49'], 'Nenner auf Grundlage des mit 0 gerechneten Werts', SECOND),
  ...entries(['C64'], ['C8', 'C50'], ZERO, UNITS),
  ...entries(['C65'], ['C8', 'C29', 'C50', 'C56'], 'gewichtete Standardabweichung mit 0 an Stelle der leeren Zelle', DEVIATION),
  ...entries(['C66', 'C68', 'C70'], ['C7', 'C8', 'C23', 'C26', 'C29', 'C49', 'C50', 'C56'], 'Umfang auf Grundlage des mit 0 gerechneten Werts (mindestens der Mindestumfang)', SECOND),
  ...entries(['C63', 'C69', 'C72', 'C73', 'C74', 'C75', 'C76', 'N10'], ALL_INPUTS, SECOND_TEMPLATE, SECOND),
  ...entries(['C83', 'C84', 'C91', 'C92', 'N5', 'N11'], ['C7', 'C49'], 'Hochrechnung auf Grundlage von 0 € abzüglich des Buchwerts der umfassenden Schicht (negativer Betrag)', BOOK_VALUE),
  ...entries(['C85', 'C88', 'C89', 'C90', 'C93', 'N7'], ALL_INPUTS, 'Wert auf Grundlage der mit 0 gerechneten Umfänge bzw. einer Zufallsschicht mit N ≤ 0', FINAL),
  ...entries(['C94'], ['C7', 'C8', 'C14', 'C15', 'C26', 'C29', 'C30', 'C49', 'C50', 'C56'], 'Würdigung auf Grundlage der mit 0 gerechneten Genauigkeit', FINAL),
  // Werte ohne Grundlage (`unfounded`): Die Webfassung zeigt sie nach der geltenden Richtlinie nicht.
  ...entries(
    ['C73', 'C74', 'C75', 'C76', 'N10'],
    ['C63'],
    'Untergrenzen (mindestens 3, Auffüllung auf 30) bzw. die darauf aufbauende Gesamtstichprobe und ihre Prüfhinweise, obwohl die Standardneuberechnung keinen Umfang ergibt (z. B. ohne Konfidenzniveau oder ohne Einheiten der Zufallsschicht in Zeitraum 1)',
    FLOOR_REASON,
    'withoutBasis',
  ),
  ...entries(
    ['C83'],
    ['C45', 'C78'],
    '0,00 € (kein Zeitraum trägt eine Fehlersumme)',
    'Solange kein Zeitraum eine Fehlersumme trägt, gibt es nichts hochzurechnen; ein extrapolierter Fehler von 0 € sähe wie ein Prüfergebnis aus.',
    'withoutBasis',
  ),
]
