/**
 * Begründete Abweichungen des Blatts 06. In allen Fällen zeigt die Webfassung
 * keinen Wert (`null`), nie einen anderen Wert als die Vorlage.
 *
 * Pflichteingaben (ohne `kind`): Wesentlichkeitsschwelle, voraussichtliche
 * Fehlerquote und die Standardabweichungen einer belegten Schicht (Zeilen 24, 25
 * und 53; die Vorlage rechnet sie dort mit `N(…)` als 0). `whenEmpty` nennt je
 * Zelle die Eingaben, deren Fehlen in den Golden-Fällen die Abweichung auslöst.
 *
 * Werte ohne Grundlage (`kind: 'withoutBasis'`): die Summe 0 über eine
 * Schichtzeile, in der keine Schicht einen Wert trägt, und alles, was auf dieser
 * 0 aufbaut; der bestandene Prüfhinweis „✔ ≥ 3“ ohne Einheiten der Zufallsschicht;
 * die Untergrenze 3 ohne Planumfang. `whenEmpty` nennt dort die leere Summe bzw.
 * die leere Schichtzelle. Geführt sind alle Schichtspalten des Blatts (D–J und
 * AA–AM); belegt ist jede Zeile in mindestens einer Spalte der Vorlage.
 */
import { STRATA_COLUMNS, stratumCell } from '../../model/strata'
import type { Deviation } from '../../model/types'

function entries(cells: readonly string[], whenEmpty: readonly string[], template: string, reason: string): Deviation[] {
  return cells.map((cell) => ({ cell, whenEmpty, template, reason }))
}

/** Zellen einer Schichtzeile in allen Schichtspalten. */
const row = (number: number): string[] => STRATA_COLUMNS.map((column) => stratumCell(column, number))
const rows = (...numbers: number[]): string[] => numbers.flatMap(row)
/** Je Schichtspalte ein Eintrag: Zelle der Zeile `cell`, leer ist eine der Zeilen `inputs` derselben Schicht. */
const perStratum = (cell: number, inputs: readonly number[], template: string, reason: string): Deviation[] =>
  STRATA_COLUMNS.flatMap((column) => entries([stratumCell(column, cell)], inputs.map((input) => stratumCell(column, input)), template, reason))

const SIGMA1 = row(24)
const SIGMA2 = row(25)
const SIGMA_UPDATED = row(53)
const SIZE_INPUTS = ['C20', ...SIGMA1, ...SIGMA2]
const ALL_INPUTS = [...SIZE_INPUTS, ...SIGMA_UPDATED]

const ZERO = '0,00 € (leere Zelle zählt als 0)'
const TERM = 'Hilfswert ohne den Beitrag der fehlenden Standardabweichung (σ zählt als 0)'
const SIGMA = 'Fehlt die Standardabweichung einer belegten Schicht, ist die gewichtete Standardabweichung nicht bestimmt.'
const SIZE = 'Ohne voraussichtliche Fehlerquote und Standardabweichung jeder belegten Schicht ist der Gesamtumfang nicht bestimmt; alle Folgegrößen bleiben offen.'
const SIZE_TEMPLATE = 'Wert auf Grundlage des mit AE = 0 bzw. σ_rh = 0 berechneten Umfangs (mindestens 30)'
const SECOND = 'Ohne aktualisierte Standardabweichung jeder im zweiten Zeitraum belegten Schicht ist die Neuberechnung nicht bestimmt; die Folgegrößen bleiben offen.'
const SECOND_TEMPLATE = 'Wert auf Grundlage von σ_rh = 0 bzw. AE = 0 (z. B. Umfang 0 oder 3 je Schicht)'
const FINAL_SIZES = 'Ohne die Angaben zum Gesamtumfang und zur Neuberechnung sind die endgültigen Umfänge nicht bestimmt; Hochrechnung und Würdigung bleiben offen.'

