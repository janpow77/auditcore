/**
 * Methodendefinition Blatt X1_KonsMUS_2017 (Altvorlage von 2017, Template 1:
 * konservativer MUS-Ansatz). Bezeichnungen und Abschnitte stehen wörtlich –
 * englisch und mit den Schreibweisen der Vorlage – in den Spalten A und B.
 *
 * **Ableitung der Eingaben.** Die grauen Altvorlagen kennzeichnen Eingaben
 * nicht farbig. Eingaben sind die leeren Zellen der Spalte C, auf die Formeln
 * verweisen; die Bezeichnung steht in der Nachbarzelle der Spalte B:
 *
 * | Zelle | gelesen von | Bezeichnung (Spalte B) |
 * |---|---|---|
 * | C1 | C8, C10, C11, C12, C18, C21, C22 | Total book value … |
 * | C4 | C5, C6 | Confidence level |
 * | C7 | C8 | Expected error rate |
 * | C13 | C19 | Sum of errors in sampling units with BV larger than sampling interval |
 * | C14 | C19 | Sum of sample error rates |
 * | C16 | C17, C18, C20 | Incremental Allowance |
 *
 * Leer und beschriftet, aber von keiner Formel gelesen (Angaben zum Vorgang):
 * C2 (Sampling unit), C3 (Size of population). C9 ist keine Eingabe, sondern
 * der feste Wert 2 %. Das Konfidenzniveau fragt die Vorlage in fünf Stufen ab
 * (60, 70, 80, 90, 95 %); sie sind die Auswahl des Felds und decken sich mit
 * den Niveaus der z-Tabelle in Blatt 01.
 *
 * Abschnitte haben in der Vorlage keine Kennbuchstaben; A–D zählen sie durch.
 * Die Zuverlässigkeitsfaktoren für die Incremental Allowance stehen in Blatt
 * X1a; X1 selbst liest sie nicht.
 */
import type { FieldDefinition, MethodDefinition } from '../../model/definition'
import { LEGACY_LEGAL_BASIS, LEGACY_NOTICE_LABEL } from '../shared/legacy'

const EUR = '#,##0" €"'
const INT = '#,##0'
const RATE = '0.00%'
const FACTOR = '#,##0.00'

const population: FieldDefinition[] = [
  { cell: 'G1', alias: 'legacyNotice', kind: 'formula', type: 'check', label: LEGACY_NOTICE_LABEL },
  { cell: 'C1', alias: 'bookValue', kind: 'input', type: 'amount', format: INT, label: 'Total book value (declared expenditure in the reference period) - positive population' },
  { cell: 'C2', alias: 'samplingUnit', kind: 'input', type: 'text', label: 'Sampling unit' },
  { cell: 'C3', alias: 'populationSize', kind: 'input', type: 'integer', label: 'Size of population (number of sampling units)' },
]

const size: FieldDefinition[] = [
  { cell: 'C4', alias: 'confidenceLevel', kind: 'input', type: 'choice', format: '0%', list: 'confidence', label: 'Confidence level' },
  { cell: 'C5', alias: 'reliabilityFactor', kind: 'formula', type: 'decimal', format: FACTOR, label: 'Reliability Factor (RF)' },
  { cell: 'C6', alias: 'expansionFactor', kind: 'formula', type: 'decimal', format: FACTOR, label: 'Expansion Factor (EF)' },
  { cell: 'C7', alias: 'anticipatedErrorRate', kind: 'input', type: 'percent', format: RATE, label: 'Expected error rate' },
  { cell: 'C8', alias: 'anticipatedError', kind: 'formula', type: 'amount', format: EUR, label: 'Antecipated error', formula: 'AE = expected error rate × BV' },
  { cell: 'C9', alias: 'materiality', kind: 'formula', type: 'percent', format: '0%', label: 'Materiality level (maximum 2%; set by the regulation)' },
  { cell: 'C10', alias: 'tolerableError', kind: 'formula', type: 'amount', format: EUR, label: 'Tolerable error (TE)', formula: 'TE = materiality level × BV' },
  { cell: 'C11', alias: 'sampleSize', kind: 'formula', type: 'integer', format: INT, label: 'Planned sample size (n)', formula: 'n = RF · BV / (TE − AE · EF), mindestens 30' },
  { cell: 'C12', alias: 'samplingInterval', kind: 'formula', type: 'amount', format: EUR, label: 'Sampling interval', formula: 'SI = BV / n' },
]

const findings: FieldDefinition[] = [
  // Die Vorlage verwendet C13 unmittelbar (anders als Blatt 03 mit N(…)): Pflicht.
  { cell: 'C13', alias: 'highValueErrors', kind: 'input', type: 'amount', format: EUR, optional: false, label: 'Sum of errors in sampling units with BV larger than sampling interval' },
  { cell: 'C14', alias: 'errorRateSum', kind: 'input', type: 'decimal', format: '0.0000', label: 'Sum of sample error rates' },
]

const projection: FieldDefinition[] = [
  { cell: 'C15', alias: 'basicPrecision', kind: 'formula', type: 'amount', format: EUR, label: 'Basic precision', formula: 'BP = RF · SI' },
  { cell: 'C16', alias: 'incrementalAllowance', kind: 'input', type: 'amount', format: EUR, label: 'Incremental Allowance' },
  { cell: 'C17', alias: 'precision', kind: 'formula', type: 'amount', format: EUR, label: 'Precision', formula: 'BP + IA' },
  { cell: 'C18', alias: 'relativePrecision', kind: 'formula', type: 'percent', format: RATE, label: 'Relative precision (% of the total book value of the population)' },
  { cell: 'C19', alias: 'projectedError', kind: 'formula', type: 'amount', format: EUR, label: 'Projected error', formula: 'EE = Σ error rates · SI + errors of the high-value units' },
  { cell: 'C20', alias: 'upperErrorLimit', kind: 'formula', type: 'amount', format: EUR, label: 'Upper limit of error', formula: 'ULE = EE + IA + BP' },
  { cell: 'C21', alias: 'projectedErrorRate', kind: 'formula', type: 'percent', format: RATE, label: 'Projected error rate (%)' },
  { cell: 'C22', alias: 'upperErrorLimitRate', kind: 'formula', type: 'percent', format: RATE, label: 'Upper limit of projected error rate (%)' },
]

export const definition: MethodDefinition = {
  tables: ['X1a_RF_2017'],
  sheet: 'X1_KonsMUS_2017',
  number: 'X1',
  title: 'Konservativer MUS-Ansatz (Template 1 der Vorlage von 2017, unverändert)',
  shortTitle: 'Konservativer MUS-Ansatz (2017)',
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
      { cell: 'C12', label: 'Sampling interval' },
      { cell: 'C19', label: 'Projected error' },
      { cell: 'C17', label: 'Precision' },
      { cell: 'C21', label: 'Projected error rate (%)', strong: true },
      { cell: 'C22', label: 'Upper limit of projected error rate (%)', strong: true },
    ],
    gauge: { threshold: 'C9', rate: 'C21', upper: 'C22', rateLabel: 'Projected error rate', upperLabel: 'Upper limit of projected error rate' },
  },
}
