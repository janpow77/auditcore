/**
 * Begründete Abweichungen des Blatts 07 vom Verhalten der Vorlage. In allen
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
 * trotzdem 50 bzw. 30 Einheiten. Liefert der gewählte Ansatz für Zeitraum 2 bzw.
 * 3 keinen Umfang – leeres Formular, „TE ≤ AE“, nicht anwendbare
 * Standardneuberechnung –, zeigt sie in C75 bzw. C109 nur die Untergrenzen. In
 * beiden Fällen rechnet sie damit weiter. Übersicht: docs/abweichungen.md.
 */
import type { CellAddress, Deviation } from '../../model/types'

function entries(cells: readonly CellAddress[], whenEmpty: readonly CellAddress[], template: string, reason: string): Deviation[] {
  return cells.map((cell) => ({ cell, whenEmpty, template, reason }))
}

const ZERO = '0,00 € bzw. der Wert mit 0 an Stelle der leeren Zelle'
const DEVIATION = 'Standardabweichung mit 0 an Stelle der leeren Zelle'
const RANDOM_STRATUM = '0 € abzüglich des Buchwerts der hochwertigen Einheiten'
const BOOK_VALUE = 'Ohne die Buchwerte der Zeiträume gibt es keine Bezugsgröße; ein Betrag auf Grundlage von 0 € wäre irreführend.'
const FIRST = 'Ohne Buchwerte, voraussichtliche Fehlerquote und Standardabweichungen aller Zeiträume ist der Gesamtumfang nicht bestimmt; alle Folgegrößen bleiben offen.'
const FIRST_TEMPLATE = 'Wert auf Grundlage des mit 0 gerechneten Buchwerts, AE = 0 bzw. σ_r = 0 (Gesamtumfang mindestens 30)'
const SECOND = 'Ohne Ist-Buchwert des zweiten Zeitraums, aktualisierte Prognose für den dritten und die aktualisierten Standardabweichungen ist die Neuberechnung nach Zeitraum 1 nicht bestimmt.'
const SECOND_TEMPLATE = 'Wert auf Grundlage von BV = 0 bzw. σ_r = 0 für die Zeiträume 2 und 3 (z. B. Umfang 0 oder 3)'
const THIRD = 'Ohne Ist-Buchwert und aktualisierte Standardabweichung des dritten Zeitraums ist die Neuberechnung nach Zeitraum 2 nicht bestimmt; endgültige Umfänge, Hochrechnung und Würdigung bleiben offen.'
const THIRD_TEMPLATE = 'Wert auf Grundlage von BV₃ = 0 bzw. σ_r3 = 0 (z. B. Umfang 0, 3 oder Auffüllung auf 30)'

const FACTOR = 'Der Faktor der Unterschätzung vergleicht den Ist-Buchwert des Zeitraums mit seiner Prognose; ohne beide ist die Erhöhung nicht bestimmt.'
const FACTOR_TEMPLATE = 'Planumfang mal Faktor 1 bzw. mal dem Faktor allein aus dem Verhältnis der Anzahlen (ein leerer Buchwert zählt als 0)'
const BOUNDS = 'Liefert der gewählte Ansatz keinen Umfang für den Zeitraum, gibt es nichts, was die Untergrenzen sichern könnten; ein Umfang von 3 bzw. die Auffüllung auf 30 sähe wie ein Ergebnis der Neuberechnung aus.'
const BOUNDS_TEMPLATE = 'Untergrenze 3 bzw. Auffüllung auf 30 (MAX übergeht den Text bzw. die leere Zelle des gewählten Umfangs)'
const AFTER_BOUNDS = 'Der Wert baut auf einem Umfang auf, den keine Neuberechnung ergeben hat; ohne ihn ist er nicht bestimmt.'
const AFTER_BOUNDS_TEMPLATE = 'Wert auf Grundlage eines Umfangs für Zeitraum 2 bzw. 3, der nur aus den Untergrenzen besteht'

/** Eingaben, von denen der Gesamtumfang und seine Aufteilung abhängen. */
const SIZE_INPUTS = ['C7', 'C8', 'C9', 'C21', 'C24', 'C25', 'C26']
/** Eingaben der Neuberechnung nach Zeitraum 1. */
const SECOND_INPUTS = ['C51', 'C53', 'C55', 'C56']
/** Eingaben der Neuberechnung nach Zeitraum 2. */
const THIRD_INPUTS = ['C90', 'C92']
/** Wie `SIZE_INPUTS`, ohne den Buchwert des ersten Zeitraums: Fehlt er, teilt die Vorlage durch 0 und zeigt nichts. */
const SIZE_WITHOUT_FIRST = SIZE_INPUTS.filter((cell) => cell !== 'C7')

