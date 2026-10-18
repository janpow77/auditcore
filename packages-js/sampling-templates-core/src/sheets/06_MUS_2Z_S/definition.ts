/**
 * Methodendefinition Blatt 06_MUS_2Z_S. Erzeugt mit `scripts/generate-definition.mjs`
 * und von Hand geprüft. Schichtzeilen tragen `columns: STRATA_COLUMNS`: `cell` ist die
 * Zelle der ersten Schicht (Spalte D), `total` die Summenzelle in Spalte C, soweit die
 * Vorlage eine hat. Fundstellen stehen in diesem Blatt in Spalte K. Die Erhöhung bei
 * begrenztem Umfang rechnet die Vorlage hier innerhalb der Zeile 69.
 */
import type { FieldDefinition, MethodDefinition } from '../../model/definition'
import { STRATA_COLUMNS } from '../../model/strata'
import { INCREASE_INTERPRETATION } from '../shared/mus'
import { HIGH_VALUE_INTERPRETATION, ROUNDING_INTERPRETATION, UPPER_LIMIT_INTERPRETATION } from '../shared/interpretations'

const EUR = '#,##0.00" €"'
const INT = '#,##0'
const RATE = '0.00%'
const DEC4 = '0.0000'
/** Die Vorlage rechnet die Erhöhung in Zeile 69; gekennzeichnet sind die Auswahl des Ansatzes und diese Zeile. */
const INCREASE_NOTE = `Ansatz „Erhöhung“ – ${INCREASE_INTERPRETATION}`

const population: FieldDefinition[] = [
  { cell: 'C4', alias: 'programme', kind: 'input', type: 'text', format: '@', label: 'Programm(e) / CCI', hint: 'Art. 3 Abs. 1 und 2 DelVO.' },
  { cell: 'C5', alias: 'accountingYear', kind: 'input', type: 'text', format: '@', label: 'Geschäftsjahr' },
  { cell: 'C6', alias: 'samplingUnit', kind: 'input', type: 'text', format: '@', label: 'Stichprobeneinheit (z. B. Vorhaben, Ausgabenerklärung, Zahlungsantrag)' },
  { cell: 'D8', alias: 'stratumBookValuePeriod1', kind: 'input', type: 'amount', format: EUR, columns: STRATA_COLUMNS, total: 'C8', label: 'Buchwert Zeitraum 1 (Ist) (BV_h1)' },
  { cell: 'D9', alias: 'stratumPlannedBookValuePeriod2', kind: 'input', type: 'amount', format: EUR, columns: STRATA_COLUMNS, total: 'C9', label: 'Prognostizierter Buchwert Zeitraum 2 (BV_h2)' },
  { cell: 'D10', alias: 'stratumPlannedUnitsPeriod2', kind: 'input', type: 'integer', format: INT, columns: STRATA_COLUMNS, total: 'C10', label: 'Prognostizierte Anzahl Einheiten Zeitraum 2 (N_h2)' },
  { cell: 'C11', alias: 'plannedBookValue', kind: 'formula', type: 'amount', format: EUR, label: 'Prognostizierter Buchwert des Geschäftsjahres (BV_1+2)' },
]

