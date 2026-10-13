/**
 * Methodendefinition Blatt 20_Druck_KOM (Druckfassung für die Kommission). Von Hand
 * aus der Zellbeschreibung der Vorlage aufgebaut, weil das Blatt keine Abschnitte
 * mit Kennbuchstaben hat: Abschnitt S sind die Steuerfelder (Spalten I:J, werden
 * nicht gedruckt), K die Kopfzeile, 1 bis 4 die Abschnitte der Druckseite.
 *
 * Bezeichnungen stammen wörtlich aus der Vorlage: aus Spalte A der Zeile, bei den
 * beiden Wertspalten ergänzt um die Spaltenüberschrift (F10, G10), in der Tabelle
 * der Fehlerfälle aus der Kopfzeile 19 mit der Nummer des Falls. Die Freitexte
 * (A9, A18, A31, A45) tragen als Bezeichnung den Platzhaltertext der Vorlage in
 * eckigen Klammern. Ohne eigene Bezeichnung in der Vorlage sind A6 (hier: Titel
 * aus A5), G6 (hier: „Stand“ aus I4) und A37 (hier: „Würdigung“ wie Blatt 18, B30).
 * Die Seitenaufteilung für die Berichtsansicht steht in `layout.ts`.
 */
import type { FieldDefinition, MethodDefinition } from '../../model/definition'

const EUR = '#,##0.00" €"'
const INT = '#,##0'
const RATE = '0.00%'

/** Titel der Druckseite (A5). */
export const TITLE = 'Vorhabenprüfungen – Stichprobe und Ergebnisse'

/** Platzhaltertexte der Freitextfelder, wörtlich mit den eckigen Klammern der Vorlage. */
export const PLACEHOLDERS = {
  A9: '[Zahlungsanträge mit Nummer und Datum. Abstimmung der Datensätze mit SFC2021. Stichprobeneinheit. Angewandtes Verfahren mit Rechtsgrundlage, Datum der Auswahl, Software und Startzahl. Behandlung der negativen Grundgesamtheit.]',
  A18: '[Stand der Prüfberichte. Anzahl der Feststellungen, davon formell und finanziell. Schwerpunkte der formellen Feststellungen.]',
  A31: '[Hochrechnungsmethode mit Rechtsgrundlage, z. B. Verhältnisschätzung nach Anhang II Nummer 2.1 der Delegierten Verordnung (EU) 2023/67. Behandlung der Pauschale der technischen Hilfe nach Artikel 8 Absatz 5.]',
  A45: '[Bewertung der Ergebnisse, systembedingte oder anomale Fehler, vorgesehene Korrekturen und weiteres Vorgehen.]',
} as const

/** Zeilen der Tabelle der Fehlerfälle (20–27) und ihre Kopfzeile (Zeile 19). */
export const CASE_ROWS = [20, 21, 22, 23, 24, 25, 26, 27] as const
export const CASE_HEADERS = { A: 'VP', B: 'FÖPG', C: 'Buchwert', D: 'Fehler', E: 'Quote', F: 'Art des Fehlers', G: 'Stand' } as const

const freeText = (cell: keyof typeof PLACEHOLDERS, alias: string): FieldDefinition => ({ cell, alias, kind: 'input', type: 'text', label: PLACEHOLDERS[cell] })

