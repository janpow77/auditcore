/**
 * Methodendefinition Blatt X4_DiffSch_2Z_2017 (Altvorlage von 2017, Template
 * 12: Differenzschätzung, zwei Zeiträume). Bezeichnungen und Abschnitte stehen
 * wörtlich – englisch und mit den Schreibweisen der Vorlage – in den Spalten A
 * und B. Jeder Zeitraum hat eigene Zellen und eigene Abschnitte.
 *
 * **Ableitung der Eingaben.** Eingaben sind die leeren Zellen der Spalte C,
 * auf die Formeln verweisen; die Bezeichnung steht in der Nachbarzelle der
 * Spalte B:
 *
 * | Zelle | gelesen von | Bezeichnung (Spalte B) |
 * |---|---|---|
 * | C3 | C1, C24 | Book value at the end of period 1 (declared expenditure) |
 * | C4 | C1 | Predicted book value for period 2 |
 * | C5 | C9, C16, C17, C31, C36, C39 | Size of population at the end of period 1 … |
 * | C6 | C9, C16, C17 | Predicted size of population for period 2 … |
 * | C7 | C9, C16 | Standard deviation of errors of period 1 … |
 * | C8 | C9, C16 | Predicted standard deviation of errors of period 2 … |
 * | C10 | C11 | Confidence level |
 * | C12 | C13 | Expected error rate |
 * | C21 | C36 | Sample total error - first period |
 * | C22 | C31, C39 | Sample standard deviation of errors - first semester |
 * | C23 | C31 | Standard deviation of errors of period 2 … |
 * | C25 | C24 | Book value for period 2 (declared expenditure) |
 * | C26 | C31, C36, C39 | Size of population for period 2 … |
 * | C27 | C28 | Expected error rate |
 * | C34 | C36 | Sample total error - second period |
 * | C35 | C39 | Sample standard deviation of errors - second period |
 *
 * Leer und beschriftet, aber von keiner Formel gelesen (Angaben zum Vorgang):
 * C2 (Sampling unit), C20 und C33 (Sample book value je Zeitraum). C14 und C29
 * sind feste Werte (2 %). Das Konfidenzniveau fragt die Vorlage in fünf Stufen
 * ab (60, 70, 80, 90, 95 %). Die Zwischenüberschriften B19 („Sample results -
 * first period“) und B32 („Sample results - second period“) sind keine Felder.
 * Die Fußnote A45 steht als Erläuterung an den drei Zeilen mit Sternchen.
 * Abschnitte haben keine Kennbuchstaben; A–E zählen sie durch.
 */
import type { FieldDefinition, MethodDefinition } from '../../model/definition'
import { LEGACY_LEGAL_BASIS, LEGACY_NOTICE_LABEL } from '../shared/legacy'

const EUR = '#,##0" €"'
const INT = '#,##0'
const RATE = '0.00%'
/** Fußnote A45 der Vorlage zu den Zeilen mit Sternchen. */
const MINIMUM = 'Minimum of 3 sampling units'
const HISTORICAL = '(for sample size determination; possible based on historial data or pilot sample)'

const population: FieldDefinition[] = [
  { cell: 'F1', alias: 'legacyNotice', kind: 'formula', type: 'check', label: LEGACY_NOTICE_LABEL },
  { cell: 'C1', alias: 'predictedBookValue', kind: 'formula', type: 'amount', format: EUR, label: 'Predicted total book value (declared expenditure in the reference period) - positive population' },
  { cell: 'C2', alias: 'samplingUnit', kind: 'input', type: 'text', label: 'Sampling unit' },
  { cell: 'C3', alias: 'bookValuePeriod1', kind: 'input', type: 'amount', format: EUR, label: 'Book value at the end of period 1 (declared expenditure)' },
  { cell: 'C4', alias: 'predictedBookValuePeriod2', kind: 'input', type: 'amount', format: EUR, label: 'Predicted book value for period 2' },
  { cell: 'C5', alias: 'populationSizePeriod1', kind: 'input', type: 'integer', format: INT, label: 'Size of population at the end of period 1 (number of sampling units)' },
  { cell: 'C6', alias: 'predictedPopulationSizePeriod2', kind: 'input', type: 'integer', format: INT, label: 'Predicted size of population for period 2 (number of sampling units)' },
]