const required: readonly Deviation[] = [
  ...entries(['C19', 'C56'], ['C17'], ZERO, 'Der zulässige Fehler setzt die Wesentlichkeitsschwelle voraus.'),
  ...entries(['C21', 'C57'], ['C20'], ZERO, 'Der voraussichtliche Fehler setzt die voraussichtliche Fehlerquote voraus.'),
  ...perStratum(26, [24, 25], TERM, SIGMA),
  ...entries(['C26', 'C27'], [...SIGMA1, ...SIGMA2], 'Wert ohne den Beitrag der Schicht mit fehlender Standardabweichung', SIGMA),
  ...entries(['C29', 'C35', 'C37', 'C38', 'C44', 'C60', ...rows(37, 38, 40, 44, 45, 46, 60)], SIZE_INPUTS, SIZE_TEMPLATE, SIZE),
  ...perStratum(59, [24], '0,0000 (leere Zelle zählt als 0)', 'Ohne Standardabweichung der Stichprobe und ohne voraussichtliche Standardabweichung gibt es keinen Wert für die Schicht.'),
  ...perStratum(61, [53], TERM, SECOND),
  ...entries(['C61'], SIGMA_UPDATED, TERM, SECOND),
  ...entries(['C62'], ['C17', ...SIZE_INPUTS], 'Nenner auf Grundlage des mit 0 gerechneten Werts', SIZE),
  ...perStratum(64, [24, 53], TERM, SECOND),
  ...entries(['C64'], [...SIGMA1, ...SIGMA_UPDATED], TERM, SECOND),
  ...entries(['C65', 'C66'], ['C17', 'C20', ...SIGMA1, ...SIGMA_UPDATED], 'Umfang auf Grundlage des mit 0 gerechneten Werts (mindestens 30)', SECOND),
  ...entries(['C63', 'C69', 'C72', 'C78', 'N10', ...rows(69, 74, 78, 79, 80)], ['C17', ...ALL_INPUTS], SECOND_TEMPLATE, SECOND),
  ...entries(['C68', 'C70', 'C71', 'C84', ...rows(68, 70, 84, 87, 88)], ALL_INPUTS, SECOND_TEMPLATE, FINAL_SIZES),
  ...entries(
    ['C87', 'C88', 'C89', 'C90', 'C93', 'C94', 'C95', 'C96', 'C97', 'C98', 'C99', 'N5', 'N7', 'N11'],
    ['C17', ...ALL_INPUTS],
    SECOND_TEMPLATE,
    FINAL_SIZES,
  ),
]

/** Zellen, die auf einer Summe ohne Summanden aufbauen: Die Vorlage rechnet mit deren 0 weiter. */
function built(cells: readonly string[], totals: readonly string[], template: string): Deviation[] {
  return cells.map((cell) => ({
    cell,
    whenEmpty: totals,
    template,
    reason: 'Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt.',
    kind: 'withoutBasis',
  }))
}

/** Hochrechnung, Genauigkeit, Fehlergrenzen und Würdigung samt Ergebnisübersicht. */
const RESULTS = ['C87', 'C88', 'C89', 'C90', 'C93', 'C94', 'C95', 'C96', 'C97', 'C98', 'C99', 'N5', 'N7', 'N11']
/** Standardneuberechnung und die Auswahl für Zeitraum 2, die auf ihr aufbaut. */
const STANDARD = ['C62', 'C63', 'C69', 'C72', 'C78', 'N10', ...rows(69, 74, 78, 79, 80)]
/** Globale Neuberechnung und endgültige Umfänge für Zeitraum 1. */
const FINAL = ['C65', 'C66', 'C68', 'C70', 'C71', 'C84', ...rows(68, 70, 84, 87, 88)]

const CAP = 'Ohne rechnerischen Umfang gibt es nichts zu begrenzen; der begrenzte Umfang allein sähe wie ein Ergebnis aus.'
const CAP_TEMPLATE = 'begrenzter Umfang (50 bzw. 30 Einheiten), obwohl die Zelle des rechnerischen Umfangs leer ist'