/** Felder eines Fehlerfalls: sechs Eingaben und die Fehlerquote des Falls. */
function caseFields(row: number, index: number): FieldDefinition[] {
  const number = index + 1
  return [
    { cell: `A${row}`, alias: `case${number}Operation`, kind: 'input', type: 'text', label: `${CASE_HEADERS.A} ${number}` },
    { cell: `B${row}`, alias: `case${number}Programme`, kind: 'input', type: 'text', label: `${CASE_HEADERS.B} ${number}` },
    { cell: `C${row}`, alias: `case${number}BookValue`, kind: 'input', type: 'amount', format: EUR, label: `${CASE_HEADERS.C} ${number}` },
    { cell: `D${row}`, alias: `case${number}Error`, kind: 'input', type: 'amount', format: EUR, label: `${CASE_HEADERS.D} ${number}` },
    { cell: `E${row}`, alias: `case${number}ErrorRate`, kind: 'formula', type: 'percent', format: '0.0%', label: `${CASE_HEADERS.E} ${number}` },
    { cell: `F${row}`, alias: `case${number}ErrorType`, kind: 'input', type: 'text', label: `${CASE_HEADERS.F} ${number}` },
    { cell: `G${row}`, alias: `case${number}Status`, kind: 'input', type: 'text', label: `${CASE_HEADERS.G} ${number}` },
  ]
}

const controls: FieldDefinition[] = [
  { cell: 'J4', alias: 'asOf', kind: 'input', type: 'text', format: 'dd\\.mm\\.yyyy', label: 'Stand' },
  { cell: 'J5', alias: 'status', kind: 'input', type: 'text', default: 'vorläufig', label: 'Status' },
  { cell: 'J6', alias: 'auditedExpenditure', kind: 'input', type: 'amount', format: EUR, label: 'Geprüfte Ausgaben der Stichprobe' },
  { cell: 'J7', alias: 'article98Amounts', kind: 'input', type: 'amount', format: EUR, label: 'Beträge nach Artikel 98 Absatz 6 (E)' },
  { cell: 'J8', alias: 'financialCorrections', kind: 'input', type: 'amount', format: EUR, label: 'Finanzkorrekturen (H)' },
]

const head: FieldDefinition[] = [
  { cell: 'A6', alias: 'subtitle', kind: 'formula', type: 'text', label: TITLE },
  { cell: 'G6', alias: 'asOfShown', kind: 'formula', type: 'text', format: '"Stand "dd\\.mm\\.yyyy', label: 'Stand' },
]

const population: FieldDefinition[] = [
  freeText('A9', 'populationText'),
  { cell: 'F11', alias: 'claimRecords', kind: 'formula', type: 'integer', format: INT, label: 'Zahlungsanträge insgesamt (SFC2021) – Datensätze' },
  { cell: 'G11', alias: 'claimExpenditure', kind: 'formula', type: 'amount', format: EUR, label: 'Zahlungsanträge insgesamt (SFC2021) – Ausgaben' },
  { cell: 'F12', alias: 'positiveRecords', kind: 'formula', type: 'integer', format: INT, label: 'Positive Grundgesamtheit (Artikel 3 Absatz 4 DelVO) – Datensätze' },
  { cell: 'G12', alias: 'positiveExpenditure', kind: 'formula', type: 'amount', format: EUR, label: 'Positive Grundgesamtheit (Artikel 3 Absatz 4 DelVO) – Ausgaben' },
  { cell: 'F13', alias: 'negativeRecords', kind: 'formula', type: 'integer', format: INT, label: 'Negative Werte und Nullwerte – Datensätze' },
  { cell: 'G13', alias: 'negativeExpenditure', kind: 'formula', type: 'amount', format: EUR, label: 'Negative Werte und Nullwerte – Ausgaben' },
  { cell: 'F14', alias: 'sampleUnits', kind: 'formula', type: 'integer', format: INT, label: 'Stichprobe (Einheiten / geprüfte Ausgaben) – Datensätze' },
  { cell: 'G14', alias: 'sampleExpenditure', kind: 'formula', type: 'amount', format: EUR, label: 'Stichprobe (Einheiten / geprüfte Ausgaben) – Ausgaben' },
  { cell: 'D15', alias: 'samplingMethod', kind: 'formula', type: 'text', label: 'Stichprobenverfahren' },
]

