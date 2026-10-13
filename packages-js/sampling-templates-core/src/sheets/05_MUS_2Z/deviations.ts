/**
 * Begründete Abweichungen des Blatts 05 vom Verhalten der Vorlage. In allen
 * Fällen zeigt die Webfassung keinen Wert (`null`), nie einen anderen Wert als
 * die Vorlage.
 *
 * Pflichteingaben (ohne `kind`): `whenEmpty` nennt je Zelle die Eingaben, deren
 * Fehlen in den Golden-Fällen die Abweichung auslöst; wo die Vorlage bei einer
 * fehlenden Eingabe selbst nichts zeigt (z. B. Division durch 0), steht die
 * Eingabe nicht in der Liste.
 *
 * Werte ohne Grundlage (`kind: 'withoutBasis'`): Ist der rechnerische Umfang
 * leer (etwa ohne Konfidenzniveau), zeigt die Vorlage bei begrenztem Umfang
 * trotzdem 50 bzw. 30 Einheiten. Liefert der gewählte Ansatz für Zeitraum 2
 * keinen Umfang – die Standardneuberechnung ist nicht anwendbar (Text in C57) –,
 * zeigt sie in C67 nur die Untergrenzen. In beiden Fällen rechnet sie damit
 * weiter. Übersicht: docs/abweichungen.md.
 */
import { PROJECTION_WITHOUT_ERRORS } from '../../model/policy'
import type { CellAddress, Deviation } from '../../model/types'

function entries(cells: readonly CellAddress[], whenEmpty: readonly CellAddress[], template: string, reason: string): Deviation[] {
  return cells.map((cell) => ({ cell, whenEmpty, template, reason }))
}

const ZERO = '0,00 € bzw. der Wert mit 0 an Stelle der leeren Zelle'
const BOOK_VALUE = 'Ohne die Buchwerte der Zeiträume gibt es keine Bezugsgröße; ein Betrag auf Grundlage von 0 € wäre irreführend.'
const FIRST = 'Ohne Buchwerte, voraussichtliche Fehlerquote und Standardabweichungen beider Zeiträume ist der Gesamtumfang nicht bestimmt; alle Folgegrößen bleiben offen.'
const FIRST_TEMPLATE = 'Wert auf Grundlage des mit 0 gerechneten Buchwerts, AE = 0 bzw. σ_r = 0 (Gesamtumfang mindestens 30)'
const SECOND = 'Ohne Ist-Buchwert und aktualisierte Standardabweichung des zweiten Zeitraums ist die Neuberechnung nicht bestimmt; die Folgegrößen bleiben offen.'
const SECOND_TEMPLATE = 'Wert auf Grundlage von BV₂ = 0 bzw. σ_r2 = 0 (z. B. Umfang 0, 3 oder Auffüllung auf 30)'

const FACTOR = 'Der Faktor der Unterschätzung vergleicht den Ist-Buchwert des zweiten Zeitraums mit seiner Prognose; ohne beide ist die Erhöhung nicht bestimmt.'
const BOUNDS = 'Liefert der gewählte Ansatz keinen Umfang für Zeitraum 2, gibt es nichts, was die Untergrenzen sichern könnten; ein Umfang von 3 bzw. die Auffüllung auf 30 sähe wie ein Ergebnis der Neuberechnung aus.'

/** Eingaben, von denen der Gesamtumfang und seine Aufteilung abhängen. */
const SIZE_INPUTS = ['C7', 'C8', 'C20', 'C23', 'C24']
/** Dazu die Eingaben der Neuberechnung für Zeitraum 2. */
const ALL_INPUTS = [...SIZE_INPUTS, 'C48', 'C50']

const CAP = 'Ohne rechnerischen Umfang gibt es nichts zu begrenzen; der begrenzte Umfang allein sähe wie ein Ergebnis aus.'
const CAP_TEMPLATE = 'begrenzter Umfang (50 bzw. 30 Einheiten), obwohl die Zelle des rechnerischen Umfangs leer ist'

/** Zellen, die auf dem anzuwendenden Umfang für Zeitraum 2 (C67) aufbauen. */
const AFTER_SIZE = ['C68', 'C69', 'C70', 'C74', 'C75', 'C76', 'C84', 'C85', 'C86', 'C89', 'C90', 'C91', 'C92', 'C93', 'C94', 'C95', 'N5', 'N7', 'N10', 'N11']

/**
 * Werte ohne Grundlage. `whenEmpty` nennt C67 selbst: Die fehlende Größe ist der
 * Umfang nach dem gewählten Ansatz, und der steht bei nicht anwendbarer
 * Standardneuberechnung als Text in C57 – die Zelle ist dann nicht leer.
 */