const sizes: Deviation[] = [
  ...entries(['C12', 'C23'], ['C7', 'C8', 'C9'], ZERO, BOOK_VALUE),
  ...entries(['C20'], ['C7', 'C8', 'C9', 'C18'], ZERO, 'Der zulässige Fehler setzt die Buchwerte und die Wesentlichkeitsschwelle voraus.'),
  ...entries(['C22'], ['C7', 'C8', 'C9', 'C21'], ZERO, 'Der voraussichtliche Fehler setzt die Buchwerte und die voraussichtliche Fehlerquote voraus.'),
  ...entries(['C27'], ['C7', 'C8', 'C9', 'C24', 'C25', 'C26'], DEVIATION, 'Die gewichtete Standardabweichung setzt Buchwert und Standardabweichung aller Zeiträume voraus.'),
  ...entries(['C29', 'C35', 'C36', 'C37', 'C38', 'C43', 'C44', 'C45'], SIZE_INPUTS, FIRST_TEMPLATE, FIRST),
  ...entries(['C74'], [...SIZE_INPUTS, 'C51'], FACTOR_TEMPLATE, FACTOR),
  ...entries(['C39'], SIZE_WITHOUT_FIRST, FIRST_TEMPLATE, FIRST),
  ...entries(['C42'], ['C7'], RANDOM_STRATUM, BOOK_VALUE),
]

const second: Deviation[] = [
  ...entries(['C58'], ['C7', 'C51', 'C53'], ZERO, BOOK_VALUE),
  ...entries(['C59'], ['C7', 'C18', 'C51', 'C53'], ZERO, 'Der aktualisierte zulässige Fehler setzt die Buchwerte und die Wesentlichkeitsschwelle voraus.'),
  ...entries(['C60'], ['C7', 'C21', 'C51', 'C53'], ZERO, 'Der aktualisierte voraussichtliche Fehler setzt die Buchwerte und eine voraussichtliche Fehlerquote voraus.'),
  ...entries(['C61'], ['C24'], '0,0000 (leere Zelle zählt als 0)', 'Ohne Standardabweichung der Stichprobe und ohne voraussichtliche Standardabweichung gibt es keinen Wert für Zeitraum 1.'),
  ...entries(['C62'], ['C51', 'C53'], ZERO, BOOK_VALUE),
  ...entries(['C63'], SECOND_INPUTS, DEVIATION, SECOND),
  ...entries(['C64'], [...SIZE_WITHOUT_FIRST, 'C51', 'C53'], 'Nenner auf Grundlage des mit 0 gerechneten Werts', SECOND),
  ...entries(['C65', 'C66', 'C67'], [...SIZE_WITHOUT_FIRST, ...SECOND_INPUTS], SECOND_TEMPLATE, SECOND),
  ...entries(['C68'], ['C7', 'C24', ...SECOND_INPUTS], DEVIATION, SECOND),
  ...entries(['C69', 'C70', 'C72', 'C73'], ['C7', 'C18', 'C21', 'C24', ...SECOND_INPUTS], 'Umfang auf Grundlage des mit 0 gerechneten Werts (mindestens 30)', SECOND),
  ...entries(['C71', 'C75', 'C76', 'C77', 'C78', 'C82', 'C83', 'C84'], [...SIZE_INPUTS, ...SECOND_INPUTS], SECOND_TEMPLATE, SECOND),
  ...entries(['C106'], [...SIZE_INPUTS, ...SECOND_INPUTS, 'C90'], FACTOR_TEMPLATE, FACTOR),
  ...entries(['C81'], ['C51'], RANDOM_STRATUM, BOOK_VALUE),
]

const third: Deviation[] = [
  ...entries(['C94', 'N4'], ['C7', 'C51', 'C90'], ZERO, BOOK_VALUE),
  ...entries(['C95'], ['C7', 'C18', 'C51', 'C90'], ZERO, 'Der zulässige Fehler des Geschäftsjahres setzt die Ist-Buchwerte und die Wesentlichkeitsschwelle voraus.'),
  ...entries(['C96'], ['C7', 'C21', 'C51', 'C90'], ZERO, 'Der voraussichtliche Fehler des Geschäftsjahres setzt die Ist-Buchwerte und eine voraussichtliche Fehlerquote voraus.'),
  ...entries(['C97'], ['C55'], '0,0000 (leere Zelle zählt als 0)', 'Ohne Standardabweichung der Stichprobe und ohne aktualisierte Standardabweichung gibt es keinen Wert für Zeitraum 2.'),
  ...entries(['C98'], [...SIZE_WITHOUT_FIRST, ...SECOND_INPUTS, 'C90'], 'Nenner auf Grundlage des mit 0 gerechneten Werts', THIRD),
  ...entries(['C99'], [...SIZE_WITHOUT_FIRST, ...SECOND_INPUTS, ...THIRD_INPUTS], THIRD_TEMPLATE, THIRD),
  ...entries(['C100'], ['C7', 'C24', 'C51', 'C55', ...THIRD_INPUTS], DEVIATION, THIRD),
  ...entries(['C101', 'C102', 'C105'], ['C7', 'C18', 'C21', 'C24', 'C51', 'C55', ...THIRD_INPUTS], 'Umfang auf Grundlage des mit 0 gerechneten Werts (mindestens 30)', THIRD),
  ...entries(['C104'], [...SIZE_INPUTS, 'C18', ...SECOND_INPUTS, ...THIRD_INPUTS], THIRD_TEMPLATE, THIRD),
  ...entries(['C115'], ['C90'], RANDOM_STRATUM, BOOK_VALUE),
  ...entries(
    ['C103', 'C107', 'C108', 'C109', 'C110', 'C111', 'C112', 'C116', 'C117', 'C118', 'C124', 'C125', 'C127', 'C128', 'C129', 'C132', 'C133', 'C134', 'C135', 'C136', 'C137', 'C138', 'N5', 'N7', 'N10', 'N11'],
    [...SIZE_INPUTS, ...SECOND_INPUTS, ...THIRD_INPUTS],
    THIRD_TEMPLATE,
    THIRD,
  ),
]

