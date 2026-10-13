/**
 * Englische Fassung zu Blatt 20_Druck_KOM (Druckfassung für die Kommission).
 * Vermerk: nicht amtliche Arbeitsübersetzung; maßgeblich ist der deutsche Wortlaut der Vorlage.
 * Fachbegriffe nach der englischen Fassung der Delegierten Verordnung (EU) 2023/67
 * (Art. 2, Art. 3, Art. 8): positive/negative population, sampling method,
 * extrapolated error, sampling precision, upper error limit, total error rate.
 *
 * Die Texte der Seitenaufteilung (`layout.ts`) und die festen Texte des
 * Rechenkerns stehen mit ihrem deutschen Wortlaut als Schlüssel in `values`.
 * Nicht übersetzbar sind mit `SheetTexts` die zusammengesetzte Kopfzeile A6
 * („EFRE-Programm Hessen 2021–2027 · CCI … · Geschäftsjahr …“) und die
 * Eingaben der Prüfbehörde (Status, Stand der Fehlerfälle): Die Vorlage summiert
 * „davon vorläufig“ über den deutschen Wortlaut „vorläufig“ in Spalte G.
 */
import type { FieldTexts, SheetTexts } from '../../model/texts'
import { NOT_CALCULATED } from './compute'
import { CASE_ROWS, TITLE } from './definition'
import { REPORT_LAYOUT } from './layout'

const TITLE_EN = 'Audits of operations – sample and results'

/** Kopfzeile der Tabelle der Fehlerfälle; „FÖPG“ ist ein Kürzel der Vorlage und bleibt stehen. */
const CASE_HEADERS_EN = { A: 'Audit', B: 'FÖPG', C: 'Book value', D: 'Error', E: 'Rate', F: 'Type of error', G: 'Status' } as const

/** Bezeichnungen der Felder eines Fehlerfalls: Spaltenüberschrift mit der Nummer des Falls. */
const caseFields: Record<string, FieldTexts> = Object.fromEntries(
  CASE_ROWS.flatMap((row, index) => Object.entries(CASE_HEADERS_EN).map(([column, header]) => [`${column}${row}`, { label: `${header} ${index + 1}` }])),
)

/** Zeilen der Tabelle „Grundgesamtheit und Stichprobe“: Bezeichnung der Zeile, in den Feldern ergänzt um die Spalte. */
const POPULATION_ROWS = {
  11: 'Payment applications in total (SFC2021)',
  12: 'Positive population (Article 3(4) DR)',
  13: 'Negative values and null values',
  14: 'Sample (units / audited expenditure)',
} as const

const populationFields: Record<string, FieldTexts> = Object.fromEntries(
  Object.entries(POPULATION_ROWS).flatMap(([row, label]) => [
    [`F${row}`, { label: `${label} – data records` }],
    [`G${row}`, { label: `${label} – expenditure` }],
  ]),
)

const FIGURES = {
  totalErrorRate: 'Total error rate',
  extrapolatedError: 'Extrapolated error (adjusted in accordance with Annex III)',
  precision: 'Sampling precision',
  upperLimit: 'Upper error limit',
  errorAmount: 'Amount of error including the flat rate for technical assistance (Article 8(5) DR)',
  article98: 'Amounts under Article 98(6) of Regulation (EU) 2021/1060 (E)',
  corrections: 'Financial corrections (H)',
  residualRate: 'Residual error rate after financial corrections',
  extrapolatedCorrection: 'Extrapolated financial correction down to the materiality threshold of 2 %',
} as const