const parameters: FieldDefinition[] = [
  { cell: 'C12', alias: 'systemReliability', kind: 'input', type: 'choice', format: '@', list: 'reliability', label: 'Zuverlässigkeit des Verwaltungs- und Kontrollsystems (hoch / mittel / gering)', hint: 'Anh. I Nr. 2: Bewertung unter Berücksichtigung der Systemprüfungen, so dass das kombinierte Sicherheitsniveau hoch ist.' },
  { cell: 'C13', alias: 'confidenceLevel', kind: 'input', type: 'choice', format: '0%', list: 'confidence', label: 'Konfidenzniveau', hint: 'Anh. I Nr. 2: hoch ≥ 60 %, gering ≥ 90 %; Auswahl aus Blatt 01.' },
  { cell: 'C14', alias: 'testType', kind: 'input', type: 'choice', format: '@', list: 'testType', default: 'zweiseitig', label: 'Testart (zweiseitig / einseitig)', hint: 'Anh. I Nr. 3; Art. 2 Nr. 17 und 18 DelVO.' },
  { cell: 'C15', alias: 'zCoefficient', kind: 'formula', type: 'decimal', format: '0.000', label: "Koeffizient z der Normalverteilung (z / z')", hint: 'Anh. I Nr. 3, Tabelle der z-Werte (95 % außerhalb der Tabelle, siehe Blatt 01).' },
  { cell: 'C16', alias: 'checkConfidence', kind: 'formula', type: 'check', label: 'Prüfung Konfidenzniveau gegen Systembewertung', hint: 'Anh. I Nr. 2 legt nur die Eckwerte fest; für „mittel“ ist das Konfidenzniveau fachlich zu begründen.' },
  { cell: 'C17', alias: 'materiality', kind: 'input', type: 'percent', format: RATE, default: 0.02, label: 'Signifikanzschwelle (höchstens 2 %)', hint: 'Anh. I Nr. 1 i. V. m. Anh. XX Nr. 5.9 VO (EU) 2021/1060.' },
  { cell: 'C18', alias: 'checkMateriality', kind: 'formula', type: 'check', label: 'Prüfung Signifikanzschwelle' },
  { cell: 'C19', alias: 'tolerableError', kind: 'formula', type: 'amount', format: EUR, label: 'Zulässiger Fehler (TE = Signifikanzschwelle × BV)', hint: 'Anh. II: TE höchstens 2 % der gesamten Ausgaben.' },
  { cell: 'C20', alias: 'anticipatedErrorRate', kind: 'input', type: 'percent', format: RATE, label: 'Voraussichtliche Fehlerquote', hint: 'Anh. I Nr. 4: Pilotstichprobe, historische Daten oder fachkundiges Ermessen.' },
  { cell: 'C21', alias: 'anticipatedError', kind: 'formula', type: 'amount', format: EUR, label: 'Voraussichtlicher Fehler (AE = voraussichtliche Fehlerquote × BV)' },
  { cell: 'C22', alias: 'checkTolerableError', kind: 'formula', type: 'check', label: 'Prüfung TE > AE' },
  { cell: 'D24', alias: 'stratumAnticipatedDeviationPeriod1', kind: 'input', type: 'decimal', format: DEC4, columns: STRATA_COLUMNS, label: 'Voraussichtliche Standardabweichung der Fehlerquoten Zeitraum 1 (σ_rh1)' },
  { cell: 'D25', alias: 'stratumAnticipatedDeviationPeriod2', kind: 'input', type: 'decimal', format: DEC4, columns: STRATA_COLUMNS, label: 'Voraussichtliche Standardabweichung der Fehlerquoten Zeitraum 2 (σ_rh2)' },
  { cell: 'D26', alias: 'stratumVarianceTerm', kind: 'formula', type: 'amount', format: EUR, columns: STRATA_COLUMNS, total: 'C26', label: 'Hilfszeile BV_h1·σ²_rh1 + BV_h2·σ²_rh2' },
  { cell: 'C27', alias: 'weightedDeviation', kind: 'formula', type: 'decimal', format: DEC4, label: 'Gewichtete Standardabweichung √(σ²_rw1 + σ²_rw2) (σ_rw1+2)' },
  { cell: 'C28', alias: 'recalculationApproach', kind: 'input', type: 'choice', format: '@', list: 'recalculation', default: 'Standard (Art. 5 Abs. 6 Buchst. a)', label: 'Ansatz der Neuberechnung des Stichprobenumfangs', hint: 'Art. 5 Abs. 6 Buchst. a (Standard) bzw. b (global); bei begrenztem Umfang zusätzlich Art. 5 Abs. 7 UAbs. 4 Buchst. a (Erhöhung).', interpretation: INCREASE_NOTE },
]