const cases: FieldDefinition[] = [
  freeText('A18', 'resultsText'),
  ...CASE_ROWS.flatMap(caseFields),
  { cell: 'C28', alias: 'caseBookValueSum', kind: 'formula', type: 'amount', format: EUR, label: 'Summe – Buchwert' },
  { cell: 'D28', alias: 'caseErrorSum', kind: 'formula', type: 'amount', format: EUR, label: 'Summe – Fehler' },
  { cell: 'G28', alias: 'preliminaryErrorSum', kind: 'formula', type: 'amount', format: EUR, label: 'davon vorläufig' },
]

const projection: FieldDefinition[] = [
  freeText('A31', 'projectionText'),
  { cell: 'G32', alias: 'totalErrorRate', kind: 'result', type: 'percent', format: RATE, label: 'Gesamtfehlerquote' },
  { cell: 'G33', alias: 'projectedError', kind: 'formula', type: 'amount', format: EUR, label: 'Hochgerechneter Fehler (angepasst nach Anhang III)' },
  { cell: 'G34', alias: 'precision', kind: 'formula', type: 'amount', format: EUR, label: 'Genauigkeit der Stichprobe' },
  { cell: 'G35', alias: 'upperErrorLimit', kind: 'formula', type: 'percent', format: RATE, label: 'Obere Fehlergrenze' },
  { cell: 'G36', alias: 'errorAmountIncludingFlatRate', kind: 'formula', type: 'amount', format: EUR, label: 'Fehlerbetrag einschließlich Pauschale der technischen Hilfe (Artikel 8 Absatz 5 DelVO)' },
  { cell: 'A37', alias: 'assessment', kind: 'formula', type: 'text', label: 'Würdigung' },
]

const residual: FieldDefinition[] = [
  { cell: 'G40', alias: 'article98AmountsShown', kind: 'formula', type: 'amount', format: EUR, label: 'Beträge nach Artikel 98 Absatz 6 VO (EU) 2021/1060 (E)' },
  { cell: 'G41', alias: 'financialCorrectionsShown', kind: 'formula', type: 'amount', format: EUR, label: 'Finanzkorrekturen (H)' },
  { cell: 'G42', alias: 'residualErrorRate', kind: 'result', type: 'percent', format: RATE, label: 'Restfehlerquote nach Finanzkorrekturen' },
  { cell: 'G43', alias: 'extrapolatedCorrection', kind: 'formula', type: 'amount', format: '#,##0.00" €";\\-#,##0.00" €";"nicht erforderlich"', label: 'Hochgerechnete Finanzkorrektur bis zur Wesentlichkeitsschwelle von 2 %' },
  freeText('A45', 'conclusionText'),
]

export const definition: MethodDefinition = {
  sheet: '20_Druck_KOM',
  number: '20',
  title: TITLE,
  shortTitle: 'Bericht',
  legalBasis: '',
  sections: [
    { id: 'S', title: 'Steuerfelder (werden nicht gedruckt)', fields: controls },
    { id: 'K', title: TITLE, fields: head },
    { id: '1', title: 'Grundgesamtheit und Stichprobe', fields: population },
    { id: '2', title: 'Ergebnisse der Vorhabenprüfungen', fields: cases },
    { id: '3', title: 'Hochrechnung und Gesamtfehlerquote', fields: projection },
    { id: '4', title: 'Restfehlerquote und weiteres Vorgehen', fields: residual },
  ],
  summary: {
    primary: { cell: 'G32', label: 'Gesamtfehlerquote', unit: '' },
    rows: [
      { cell: 'G42', label: 'Restfehlerquote nach Finanzkorrekturen', strong: true },
      { cell: 'G35', label: 'Obere Fehlergrenze' },
      { cell: 'G33', label: 'Hochgerechneter Fehler (angepasst nach Anhang III)' },
      { cell: 'G36', label: 'Fehlerbetrag einschließlich TH-Pauschale' },
      { cell: 'G43', label: 'Hochgerechnete Finanzkorrektur bis 2 %' },
    ],
  },
}