/** Zellen, die auf dem anzuwendenden Umfang für Zeitraum 3 (C109) aufbauen. */
const AFTER_THIRD = ['C110', 'C111', 'C112', 'C116', 'C117', 'C118', 'C127', 'C128', 'C129', 'C132', 'C133', 'C134', 'C135', 'C136', 'C137', 'C138', 'N5', 'N7', 'N10', 'N11']
/** Zellen, die schon auf dem anzuwendenden Umfang für Zeitraum 2 (C75) aufbauen. */
const AFTER_SECOND = ['C78', 'C82', 'C83', 'C84', 'C98', 'C99', 'C104', 'C108', 'C125']

const CAP = 'Ohne rechnerischen Umfang gibt es nichts zu begrenzen; der begrenzte Umfang allein sähe wie ein Ergebnis aus.'
const CAP_TEMPLATE = 'begrenzter Umfang (50 bzw. 30 Einheiten), obwohl die Zelle des rechnerischen Umfangs leer ist'
/** Zellen, die auf einem anzuwendenden Gesamtumfang (C35, C70, C102) aufbauen. */
const AFTER_CAP = [
  'C36', 'C37', 'C38', 'C39', 'C43', 'C44', 'C45', 'C64', 'C65', 'C66', 'C67', 'C71', 'C72', 'C73', 'C74', 'C75', 'C76', 'C77', 'C103', 'C105', 'C106', 'C107', 'C109', 'C124',
  ...AFTER_SECOND,
  ...AFTER_THIRD,
]

/**
 * Werte ohne Grundlage. `whenEmpty` nennt C75 bzw. C109 selbst: Die fehlende
 * Größe ist der Umfang nach dem gewählten Ansatz, und der steht bei nicht
 * anwendbarer Standardneuberechnung als Text in C99 – die Zelle ist dann nicht leer.
 */
const withoutBasis: Deviation[] = [
  { cell: 'C35', whenEmpty: ['C29'], template: CAP_TEMPLATE, reason: CAP, kind: 'withoutBasis' },
  { cell: 'C70', whenEmpty: ['C69'], template: CAP_TEMPLATE, reason: CAP, kind: 'withoutBasis' },
  { cell: 'C102', whenEmpty: ['C101'], template: CAP_TEMPLATE, reason: CAP, kind: 'withoutBasis' },
  ...AFTER_CAP.map((cell): Deviation => ({
    cell,
    whenEmpty: ['C29', 'C69', 'C101'],
    template: 'Wert auf Grundlage eines begrenzten Umfangs, den kein rechnerischer Umfang trägt',
    reason: 'Der Wert baut auf dem begrenzten Umfang auf; ohne rechnerischen Umfang ist er nicht bestimmt.',
    kind: 'withoutBasis',
  })),
  { cell: 'C75', whenEmpty: ['C75'], template: BOUNDS_TEMPLATE, reason: BOUNDS, kind: 'withoutBasis' },
  { cell: 'C109', whenEmpty: ['C75', 'C109'], template: BOUNDS_TEMPLATE, reason: BOUNDS, kind: 'withoutBasis' },
  ...AFTER_SECOND.map((cell): Deviation => ({ cell, whenEmpty: ['C75'], template: AFTER_BOUNDS_TEMPLATE, reason: AFTER_BOUNDS, kind: 'withoutBasis' })),
  ...AFTER_THIRD.map((cell): Deviation => ({ cell, whenEmpty: ['C75', 'C109'], template: AFTER_BOUNDS_TEMPLATE, reason: AFTER_BOUNDS, kind: 'withoutBasis' })),
]

export const deviations: readonly Deviation[] = [...sizes, ...second, ...third, ...withoutBasis]