/** Begrenzter Umfang ohne rechnerischen Umfang (etwa ohne Konfidenzniveau) und was die Vorlage darauf aufbaut; `whenEmpty` nennt den leeren rechnerischen Umfang (bei „TE ≤ AE“ steht dort ein Text). */
const onCap: readonly Deviation[] = [
  { cell: 'C35', whenEmpty: ['C29'], template: CAP_TEMPLATE, reason: CAP, kind: 'withoutBasis' },
  { cell: 'C66', whenEmpty: ['C65'], template: CAP_TEMPLATE, reason: CAP, kind: 'withoutBasis' },
  ...['C37', 'C38', 'C44', 'C60', ...rows(37, 38, 40, 44, 45, 46, 60), ...STANDARD, ...FINAL.filter((cell) => cell !== 'C65' && cell !== 'C66'), ...RESULTS].map((cell): Deviation => ({
    cell,
    whenEmpty: ['C29', 'C65'],
    template: 'Wert auf Grundlage eines begrenzten Umfangs, den kein rechnerischer Umfang trägt',
    reason: 'Der Wert baut auf dem begrenzten Umfang auf; ohne rechnerischen Umfang ist er nicht bestimmt.',
    kind: 'withoutBasis',
  })),
]

/** Auf den Summen der Buchwerte (C8) bzw. der Prognose (C9) baut die gesamte Planung auf. */
const onPopulation: readonly Deviation[] = built(
  ['C11', 'C19', 'C21', 'C22', 'C27', 'C29', 'C35', 'C37', 'C38', 'C44', 'C55', 'C56', 'C57', 'C60', 'N4', ...rows(37, 38, 40, 44, 45, 46, 60), ...STANDARD, ...FINAL, ...RESULTS],
  ['C8', 'C9'],
  'Wert auf Grundlage einer Summe der Buchwerte bzw. der Prognose von 0 €, weil keine Schicht einen Buchwert für Zeitraum 1 bzw. eine Prognose für Zeitraum 2 trägt',
)

/** Ohne Umfang je Schicht für Zeitraum 1 (z. B. bei „TE ≤ AE“) ist die Hilfssumme der Zeile 60 in der Vorlage 0; die Standardneuberechnung rechnet damit weiter. */
const onFirstSizes: readonly Deviation[] = built(
  [...STANDARD, ...RESULTS],
  ['C37', 'C60'],
  'Wert auf Grundlage einer Hilfssumme von 0, obwohl keine Schicht einen Umfang für Zeitraum 1 hat (z. B. bei „TE ≤ AE“)',
)

/** Ohne Ist-Buchwert des zweiten Zeitraums (C51) rechnet die Vorlage allein mit dem ersten Zeitraum weiter. */
const onSecondPeriod: readonly Deviation[] = built(
  ['C55', 'C56', 'C57', 'C62', 'C63', 'N4', 'N10', ...FINAL, ...RESULTS],
  ['C51'],
  'Wert allein aus dem ersten Zeitraum, weil die Summe der Ist-Buchwerte des zweiten Zeitraums 0 € ist',
)

/**
 * Hat nicht jede im zweiten Zeitraum belegte Schicht einen Umfang, rechnet die
 * Vorlage mit der Summe der übrigen weiter – bei nicht anwendbarer
 * Standardneuberechnung mit 0, ohne Planumfang mit der Untergrenze 3.
 */
const onSecondSizes: readonly Deviation[] = built(
  ['C71', 'C72', 'N10', ...RESULTS],
  ['C69', 'C78'],
  'Wert auf Grundlage eines Umfangs für Zeitraum 2, den keine Neuberechnung ergeben hat (0 bei nicht anwendbarer Standardneuberechnung, Untergrenze 3 ohne Planumfang)',
)