const size: FieldDefinition[] = [
  { cell: 'C29', alias: 'computedSampleSize', kind: 'formula', type: 'integer', format: INT, label: 'Rechnerischer Gesamtumfang (n_1+2)', interpretation: ROUNDING_INTERPRETATION },
  { cell: 'C30', alias: 'programmeCategory', kind: 'input', type: 'choice', list: 'category', label: 'Kategorie des Programms nach Anh. XI Tabelle 2 VO (EU) 2021/1060 (1–4)', hint: 'Art. 5 Abs. 7 UAbs. 1 DelVO; ErwG 10.' },
  { cell: 'C31', alias: 'article83', kind: 'input', type: 'choice', format: '@', list: 'yesNo', default: 'Nein', label: 'Verbesserte angemessene Regelungen nach Art. 83 VO (EU) 2021/1060 (Ja/Nein)', hint: 'Anh. I Buchst. a DelVO: Stichprobe von 30 Einheiten.' },
  { cell: 'C32', alias: 'applyLimitedSize', kind: 'input', type: 'choice', format: '@', list: 'yesNo', default: 'Nein', label: 'Begrenzten Stichprobenumfang anwenden (Ja/Nein)', hint: 'Art. 5 Abs. 7: Anwendung auf eine Stichprobe für die gesamte Grundgesamtheit (UAbs. 2).' },
  { cell: 'C33', alias: 'checkLimitedSize', kind: 'formula', type: 'check', label: 'Zulässigkeit des begrenzten Stichprobenumfangs' },
  { cell: 'C34', alias: 'limitedSampleSize', kind: 'formula', type: 'integer', format: INT, label: 'Begrenzter Stichprobenumfang (Einheiten) (n_lim)', hint: 'Angerechnet werden alle Einheiten der Zufallsschichten und nur die hochwertigen Einheiten umfassender Schichten (Art. 5 Abs. 7 UAbs. 3).' },
  { cell: 'C35', alias: 'sampleSize', kind: 'result', type: 'integer', format: INT, label: 'Anzuwendender Gesamtumfang (mind. 30; ggf. begrenzt)' },
  { cell: 'D37', alias: 'stratumSampleSizePeriod1', kind: 'formula', type: 'integer', format: INT, columns: STRATA_COLUMNS, total: 'C37', label: 'Umfang Zeitraum 1 je Schicht (BV_h1/BV · n) (n_h1)' },
  { cell: 'D38', alias: 'stratumPlannedSampleSizePeriod2', kind: 'formula', type: 'integer', format: INT, columns: STRATA_COLUMNS, total: 'C38', label: 'Geplanter Umfang Zeitraum 2 je Schicht (n_h2)' },
]

const period1: FieldDefinition[] = [
  { cell: 'D40', alias: 'stratumCutOffPeriod1', kind: 'formula', type: 'amount', format: EUR, columns: STRATA_COLUMNS, label: 'Grenzwert Zeitraum 1 je Schicht (BV/n)' },
  { cell: 'D41', alias: 'stratumHighValueUnitsPeriod1', kind: 'input', type: 'integer', format: INT, columns: STRATA_COLUMNS, total: 'C41', label: 'Anzahl hochwertiger Einheiten (n_eh)' },
  { cell: 'D42', alias: 'stratumHighValueBookValuePeriod1', kind: 'input', type: 'amount', format: EUR, columns: STRATA_COLUMNS, total: 'C42', label: 'Buchwert der hochwertigen Einheiten (BV_eh)' },
  { cell: 'D43', alias: 'stratumRandomBookValuePeriod1', kind: 'formula', type: 'amount', format: EUR, columns: STRATA_COLUMNS, total: 'C43', label: 'Buchwert der Zufallsschicht (BV_hs)' },
  { cell: 'D44', alias: 'stratumRandomUnitsPeriod1', kind: 'formula', type: 'integer', format: INT, columns: STRATA_COLUMNS, total: 'C44', label: 'Auszuwählende Zufallseinheiten (n_hs)', interpretation: HIGH_VALUE_INTERPRETATION },
  { cell: 'D45', alias: 'checkStratumMinimumUnitsPeriod1', kind: 'formula', type: 'check', columns: STRATA_COLUMNS, label: 'Mindestens drei Einheiten je Zufallsschicht', hint: 'Art. 5 Abs. 5 DelVO.' },
  { cell: 'D46', alias: 'stratumSamplingIntervalPeriod1', kind: 'formula', type: 'amount', format: EUR, columns: STRATA_COLUMNS, label: 'Auswahlintervall (SI_h)' },
  { cell: 'D47', alias: 'stratumHighValueErrorsPeriod1', kind: 'input', type: 'amount', format: EUR, columns: STRATA_COLUMNS, total: 'C47', label: 'Summe der Fehler in hochwertigen Einheiten (ΣE_eh)' },
  { cell: 'D48', alias: 'stratumErrorRateSumPeriod1', kind: 'input', type: 'decimal', format: DEC4, columns: STRATA_COLUMNS, total: 'C48', label: 'Summe der Fehlerquoten der Zufallsschicht (Σ E/BV)' },
  { cell: 'D49', alias: 'stratumSampleDeviationPeriod1', kind: 'input', type: 'decimal', format: DEC4, columns: STRATA_COLUMNS, label: 'Standardabweichung der Fehlerquoten der Zufallsschicht (s_rh)' },
]

