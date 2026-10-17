/**
 * Methodendefinition Blatt X2_DiffSch_2017 (Altvorlage von 2017, Template 10:
 * Differenzschätzung). Bezeichnungen und Abschnitte stehen wörtlich – englisch
 * und mit den Schreibweisen der Vorlage – in den Spalten A und B.
 *
 * **Ableitung der Eingaben.** Eingaben sind die leeren Zellen der Spalte C,
 * auf die Formeln verweisen; die Bezeichnung steht in der Nachbarzelle der
 * Spalte B:
 *
 * | Zelle | gelesen von | Bezeichnung (Spalte B) |
 * |---|---|---|
 * | C1 | C8, C10, C17, C18, C20, C21, C23 | Total book value … |
 * | C3 | C11, C16, C19 | Size of population (sampling units) |
 * | C4 | C11 | Standard deviation of errors (for sample size determination …) |
 * | C5 | C6 | Confidence level |
 * | C7 | C8 | Expected error rate |
 * | C13 | C14 | Sample total error (sum of the errors in the sample) |
 * | C15 | C19 | Sample standard deviation of errors |
 *
 * Leer und beschriftet, aber von keiner Formel gelesen (Angaben zum Vorgang):
 * C2 (Sampling unit), C12 (Expenditure of the sample). C9 ist der feste Wert
 * 2 %. Das Konfidenzniveau fragt die Vorlage in fünf Stufen ab (60, 70, 80,
 * 90, 95 %). Abschnitte haben keine Kennbuchstaben; A–D zählen sie durch.
 */
import type { FieldDefinition, MethodDefinition } from '../../model/definition'
import { LEGACY_LEGAL_BASIS, LEGACY_NOTICE_LABEL } from '../shared/legacy'

const EUR = '#,##0" €"'
const INT = '#,##0'
const RATE = '0.00%'

const population: FieldDefinition[] = [
  { cell: 'E1', alias: 'legacyNotice', kind: 'formula', type: 'check', label: LEGACY_NOTICE_LABEL },
  { cell: 'C1', alias: 'bookValue', kind: 'input', type: 'amount', format: EUR, label: 'Total book value (declared expenditure in the reference period) - positive population' },
  { cell: 'C2', alias: 'samplingUnit', kind: 'input', type: 'text', label: 'Sampling unit' },
  { cell: 'C3', alias: 'populationSize', kind: 'input', type: 'integer', format: INT, label: 'Size of population (sampling units)' },
]

const size: FieldDefinition[] = [
  {
    cell: 'C4',
    alias: 'anticipatedDeviation',
    kind: 'input',
    type: 'amount',
    format: EUR,
    label: 'Standard deviation of errors (for sample size determination; possible based on historial data or pilot sample)',
  },
  { cell: 'C5', alias: 'confidenceLevel', kind: 'input', type: 'choice', format: '0%', list: 'confidence', label: 'Confidence level' },
  { cell: 'C6', alias: 'zCoefficient', kind: 'formula', type: 'decimal', format: '#,##0.000', label: 'z' },
  { cell: 'C7', alias: 'anticipatedErrorRate', kind: 'input', type: 'percent', format: RATE, label: 'Expected error rate' },
  { cell: 'C8', alias: 'anticipatedError', kind: 'formula', type: 'amount', format: EUR, label: 'Antecipated error', formula: 'AE = expected error rate × BV' },
  { cell: 'C9', alias: 'materiality', kind: 'formula', type: 'percent', format: '0%', label: 'Materiality level (maximum 2%; set by the regulation)' },
  { cell: 'C10', alias: 'tolerableError', kind: 'formula', type: 'amount', format: EUR, label: 'Tolerable error (TE)', formula: 'TE = materiality level × BV' },
  { cell: 'C11', alias: 'sampleSize', kind: 'formula', type: 'integer', format: INT, label: 'Planned sample size (n)', formula: 'n = (N · z · σ_e / (TE − AE))², mindestens 30' },
]

const findings: FieldDefinition[] = [
  { cell: 'C12', alias: 'sampleExpenditure', kind: 'input', type: 'amount', format: EUR, label: 'Expenditure of the sample' },
  { cell: 'C13', alias: 'sampleError', kind: 'input', type: 'amount', format: EUR, label: 'Sample total error (sum of the errors in the sample)' },
  { cell: 'C14', alias: 'sampleAverageError', kind: 'formula', type: 'amount', format: EUR, label: 'Sample average error', formula: 'sample total error / n' },
  { cell: 'C15', alias: 'sampleDeviation', kind: 'input', type: 'amount', format: EUR, label: 'Sample standard deviation of errors' },
]

const projection: FieldDefinition[] = [
  { cell: 'C16', alias: 'projectedError', kind: 'formula', type: 'amount', format: EUR, label: 'Projected error', formula: 'EE = N · sample average error' },
  { cell: 'C17', alias: 'projectedErrorRate', kind: 'formula', type: 'percent', format: RATE, label: 'Projected error rate' },
  { cell: 'C18', alias: 'correctedBookValue', kind: 'formula', type: 'amount', format: EUR, label: 'Corrected Book Value (CBV)', formula: 'CBV = BV − EE' },
  { cell: 'C19', alias: 'precision', kind: 'formula', type: 'amount', format: EUR, label: 'Precision', formula: 'SE = N · z · s_e / √n' },
  { cell: 'C20', alias: 'relativePrecision', kind: 'formula', type: 'percent', format: RATE, label: 'Relative precision (% of the total book value of the population)' },
  { cell: 'C21', alias: 'upperErrorLimitRate', kind: 'formula', type: 'percent', format: RATE, label: 'Upper limit of error rate', formula: '(EE + SE) / BV' },
  { cell: 'C22', alias: 'lowerCorrectedBookValue', kind: 'formula', type: 'amount', format: EUR, label: 'Lower limit for the corrected book value (LL=CBV-SE)' },
  { cell: 'C23', alias: 'bookValueLessTolerable', kind: 'formula', type: 'amount', format: EUR, label: 'Book Value - Tolerable error (BV-TE)' },
]

export const definition: MethodDefinition = {
  sheet: 'X2_DiffSch_2017',
  number: 'X2',
  title: 'Differenzschätzung (Template 10 der Vorlage von 2017, unverändert)',
  shortTitle: 'Differenzschätzung (2017)',
  legalBasis: LEGACY_LEGAL_BASIS,
  sections: [
    { id: 'A', title: 'Population characteristics', fields: population },
    { id: 'B', title: 'Sample size determination', fields: size },
    { id: 'C', title: 'Sample results', fields: findings },
    { id: 'D', title: 'Projection and precision', fields: projection },
  ],
  summary: {
    primary: { cell: 'C11', label: 'Planned sample size (n)', unit: 'Einheiten' },
    rows: [
      { cell: 'C16', label: 'Projected error' },
      { cell: 'C19', label: 'Precision' },
      { cell: 'C22', label: 'Lower limit for the corrected book value (LL=CBV-SE)' },
      { cell: 'C23', label: 'Book Value - Tolerable error (BV-TE)' },
      { cell: 'C17', label: 'Projected error rate', strong: true },
      { cell: 'C21', label: 'Upper limit of error rate', strong: true },
    ],
    gauge: { threshold: 'C9', rate: 'C17', upper: 'C21', rateLabel: 'Projected error rate', upperLabel: 'Upper limit of error rate' },
  },
}