/** Methodennamen aus der Ergebnisübersicht der Methodenblätter (Zeile „Stichprobenverfahren“, D15). */
const METHODS: Readonly<Record<string, string>> = {
  'MUS-Standardansatz, 1 Zeitraum': 'MUS standard approach, 1 period',
  'MUS-Standardansatz, 1 Zeitraum, geschichtet': 'MUS standard approach, 1 period, stratified',
  'MUS-Standardansatz, 2 Zeiträume': 'MUS standard approach, 2 periods',
  'MUS-Standardansatz, 2 Zeiträume, geschichtet': 'MUS standard approach, 2 periods, stratified',
  'MUS-Standardansatz, 3 Zeiträume': 'MUS standard approach, 3 periods',
  'Einfaches Zufallsstichprobenverfahren, 1 Zeitraum': 'Simple random sampling, 1 period',
  'Einfaches Zufallsstichprobenverfahren, 1 Zeitraum, geschichtet': 'Simple random sampling, 1 period, stratified',
  'Einfaches Zufallsstichprobenverfahren, 2 Zeiträume': 'Simple random sampling, 2 periods',
  'Einfaches Zufallsstichprobenverfahren, 2 Zeiträume, geschichtet': 'Simple random sampling, 2 periods, stratified',
  'Einfaches Zufallsstichprobenverfahren, 3 Zeiträume': 'Simple random sampling, 3 periods',
  'Nichtstatistisch, gleiche Wahrscheinlichkeit': 'Non-statistical, equal probability',
  'Nichtstatistisch, gleiche Wahrscheinlichkeit, geschichtet': 'Non-statistical, equal probability, stratified',
  'Nichtstatistisch, PPS': 'Non-statistical, PPS',
  'Nichtstatistisch, PPS, geschichtet': 'Non-statistical, PPS, stratified',
}