const recalculation: FieldDefinition[] = [
  { cell: 'D51', alias: 'stratumBookValuePeriod2', kind: 'input', type: 'amount', format: EUR, columns: STRATA_COLUMNS, total: 'C51', label: 'Buchwert Zeitraum 2 (Ist) (BV_h2)' },
  { cell: 'D52', alias: 'stratumUnitsPeriod2', kind: 'input', type: 'integer', format: INT, columns: STRATA_COLUMNS, total: 'C52', label: 'Anzahl Einheiten Zeitraum 2 (Ist) (N_h2)' },
  { cell: 'D53', alias: 'stratumUpdatedDeviationPeriod2', kind: 'input', type: 'decimal', format: DEC4, columns: STRATA_COLUMNS, label: 'Aktualisierte Standardabweichung Zeitraum 2 (σ_rh2)' },
  { cell: 'C54', alias: 'updatedAnticipatedErrorRate', kind: 'input', type: 'percent', format: RATE, label: 'Aktualisierte voraussichtliche Fehlerquote (leer = Wert aus I)' },
  { cell: 'C55', alias: 'bookValue', kind: 'formula', type: 'amount', format: EUR, label: 'Buchwert des Geschäftsjahres (BV)' },
  { cell: 'C56', alias: 'updatedTolerableError', kind: 'formula', type: 'amount', format: EUR, label: 'Zulässiger Fehler (aktualisiert) (TE)' },
  { cell: 'C57', alias: 'updatedAnticipatedError', kind: 'formula', type: 'amount', format: EUR, label: 'Voraussichtlicher Fehler (aktualisiert) (AE)' },
  { cell: 'D59', alias: 'stratumRecalculationDeviationPeriod1', kind: 'formula', type: 'decimal', format: DEC4, columns: STRATA_COLUMNS, label: 'Standardabweichung Zeitraum 1 (s, ersatzweise σ) (s_rh1)' },
  { cell: 'D60', alias: 'stratumDenominatorTerm', kind: 'formula', type: 'amount', format: EUR, columns: STRATA_COLUMNS, total: 'C60', label: 'Hilfszeile BV²_h1/n_h1 · s²_rh1' },
  { cell: 'D61', alias: 'stratumNumeratorTerm', kind: 'formula', type: 'amount', format: EUR, columns: STRATA_COLUMNS, total: 'C61', label: 'Hilfszeile BV_h2 · σ²_rh2' },
  { cell: 'C62', alias: 'standardDenominator', kind: 'formula', type: 'amount', format: EUR, label: 'Nenner (TE − AE)² − z²·Σ BV²_h1/n_h1·s²_rh1' },
  { cell: 'C63', alias: 'standardSampleSizePeriod2', kind: 'formula', type: 'integer', format: INT, label: 'Standard: n₂ = z²·BV₂·Σ(BV_h2·σ²_rh2) / Nenner (n_2)' },
  { cell: 'D64', alias: 'stratumGlobalVarianceTerm', kind: 'formula', type: 'amount', format: EUR, columns: STRATA_COLUMNS, total: 'C64', label: 'Hilfszeile global: BV_h1·s²_rh1 + BV_h2·σ²_rh2' },
  { cell: 'C65', alias: 'globalComputedSampleSize', kind: 'formula', type: 'integer', format: INT, label: 'Global: rechnerischer Gesamtumfang' },
  { cell: 'C66', alias: 'globalSampleSize', kind: 'formula', type: 'integer', format: INT, label: 'Global: anzuwendender Gesamtumfang' },
  { cell: 'D68', alias: 'stratumGlobalAdditionalUnitsPeriod1', kind: 'formula', type: 'integer', format: INT, columns: STRATA_COLUMNS, total: 'C68', label: 'Global: Zusatzeinheiten Zeitraum 1 je Schicht' },
  { cell: 'D69', alias: 'stratumSampleSizePeriod2', kind: 'result', type: 'integer', format: INT, columns: STRATA_COLUMNS, total: 'C69', label: 'Anzuwendender Umfang Zeitraum 2 je Schicht (mind. 3) (n_h2)', interpretation: INCREASE_NOTE },
  { cell: 'D70', alias: 'stratumFinalSampleSizePeriod1', kind: 'formula', type: 'integer', format: INT, columns: STRATA_COLUMNS, total: 'C70', label: 'Endgültiger Umfang Zeitraum 1 je Schicht (n_h1)' },
  { cell: 'C71', alias: 'checkLimitedSizeKept', kind: 'formula', type: 'check', label: 'Einhaltung des begrenzten Stichprobenumfangs' },
  { cell: 'C72', alias: 'checkMinimumSize', kind: 'formula', type: 'check', label: 'Mindestumfang des Geschäftsjahres' },
]

