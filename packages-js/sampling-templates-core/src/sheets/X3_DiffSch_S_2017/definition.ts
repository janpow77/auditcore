/**
 * Methodendefinition Blatt X3_DiffSch_S_2017 (Altvorlage von 2017, Template
 * 11: Differenzschätzung, geschichtet). Bezeichnungen und Abschnitte stehen
 * wörtlich – englisch und mit den Schreibweisen der Vorlage – in den Spalten A
 * und B.
 *
 * **Abweichender Aufbau.** Anders als in den Blättern 04–16 stehen die
 * Schichten hier in den Spalten E–K (E–I „1–5“, J „…“, K „k“), die Werte des
 * Blatts in Spalte D. Die Schichtzeilen tragen deshalb `LEGACY_STRATA` statt
 * `STRATA_COLUMNS`; eine Summenzelle je Zeile gibt es nicht (die Summen D1 und
 * D3 sind eigene Zeilen der Vorlage).
 *
 * **Ableitung der Eingaben.** Eingaben sind die leeren Zellen, auf die Formeln
 * verweisen; die Bezeichnung steht in Spalte B derselben Zeile:
 *
 * | Zellen | gelesen von | Bezeichnung (Spalte B) |
 * |---|---|---|
 * | E6–K6 | D1 | Book value |
 * | E7–K7 | D3, D4, D26, Zeilen 17 und 22 | Size of stratum (number of sampling units) |
 * | E8–K8 | D4 | Standard deviation of error (for sample size determination …) |
 * | D9 | D10 | Confidence level |
 * | D11 | D12 | Expected error rate |
 * | E19–K19 | Zeile 20 | Sample total error (sum of the errors in the sample) |
 * | E21–K21 | D26 | Sample standard deviation of errors |
 *
 * Leer und beschriftet, aber von keiner Formel gelesen (Angaben zum Vorgang):
 * D2 (Sampling unit), E18–K18 (Total sample expenditure). D13 ist der feste
 * Wert 2 %. Die Zeilen 5 und 16 („Stratum“) sind Spaltenköpfe. Die Zellen der
 * Zeile 17 tragen in der Vorlage Formeln, die die Prüfbehörde laut Fußnote
 * überschreiben darf; die Webfassung führt sie als Formel. Die Fußnoten A32
 * und A33 stehen als Erläuterung an Zeile 17. Die Zeilen 1–3 haben in Spalte A
 * keine Abschnittsbezeichnung; sie stehen hier im ersten Abschnitt. Abschnitte
 * haben keine Kennbuchstaben; A–C zählen sie durch.
 */
import type { FieldDefinition, MethodDefinition } from '../../model/definition'
import { LEGACY_LEGAL_BASIS, LEGACY_NOTICE_LABEL, LEGACY_STRATA } from '../shared/legacy'

const EUR = '#,##0" €"'
const INT = '#,##0'
const RATE = '0.00%'
const columns = LEGACY_STRATA
/** Fußnoten A32 und A33 der Vorlage zu Zeile 17. */
const ROUNDING =
  'The template rounds up both the global sample size as well as sample sizes for individual strata. For that reason the sum of sample sizes for individual strata could be larger than the global sample size. Please note that it is not obligatory to round up all sample sizes for individual strata, provided that the general sample size is rounded up. In case the AA has decided not to round up all sample sizes for individual strata, the formulas from the relevant cells of columns E-K should be replaced manually by the rounded down numbers. Minimum of 3 sampling units per stratum'

const population: FieldDefinition[] = [
  { cell: 'M1', alias: 'legacyNotice', kind: 'formula', type: 'check', label: LEGACY_NOTICE_LABEL },
  { cell: 'D1', alias: 'bookValue', kind: 'formula', type: 'amount', format: EUR, label: 'Total book value (declared expenditure in the reference period) - positive population' },
  { cell: 'D2', alias: 'samplingUnit', kind: 'input', type: 'text', label: 'Sampling unit' },
  { cell: 'D3', alias: 'populationSize', kind: 'formula', type: 'integer', format: INT, label: 'Size of population (number of sampling units)' },
  { cell: 'D4', alias: 'weightedVariance', kind: 'formula', type: 'decimal', format: '#,##0.00', label: 'Weighted sum of variances of the error (section 6.2.2.2 of the guidance)' },
  { cell: 'E6', alias: 'stratumBookValue', kind: 'input', type: 'amount', format: EUR, columns, label: 'Book value' },
  { cell: 'E7', alias: 'stratumSize', kind: 'input', type: 'integer', format: INT, columns, label: 'Size of stratum (number of sampling units)' },
]