const firstSize: FieldDefinition[] = [
  { cell: 'C7', alias: 'anticipatedDeviationPeriod1', kind: 'input', type: 'amount', label: `Standard deviation of errors of period 1 ${HISTORICAL}` },
  { cell: 'C8', alias: 'predictedDeviationPeriod2', kind: 'input', type: 'amount', label: `Predicted standard deviation of errors of period 2 ${HISTORICAL}` },
  { cell: 'C9', alias: 'weightedVariance', kind: 'formula', type: 'amount', format: EUR, label: 'Weighted average of the variances of the errors' },
  { cell: 'C10', alias: 'confidenceLevel', kind: 'input', type: 'choice', format: '0%', list: 'confidence', label: 'Confidence level' },
  { cell: 'C11', alias: 'zCoefficient', kind: 'formula', type: 'decimal', format: '#,##0.000', label: 'z' },
  { cell: 'C12', alias: 'anticipatedErrorRate', kind: 'input', type: 'percent', format: RATE, label: 'Expected error rate' },
  { cell: 'C13', alias: 'anticipatedError', kind: 'formula', type: 'amount', format: EUR, label: 'Antecipated error' },
  { cell: 'C14', alias: 'materiality', kind: 'formula', type: 'percent', format: RATE, label: 'Materiality level (maximum 2%; set by the regulation)' },
  { cell: 'C15', alias: 'tolerableError', kind: 'formula', type: 'amount', format: EUR, label: 'Tolerable error (TE)' },
  { cell: 'C16', alias: 'sampleSize', kind: 'formula', type: 'integer', format: INT, label: 'Planned sample size (n)', formula: 'n = ((N₁ + N₂) · z · σ_w / (TE − AE))²' },
  { cell: 'C17', alias: 'sampleSizePeriod1', kind: 'formula', type: 'integer', format: INT, label: 'Sample size - first period*', formula: 'n₁ = N₁ / (N₁ + N₂) · n', hint: MINIMUM },
  { cell: 'C18', alias: 'sampleSizePeriod2', kind: 'formula', type: 'integer', format: INT, label: 'Sample size - second period*', formula: 'n₂ = n − n₁', hint: MINIMUM },
]

const firstResults: FieldDefinition[] = [
  { cell: 'C20', alias: 'sampleBookValuePeriod1', kind: 'input', type: 'amount', format: EUR, label: 'Sample book value - first period' },
  { cell: 'C21', alias: 'sampleErrorPeriod1', kind: 'input', type: 'amount', format: EUR, label: 'Sample total error - first period' },
  { cell: 'C22', alias: 'sampleDeviationPeriod1', kind: 'input', type: 'amount', format: EUR, label: 'Sample standard deviation of errors - first semester' },
]

const secondSize: FieldDefinition[] = [
  { cell: 'C23', alias: 'anticipatedDeviationPeriod2', kind: 'input', type: 'amount', format: EUR, label: `Standard deviation of errors of period 2 ${HISTORICAL}` },
  { cell: 'C24', alias: 'bookValue', kind: 'formula', type: 'amount', format: EUR, label: 'Total book value (declared expenditure in the reference year) - positive population' },
  { cell: 'C25', alias: 'bookValuePeriod2', kind: 'input', type: 'amount', format: EUR, label: 'Book value for period 2 (declared expenditure)' },
  { cell: 'C26', alias: 'populationSizePeriod2', kind: 'input', type: 'integer', format: INT, label: 'Size of population for period 2 (number of sampling units)' },
  { cell: 'C27', alias: 'anticipatedErrorRatePeriod2', kind: 'input', type: 'percent', format: RATE, label: 'Expected error rate' },
  { cell: 'C28', alias: 'anticipatedErrorPeriod2', kind: 'formula', type: 'amount', format: EUR, label: 'Antecipated error' },
  { cell: 'C29', alias: 'materialityPeriod2', kind: 'formula', type: 'percent', format: RATE, label: 'Materiality level (maximum 2%)' },
  { cell: 'C30', alias: 'tolerableErrorPeriod2', kind: 'formula', type: 'amount', format: EUR, label: 'Tolerable error (TE)' },
  {
    cell: 'C31',
    alias: 'recalculatedSampleSizePeriod2',
    kind: 'formula',
    type: 'integer',
    format: INT,
    label: 'Recalculated sample size - period 2*',
    formula: 'n₂ = (z · N₂ · σ₂)² / ((TE − AE)² − z² · N₁² / n₁ · s₁²)',
    hint: MINIMUM,
  },
]