const period2: FieldDefinition[] = [
  { cell: 'D74', alias: 'stratumCutOffPeriod2', kind: 'formula', type: 'amount', format: EUR, columns: STRATA_COLUMNS, label: 'Grenzwert Zeitraum 2 je Schicht (BV/n)' },
  { cell: 'D75', alias: 'stratumHighValueUnitsPeriod2', kind: 'input', type: 'integer', format: INT, columns: STRATA_COLUMNS, total: 'C75', label: 'Anzahl hochwertiger Einheiten (n_eh)' },
  { cell: 'D76', alias: 'stratumHighValueBookValuePeriod2', kind: 'input', type: 'amount', format: EUR, columns: STRATA_COLUMNS, total: 'C76', label: 'Buchwert der hochwertigen Einheiten (BV_eh)' },
  { cell: 'D77', alias: 'stratumRandomBookValuePeriod2', kind: 'formula', type: 'amount', format: EUR, columns: STRATA_COLUMNS, total: 'C77', label: 'Buchwert der Zufallsschicht (BV_hs)' },
  { cell: 'D78', alias: 'stratumRandomUnitsPeriod2', kind: 'formula', type: 'integer', format: INT, columns: STRATA_COLUMNS, total: 'C78', label: 'Auszuwählende Zufallseinheiten (n_hs)' },
  { cell: 'D79', alias: 'checkStratumMinimumUnitsPeriod2', kind: 'formula', type: 'check', columns: STRATA_COLUMNS, label: 'Mindestens drei Einheiten je Zufallsschicht', hint: 'Art. 5 Abs. 5 DelVO.' },
  { cell: 'D80', alias: 'stratumSamplingIntervalPeriod2', kind: 'formula', type: 'amount', format: EUR, columns: STRATA_COLUMNS, label: 'Auswahlintervall (SI_h)' },
  { cell: 'D81', alias: 'stratumHighValueErrorsPeriod2', kind: 'input', type: 'amount', format: EUR, columns: STRATA_COLUMNS, total: 'C81', label: 'Summe der Fehler in hochwertigen Einheiten (ΣE_eh)' },
  { cell: 'D82', alias: 'stratumErrorRateSumPeriod2', kind: 'input', type: 'decimal', format: DEC4, columns: STRATA_COLUMNS, total: 'C82', label: 'Summe der Fehlerquoten der Zufallsschicht (Σ E/BV)' },
  { cell: 'D83', alias: 'stratumSampleDeviationPeriod2', kind: 'input', type: 'decimal', format: DEC4, columns: STRATA_COLUMNS, label: 'Standardabweichung der Fehlerquoten der Zufallsschicht (s_rh)' },
  { cell: 'D84', alias: 'stratumFinalRandomUnitsPeriod1', kind: 'formula', type: 'integer', format: INT, columns: STRATA_COLUMNS, total: 'C84', label: 'Endgültige Zufallseinheiten Zeitraum 1 je Schicht (n_h1s)' },
]