export const en: SheetTexts = {
  title: TITLE_EN,
  shortTitle: 'Report',
  sections: {
    S: { title: 'Control fields (not printed)' },
    K: { title: TITLE_EN },
    1: { title: 'Population and sample' },
    2: { title: 'Results of the audits of operations' },
    3: { title: 'Extrapolation and total error rate' },
    4: { title: 'Residual error rate and further steps' },
  },
  fields: {
    J4: { label: 'As at' },
    J5: { label: 'Status' },
    J6: { label: 'Audited expenditure of the sample' },
    J7: { label: 'Amounts under Article 98(6) (E)' },
    J8: { label: FIGURES.corrections },
    A6: { label: TITLE_EN },
    G6: { label: 'As at' },
    A9: {
      label:
        '[Payment applications with number and date. Reconciliation of the data records with SFC2021. Sampling unit. Sampling method applied with legal basis, date of selection, software and random seed. Treatment of the negative population.]',
    },
    ...populationFields,
    D15: { label: 'Sampling method' },
    A18: { label: '[Status of the audit reports. Number of findings, of which formal and financial. Main subjects of the formal findings.]' },
    ...caseFields,
    C28: { label: 'Total – book value' },
    D28: { label: 'Total – error' },
    G28: { label: 'of which preliminary' },
    A31: {
      label:
        '[Extrapolation method with legal basis, e.g. ratio estimation under point 2.1 of Annex II to Delegated Regulation (EU) 2023/67. Treatment of the flat rate for technical assistance under Article 8(5).]',
    },
    G32: { label: FIGURES.totalErrorRate },
    G33: { label: FIGURES.extrapolatedError },
    G34: { label: FIGURES.precision },
    G35: { label: FIGURES.upperLimit },
    G36: { label: FIGURES.errorAmount },
    A37: { label: 'Assessment' },
    G40: { label: FIGURES.article98 },
    G41: { label: FIGURES.corrections },
    G42: { label: FIGURES.residualRate },
    G43: { label: FIGURES.extrapolatedCorrection },
    A45: { label: '[Assessment of the results, systemic or anomalous errors, corrections envisaged and further steps.]' },
  },
  summary: {
    primary: FIGURES.totalErrorRate,
    unit: '',
    rows: {
      G42: FIGURES.residualRate,
      G35: FIGURES.upperLimit,
      G33: FIGURES.extrapolatedError,
      G36: 'Amount of error including the TA flat rate',
      G43: 'Extrapolated financial correction down to 2 %',
    },
  },
  values: {
    ...METHODS,
    // Seitenaufteilung (`layout.ts`)
    'Kofinanziert von der': 'Co-funded by the',
    'Europäischen Union': 'European Union',
    [TITLE]: TITLE_EN,
    [REPORT_LAYOUT.controls.title]: 'Control fields (not printed)',
    [REPORT_LAYOUT.controls.note]:
      'The figures come from sheet 02 and from the method sheet chosen in sheet 18. The residual error rate follows the logic of the Commission template (F = A − E, G = D × F, I = F − H, J = G − H, K = J / I).',
    '1. Grundgesamtheit und Stichprobe': '1. Population and sample',
    '2. Ergebnisse der Vorhabenprüfungen': '2. Results of the audits of operations',
    '3. Hochrechnung und Gesamtfehlerquote': '3. Extrapolation and total error rate',
    '4. Restfehlerquote und weiteres Vorgehen': '4. Residual error rate and further steps',
    Datensätze: 'Data records',
    Ausgaben: 'Expenditure',
    'Zahlungsanträge insgesamt (SFC2021)': POPULATION_ROWS[11],
    'Positive Grundgesamtheit (Artikel 3 Absatz 4 DelVO)': POPULATION_ROWS[12],
    'Negative Werte und Nullwerte': POPULATION_ROWS[13],
    'Stichprobe (Einheiten / geprüfte Ausgaben)': POPULATION_ROWS[14],
    Stichprobenverfahren: 'Sampling method',
    VP: CASE_HEADERS_EN.A,
    Buchwert: CASE_HEADERS_EN.C,
    Fehler: CASE_HEADERS_EN.D,
    Quote: CASE_HEADERS_EN.E,
    'Art des Fehlers': CASE_HEADERS_EN.F,
    Stand: CASE_HEADERS_EN.G,
    Summe: 'Total',
    Gesamtfehlerquote: FIGURES.totalErrorRate,
    'Hochgerechneter Fehler (angepasst nach Anhang III)': FIGURES.extrapolatedError,
    'Genauigkeit der Stichprobe': FIGURES.precision,
    'Obere Fehlergrenze': FIGURES.upperLimit,
    'Fehlerbetrag einschließlich Pauschale der technischen Hilfe (Artikel 8 Absatz 5 DelVO)': FIGURES.errorAmount,
    'Beträge nach Artikel 98 Absatz 6 VO (EU) 2021/1060 (E)': FIGURES.article98,
    'Finanzkorrekturen (H)': FIGURES.corrections,
    'Restfehlerquote nach Finanzkorrekturen': FIGURES.residualRate,
    'Hochgerechnete Finanzkorrektur bis zur Wesentlichkeitsschwelle von 2 %': FIGURES.extrapolatedCorrection,
    [REPORT_LAYOUT.footer]: 'ERDF audit authority, Unit Z 6, HMWVW, Wiesbaden',
    // Rechenkern und Zahlenformate
    'Stand ': 'As at ',
    'davon vorläufig: ': 'of which preliminary: ',
    [NOT_CALCULATED]: 'not calculated',
    'nicht erforderlich': 'not required',
    'Die Gesamtfehlerquote liegt über der Wesentlichkeitsschwelle.': 'The total error rate is above the materiality threshold.',
    'Die Gesamtfehlerquote liegt unter der Wesentlichkeitsschwelle.': 'The total error rate is below the materiality threshold.',
  },
  webHints: {
    'fixed-programme':
      'As in the template, header and footer name the “EFRE-Programm Hessen 2021–2027” (ERDF programme Hessen 2021–2027) and the audit authority in Wiesbaden as fixed text; for other programmes the template has to be adapted',
    'case-book-value-zero': 'Error case with book value 0: the rate cannot be determined (the template shows an error value there)',
    'residual-rate-undefined': 'The residual error rate cannot be determined: amounts under Article 98(6) and financial corrections together reach the extrapolation basis',
  },
}