/** Summe einer Schichtzeile, in der keine Schicht einen Wert trägt: Die Vorlage zeigt 0. */
function emptyTotal(cell: string, cells: readonly number[]): Deviation {
  return {
    cell,
    whenEmpty: rows(...cells),
    template: SIZE_ROWS.includes(cell) ? '0 (Summe über Schichten ohne Wert) bzw. Summe mit der Untergrenze 3 einer Schicht ohne Planumfang' : '0 (Summe über Schichten ohne Wert)',
    reason: 'Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus.',
    kind: 'withoutBasis',
  }
}

/** Summen der Umfänge für Zeitraum 2: Die Untergrenze 3 einer Schicht ohne Planumfang ginge in sie ein. */
const SIZE_ROWS = ['C69', 'C78']

/**
 * Summenzellen mit den Schichtzeilen, deren Werte sie summieren. Hilfszeilen
 * (26, 60, 61, 64, 86) tragen für unbelegte Schichten 0; dort zählen die Zeilen,
 * die eine Schicht belegen, und die Hilfszeile selbst. Die Summen der Zeilen 87
 * und 88 stehen bei den Ergebnissen: Sie sind nur leer, wenn ein Umfang fehlt.
 */
const TOTALS: readonly (readonly [cell: string, cells: readonly number[]])[] = [
  ['C8', [8]], ['C9', [9]], ['C10', [10]], ['C26', [8, 9]], ['C37', [37]], ['C38', [38]], ['C41', [41]], ['C42', [42]], ['C43', [43]], ['C44', [44]], ['C47', [47]], ['C48', [48]],
  ['C51', [51]], ['C52', [52]], ['C60', [8, 60]], ['C61', [51, 61]], ['C64', [8, 51]], ['C68', [68]], ['C69', [69]], ['C70', [70]], ['C75', [75]], ['C76', [76]], ['C77', [77]], ['C78', [78]],
  ['C81', [81]], ['C82', [82]], ['C84', [84]], ['C86', [8, 47, 51, 81]], ['N6', [8, 47, 51, 81]],
]

const UNITS_TEMPLATE = '„✔ ≥ 3“ (Excel wertet die leere Textzelle im Vergleich größer als jede Zahl)'
const UNITS = 'Ohne Einheiten der Zufallsschicht gibt es nichts zu prüfen; ein bestandener Prüfhinweis wäre irreführend.'
const BOUND_TEMPLATE = 'Untergrenze 3 (MAX übergeht den leeren Planumfang der Schicht)'
const BOUND = 'Ohne Planumfang der Schicht gibt es nichts, was die Untergrenze sichern könnte; ein Umfang von 3 sähe wie ein Ergebnis aus.'

/** Je Schichtspalte: Wert der Zeile `cell` ohne Grundlage, weil die Zelle der Zeile `missing` derselben Schicht leer ist. */
const unfoundedPerStratum = (cell: number, missing: number, template: string, reason: string): Deviation[] =>
  STRATA_COLUMNS.map((column) => ({ cell: stratumCell(column, cell), whenEmpty: [stratumCell(column, missing)], template, reason, kind: 'withoutBasis' }))

const strata: readonly Deviation[] = [
  ...unfoundedPerStratum(45, 44, UNITS_TEMPLATE, UNITS),
  ...unfoundedPerStratum(79, 78, UNITS_TEMPLATE, UNITS),
  ...unfoundedPerStratum(69, 38, BOUND_TEMPLATE, BOUND),
  ...[74, 78, 80, 87, 88].flatMap((cell) => unfoundedPerStratum(cell, 69, 'Wert auf Grundlage der Untergrenze 3 als Umfang der Schicht für Zeitraum 2', BOUND)),
]

/** Reihenfolge von der Ursache zur Folge: Der Abgleich nennt je Zelle die erste zutreffende Zeile. */
export const deviations: readonly Deviation[] = [...required, ...onPopulation, ...onSecondPeriod, ...onCap, ...onFirstSizes, ...strata, ...onSecondSizes, ...TOTALS.map(([cell, cells]) => emptyTotal(cell, cells))]