const projection: FieldDefinition[] = [
  { cell: 'D86', alias: 'stratumExhaustiveError', kind: 'formula', type: 'amount', format: EUR, columns: STRATA_COLUMNS, total: 'C86', label: 'Fehler der umfassenden Schichten (Z1 + Z2) (EE_eh)' },
  { cell: 'D87', alias: 'stratumRandomError', kind: 'formula', type: 'amount', format: EUR, columns: STRATA_COLUMNS, total: 'C87', label: 'Extrapolierter Fehler der Zufallsschichten (Z1 + Z2) (EE_sh)' },
  { cell: 'D88', alias: 'stratumPrecisionTerm', kind: 'formula', type: 'amount', format: EUR, columns: STRATA_COLUMNS, total: 'C88', label: 'Hilfszeile BV²_h1s/n_h1s·s²_rh1 + BV²_h2s/n_h2s·s²_rh2' },
  { cell: 'C89', alias: 'projectedError', kind: 'result', type: 'amount', format: EUR, label: 'Extrapolierter Fehler EE' },
  { cell: 'C90', alias: 'precision', kind: 'result', type: 'amount', format: EUR, label: 'Genauigkeit SE = z·√(Σ…)' },
  { cell: 'C91', alias: 'systemicErrors', kind: 'input', type: 'amount', format: EUR, label: 'Abgegrenzte systembedingte Fehler (Betrag)', hint: 'Art. 2 Nr. 20, 21; Art. 8 Abs. 1 DelVO.' },
  { cell: 'C92', alias: 'anomalousErrors', kind: 'input', type: 'amount', format: EUR, label: 'Nicht berichtigte anomale Fehler (Betrag)', hint: 'Art. 2 Nr. 20, 21; Art. 8 Abs. 1 DelVO.' },
  { cell: 'C93', alias: 'upperErrorLimit', kind: 'result', type: 'amount', format: EUR, label: 'Obere Fehlergrenze (EE + SE + systembedingte + nicht berichtigte anomale Fehler)', hint: 'Art. 2 Nr. 20 DelVO.' },
  { cell: 'C94', alias: 'lowerErrorLimit', kind: 'formula', type: 'amount', format: EUR, label: 'Untere Fehlergrenze (EE − SE + systembedingte + nicht berichtigte anomale Fehler)', hint: 'Art. 2 Nr. 21 i. V. m. Nr. 17, 24 DelVO: nur beim zweiseitigen Test.' },
  { cell: 'C95', alias: 'relativePrecision', kind: 'formula', type: 'percent', format: RATE, label: 'Relative Genauigkeit (SE / BV)' },
  { cell: 'C96', alias: 'projectedErrorRate', kind: 'formula', type: 'percent', format: RATE, label: 'Extrapolierte Zufallsfehlerquote (EE / BV)' },
  { cell: 'C97', alias: 'totalErrorRate', kind: 'result', type: 'percent', format: RATE, label: 'Gesamtfehlerquote ((EE + systembedingte + nicht berichtigte anomale Fehler) / BV)', hint: 'Art. 8 Abs. 1 DelVO; endgültige Berechnung inkl. TH-Pauschale und Anh. III in Blatt 18.' },
  { cell: 'C98', alias: 'upperErrorLimitRate', kind: 'result', type: 'percent', format: RATE, label: 'Obere Fehlergrenze in % von BV' },
  { cell: 'C99', alias: 'assessment', kind: 'formula', type: 'check', label: 'Würdigung gegen die Signifikanzschwelle', interpretation: UPPER_LIMIT_INTERPRETATION },
]

export const definition: MethodDefinition = {
  sheet: '06_MUS_2Z_S',
  number: '06',
  title: 'MUS-Standardansatz – zwei Stichprobenzeiträume, geschichtet',
  shortTitle: 'MUS, 2 Zeiträume, geschichtet',
  legalBasis: 'Art. 4; Art. 5 Abs. 1 Buchst. a, Abs. 5–7; Art. 8; Anhang I; Anhang II Nr. 1.2 (geschichtet) DelVO (EU) 2023/67',
  sections: [
    { id: 'H', title: 'Grundgesamtheit und Prognose', fields: population },
    { id: 'I', title: 'Stichprobenparameter', reference: 'Anhang I', fields: parameters },
    { id: 'J', title: 'Stichprobenumfang „Erster Zeitraum“', fields: size },
    { id: 'K', title: 'Auswahl und Ergebnisse Zeitraum 1 (PPS)', fields: period1 },
    { id: 'L', title: 'Neuberechnung für Zeitraum 2', reference: 'Art. 5 Abs. 6 und 7', fields: recalculation },
    { id: 'M', title: 'Auswahl und Ergebnisse Zeitraum 2 (PPS)', fields: period2 },
    { id: 'N', title: 'Hochrechnung und Genauigkeit', reference: 'Anhang II Nr. 1.2, geschichtet; Art. 8', fields: projection },
  ],
  summary: {
    primary: { cell: 'C35', label: 'Anzuwendender Gesamtumfang', unit: 'Einheiten', reason: 'C29' },
    rows: [
      { cell: 'C70', label: 'Umfang Zeitraum 1 (Summe n_h1)' },
      { cell: 'C69', label: 'Umfang Zeitraum 2 (Summe n_h2)' },
      { cell: 'C89', label: 'Extrapolierter Fehler' },
      { cell: 'C90', label: 'Genauigkeit SE' },
      { cell: 'C97', label: 'Gesamtfehlerquote', strong: true },
      { cell: 'C98', label: 'Obere Fehlergrenze', strong: true },
    ],
    gauge: { threshold: 'C17', rate: 'C97', upper: 'C98' },
  },
}