const size: FieldDefinition[] = [
  { cell: 'E8', alias: 'stratumAnticipatedDeviation', kind: 'input', type: 'amount', columns, label: 'Standard deviation of error (for sample size determination; possible based on historical data or pilot sample)' },
  { cell: 'D9', alias: 'confidenceLevel', kind: 'input', type: 'choice', format: '0%', list: 'confidence', label: 'Confidence level' },
  { cell: 'D10', alias: 'zCoefficient', kind: 'formula', type: 'decimal', format: '#,##0.000', label: 'z' },
  { cell: 'D11', alias: 'anticipatedErrorRate', kind: 'input', type: 'percent', format: RATE, label: 'Expected error rate' },
  { cell: 'D12', alias: 'anticipatedError', kind: 'formula', type: 'amount', format: EUR, label: 'Antecipated error' },
  { cell: 'D13', alias: 'materiality', kind: 'formula', type: 'percent', format: RATE, label: 'Materiality level (maximum 2%; set by the regulation)' },
  { cell: 'D14', alias: 'tolerableError', kind: 'formula', type: 'amount', format: EUR, label: 'Tolerable error (TE)' },
  { cell: 'D15', alias: 'sampleSize', kind: 'formula', type: 'integer', format: INT, label: 'Planned sample size (n)', formula: 'n = (N · z · σ_w / (TE − AE))², mindestens 30' },
  { cell: 'E17', alias: 'stratumSampleSize', kind: 'formula', type: 'integer', columns, label: 'Planned sample size (n_h=n*(N_h/N))*', hint: ROUNDING },
  { cell: 'E18', alias: 'stratumSampleExpenditure', kind: 'input', type: 'amount', columns, label: 'Total sample expenditure (sum of the book values of sampling units in the sample)' },
  { cell: 'E19', alias: 'stratumSampleError', kind: 'input', type: 'amount', format: EUR, columns, label: 'Sample total error (sum of the errors in the sample)' },
  { cell: 'E20', alias: 'stratumAverageError', kind: 'formula', type: 'amount', format: EUR, columns, label: 'Sample average error' },
  { cell: 'E21', alias: 'stratumSampleDeviation', kind: 'input', type: 'amount', columns, label: 'Sample standard deviation of errors' },
  { cell: 'E22', alias: 'stratumProjectedError', kind: 'formula', type: 'amount', format: EUR, columns, label: 'Projected error by stratum' },
]

const results: FieldDefinition[] = [
  { cell: 'D23', alias: 'projectedError', kind: 'formula', type: 'amount', format: EUR, label: 'Projected error' },
  { cell: 'D24', alias: 'projectedErrorRate', kind: 'formula', type: 'percent', format: RATE, label: 'Projected error rate (%)' },
  { cell: 'D25', alias: 'correctedBookValue', kind: 'formula', type: 'amount', format: EUR, label: 'Corrected Book Value (CBV)', formula: 'CBV = BV − EE' },
  { cell: 'D26', alias: 'precision', kind: 'formula', type: 'amount', label: 'Precision', formula: 'SE = N · z · s_w / √Σn_h' },
  { cell: 'D27', alias: 'relativePrecision', kind: 'formula', type: 'percent', format: RATE, label: 'Relative precision (% of the total book value of the population)' },
  { cell: 'D28', alias: 'upperErrorLimitRate', kind: 'formula', type: 'percent', format: RATE, label: 'Upper limit of error rate', formula: '(EE + SE) / BV' },
  { cell: 'D29', alias: 'lowerCorrectedBookValue', kind: 'formula', type: 'amount', format: EUR, label: 'Lower limit for the corrected book value (LL=CBV-SE)' },
  { cell: 'D30', alias: 'bookValueLessTolerable', kind: 'formula', type: 'amount', format: EUR, label: 'Book Value - Tolerable error (BV-TE)' },
]

export const definition: MethodDefinition = {
  sheet: 'X3_DiffSch_S_2017',
  number: 'X3',
  title: 'Differenzschätzung, geschichtet (Template 11 der Vorlage von 2017, unverändert)',
  shortTitle: 'Differenzschätzung, geschichtet (2017)',
  legalBasis: LEGACY_LEGAL_BASIS,
  sections: [
    { id: 'A', title: 'Positive population characteristics', fields: population },
    { id: 'B', title: 'Sample size determination', fields: size },
    { id: 'C', title: 'Sample results', fields: results },
  ],
  summary: {
    primary: { cell: 'D15', label: 'Planned sample size (n)', unit: 'Einheiten' },
    rows: [
      { cell: 'D23', label: 'Projected error' },
      { cell: 'D26', label: 'Precision' },
      { cell: 'D29', label: 'Lower limit for the corrected book value (LL=CBV-SE)' },
      { cell: 'D30', label: 'Book Value - Tolerable error (BV-TE)' },
      { cell: 'D24', label: 'Projected error rate (%)', strong: true },
      { cell: 'D28', label: 'Upper limit of error rate', strong: true },
    ],
    gauge: { threshold: 'D13', rate: 'D24', upper: 'D28', rateLabel: 'Projected error rate', upperLabel: 'Upper limit of error rate' },
  },
}