const projection: FieldDefinition[] = [
  { cell: 'C33', alias: 'sampleBookValuePeriod2', kind: 'input', type: 'amount', format: EUR, label: 'Sample book value -  second period' },
  { cell: 'C34', alias: 'sampleErrorPeriod2', kind: 'input', type: 'amount', format: EUR, label: 'Sample total error - second period' },
  { cell: 'C35', alias: 'sampleDeviationPeriod2', kind: 'input', type: 'amount', format: EUR, label: 'Sample standard deviation of errors - second period' },
  { cell: 'C36', alias: 'projectedError', kind: 'formula', type: 'amount', format: EUR, label: 'Projected error', formula: 'EE = E₁ / n₁ · N₁ + E₂ / n₂ · N₂' },
  { cell: 'C37', alias: 'projectedErrorRate', kind: 'formula', type: 'percent', format: RATE, label: 'Projected error rate' },
  { cell: 'C38', alias: 'correctedBookValue', kind: 'formula', type: 'amount', format: EUR, label: 'Corrected Book Value (CBV)', formula: 'CBV = BV − EE' },
  { cell: 'C39', alias: 'precision', kind: 'formula', type: 'amount', format: EUR, label: 'Precision', formula: 'SE = z · √(N₁² · s₁² / n₁ + N₂² · s₂² / n₂)' },
  { cell: 'C40', alias: 'relativePrecision', kind: 'formula', type: 'percent', format: RATE, label: 'Relative precision (% of the total book value of the population)' },
  { cell: 'C41', alias: 'upperErrorLimitRate', kind: 'formula', type: 'percent', format: RATE, label: 'Upper limit of error rate', formula: '(EE + SE) / BV' },
  { cell: 'C42', alias: 'lowerCorrectedBookValue', kind: 'formula', type: 'amount', format: EUR, label: 'Lower limit for the corrected book value (LL=CBV-SE)' },
  { cell: 'C43', alias: 'bookValueLessTolerable', kind: 'formula', type: 'amount', format: EUR, label: 'Book Value - Tolerable error (BV-TE)' },
]

export const definition: MethodDefinition = {
  sheet: 'X4_DiffSch_2Z_2017',
  number: 'X4',
  title: 'Differenzschätzung, zwei Zeiträume (Template 12 der Vorlage von 2017, unverändert)',
  shortTitle: 'Differenzschätzung, 2 Zeiträume (2017)',
  legalBasis: LEGACY_LEGAL_BASIS,
  sections: [
    { id: 'A', title: 'Population characteristics', fields: population },
    { id: 'B', title: 'Sample size determination (period 1)', fields: firstSize },
    { id: 'C', title: 'Sample results at the end of period 1', fields: firstResults },
    { id: 'D', title: 'Sample size determination (period 2)', fields: secondSize },
    { id: 'E', title: 'Projection and precision', fields: projection },
  ],
  summary: {
    primary: { cell: 'C16', label: 'Planned sample size (n)', unit: 'Einheiten' },
    rows: [
      { cell: 'C17', label: 'Sample size - first period*' },
      { cell: 'C18', label: 'Sample size - second period*' },
      { cell: 'C31', label: 'Recalculated sample size - period 2*' },
      { cell: 'C36', label: 'Projected error' },
      { cell: 'C39', label: 'Precision' },
      { cell: 'C37', label: 'Projected error rate', strong: true },
      { cell: 'C41', label: 'Upper limit of error rate', strong: true },
    ],
    gauge: { threshold: 'C29', rate: 'C37', upper: 'C41', rateLabel: 'Projected error rate', upperLabel: 'Upper limit of error rate' },
  },
}