const withoutBasis: Deviation[] = [
  { cell: 'C33', whenEmpty: ['C27'], template: CAP_TEMPLATE, reason: CAP, kind: 'withoutBasis' },
  { cell: 'C60', whenEmpty: ['C59'], template: CAP_TEMPLATE, reason: CAP, kind: 'withoutBasis' },
  ...['C34', 'C35', 'C36', 'C40', 'C41', 'C42', 'C56', 'C57', 'C61', 'C62', 'C63', 'C65', 'C66', 'C67', 'C79', ...AFTER_SIZE].map((cell): Deviation => ({
    cell,
    whenEmpty: ['C27', 'C59'],
    template: 'Wert auf Grundlage eines begrenzten Umfangs, den kein rechnerischer Umfang trägt',
    reason: 'Der Wert baut auf dem begrenzten Umfang auf; ohne rechnerischen Umfang ist er nicht bestimmt.',
    kind: 'withoutBasis',
  })),
  { cell: 'C67', whenEmpty: ['C67'], template: 'Untergrenze 3 bzw. Auffüllung auf 30 (MAX übergeht den Text bzw. die leere Zelle des gewählten Umfangs)', reason: BOUNDS, kind: 'withoutBasis' },
  ...AFTER_SIZE.map((cell): Deviation => ({
    cell,
    whenEmpty: ['C67'],
    template: 'Wert auf Grundlage eines Umfangs für Zeitraum 2, der nur aus den Untergrenzen besteht',
    reason: 'Der Wert baut auf einem Umfang für Zeitraum 2 auf, den keine Neuberechnung ergeben hat; ohne ihn ist er nicht bestimmt.',
    kind: 'withoutBasis',
  })),
]

export const deviations: readonly Deviation[] = [
  ...entries(['C11'], ['C7', 'C8'], ZERO, BOOK_VALUE),
  ...entries(['C19'], ['C7', 'C8', 'C17'], ZERO, 'Der zulässige Fehler setzt beide Buchwerte und die Wesentlichkeitsschwelle voraus.'),
  ...entries(['C21'], ['C7', 'C8', 'C20'], ZERO, 'Der voraussichtliche Fehler setzt beide Buchwerte und die voraussichtliche Fehlerquote voraus.'),
  ...entries(['C22'], ['C7', 'C8'], 'Prüfhinweis auf Grundlage nur eines Buchwerts', BOOK_VALUE),
  ...entries(['C25'], ['C7', 'C8', 'C23', 'C24'], 'gewichtete Standardabweichung mit 0 an Stelle der leeren Zelle', 'Die gewichtete Standardabweichung setzt Buchwert und Standardabweichung beider Zeiträume voraus.'),
  ...entries(['C27', 'C33', 'C34', 'C35', 'C40', 'C41', 'C42'], SIZE_INPUTS, FIRST_TEMPLATE, FIRST),
  ...entries(['C36'], ['C8', 'C20', 'C23', 'C24'], FIRST_TEMPLATE, FIRST),
  ...entries(['C39'], ['C7'], '0 € abzüglich des Buchwerts der hochwertigen Einheiten', BOOK_VALUE),
  ...entries(['C52', 'N4'], ['C7', 'C48'], ZERO, BOOK_VALUE),
  ...entries(['C53'], ['C7', 'C17', 'C48'], ZERO, 'Der aktualisierte zulässige Fehler setzt beide Ist-Buchwerte und die Wesentlichkeitsschwelle voraus.'),
  ...entries(['C54'], ['C7', 'C20', 'C48'], ZERO, 'Der aktualisierte voraussichtliche Fehler setzt beide Ist-Buchwerte und eine voraussichtliche Fehlerquote voraus.'),
  ...entries(['C55'], ['C23'], '0,0000 (leere Zelle zählt als 0)', 'Ohne Standardabweichung der Stichprobe und ohne voraussichtliche Standardabweichung gibt es keinen Wert für Zeitraum 1.'),
  ...entries(['C56'], ['C8', 'C20', 'C23', 'C24', 'C48'], 'Nenner auf Grundlage des mit 0 gerechneten Werts', SECOND),
  ...entries(['C57'], ['C8', 'C20', 'C23', 'C24', 'C48', 'C50'], SECOND_TEMPLATE, SECOND),
  ...entries(['C58'], ['C7', 'C23', 'C48', 'C50'], 'gewichtete Standardabweichung mit 0 an Stelle der leeren Zelle', SECOND),
  ...entries(['C59', 'C60', 'C61', 'C63'], ['C7', 'C17', 'C20', 'C23', 'C48', 'C50'], 'Umfang auf Grundlage des mit 0 gerechneten Werts (mindestens 30)', SECOND),
  ...entries(['C64'], ['C8', 'C48'], 'Faktor 1 bzw. der Faktor allein aus dem Verhältnis der Anzahlen (ein leerer Buchwert zählt als 0)', FACTOR),
  ...entries(['C65'], [...SIZE_INPUTS, 'C48'], 'geplanter Umfang mal Faktor 1 bzw. mal dem Faktor allein aus dem Verhältnis der Anzahlen', FACTOR),
  ...entries(['C73'], ['C48'], '0 € abzüglich des Buchwerts der hochwertigen Einheiten', BOOK_VALUE),
  ...entries(
    ['C62', 'C66', 'C67', 'C68', 'C69', 'C70', 'C74', 'C75', 'C76', 'C79', 'C84', 'C85', 'C86', 'C89', 'C90', 'C91', 'C92', 'C93', 'C94', 'C95', 'N5', 'N7', 'N10', 'N11'],
    ALL_INPUTS,
    SECOND_TEMPLATE,
    'Ohne die Angaben zum Gesamtumfang und zur Neuberechnung für Zeitraum 2 sind die endgültigen Umfänge nicht bestimmt; Auswahl, Hochrechnung und Würdigung bleiben offen.',
  ),
  ...withoutBasis,
  { cell: 'C84', whenEmpty: ['C46', 'C81'], ...PROJECTION_WITHOUT_ERRORS },
]
