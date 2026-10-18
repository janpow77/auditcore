/**
 * Methodendefinition Blatt 07_MUS_3Z. Erzeugt mit `scripts/generate-definition.mjs`
 * aus der Zellbeschreibung der Vorlage und von Hand geprüft: Abschnitte,
 * Reihenfolge, Zellen, Zahlenformate, Bezeichnungen und Fundstellen entsprechen
 * der Vorlage (Spalten B und D). Die Summen aus Blatt 17 werden nicht
 * übernommen (`subsample`), weil die Unterstichproben keinem Zeitraum zugeordnet sind.
 */
import type { FieldDefinition, MethodDefinition } from '../../model/definition'
import { INCREASE_INTERPRETATION } from '../shared/mus'
import { HIGH_VALUE_INTERPRETATION, ROUNDING_INTERPRETATION, UPPER_LIMIT_INTERPRETATION } from '../shared/interpretations'

const EUR = '#,##0.00" €"'
const INT = '#,##0'
const RATE = '0.00%'
const DEC4 = '0.0000'

const population: FieldDefinition[] = [
  { cell: 'C4', alias: 'programme', kind: 'input', type: 'text', format: '@', label: 'Programm(e) / CCI', hint: 'Art. 3 Abs. 1 und 2 DelVO.' },
  { cell: 'C5', alias: 'accountingYear', kind: 'input', type: 'text', format: '@', label: 'Geschäftsjahr' },
  { cell: 'C6', alias: 'samplingUnit', kind: 'input', type: 'text', format: '@', label: 'Stichprobeneinheit (z. B. Vorhaben, Ausgabenerklärung, Zahlungsantrag)' },
  { cell: 'C7', alias: 'bookValuePeriod1', kind: 'input', type: 'amount', format: EUR, label: 'Buchwert Zeitraum 1 (Ist) (BV_1)' },
  { cell: 'C8', alias: 'plannedBookValuePeriod2', kind: 'input', type: 'amount', format: EUR, label: 'Prognostizierter Buchwert Zeitraum 2 (BV_2)' },
  { cell: 'C9', alias: 'plannedBookValuePeriod3', kind: 'input', type: 'amount', format: EUR, label: 'Prognostizierter Buchwert Zeitraum 3 (BV_3)' },
  { cell: 'C10', alias: 'plannedPopulationSizePeriod2', kind: 'input', type: 'integer', format: INT, label: 'Prognostizierte Anzahl Einheiten Zeitraum 2 (N_2)' },
  { cell: 'C11', alias: 'plannedPopulationSizePeriod3', kind: 'input', type: 'integer', format: INT, label: 'Prognostizierte Anzahl Einheiten Zeitraum 3 (N_3)' },
  { cell: 'C12', alias: 'plannedBookValue', kind: 'formula', type: 'amount', format: EUR, label: 'Prognostizierter Buchwert des Geschäftsjahres (BV_1+2+3)' },
]

const parameters: FieldDefinition[] = [
  { cell: 'C13', alias: 'systemReliability', kind: 'input', type: 'choice', format: '@', list: 'reliability', label: 'Zuverlässigkeit des Verwaltungs- und Kontrollsystems (hoch / mittel / gering)', hint: 'Anh. I Nr. 2: Bewertung unter Berücksichtigung der Systemprüfungen, so dass das kombinierte Sicherheitsniveau hoch ist.' },
  { cell: 'C14', alias: 'confidenceLevel', kind: 'input', type: 'choice', format: '0%', list: 'confidence', label: 'Konfidenzniveau', hint: 'Anh. I Nr. 2: hoch ≥ 60 %, gering ≥ 90 %; Auswahl aus Blatt 01.' },
  { cell: 'C15', alias: 'testType', kind: 'input', type: 'choice', format: '@', list: 'testType', default: 'zweiseitig', label: 'Testart (zweiseitig / einseitig)', hint: 'Anh. I Nr. 3; Art. 2 Nr. 17 und 18 DelVO.' },
  { cell: 'C16', alias: 'zCoefficient', kind: 'formula', type: 'decimal', format: '0.000', label: "Koeffizient z der Normalverteilung (z / z')", hint: 'Anh. I Nr. 3, Tabelle der z-Werte (95 % außerhalb der Tabelle, siehe Blatt 01).' },
  { cell: 'C17', alias: 'checkConfidence', kind: 'formula', type: 'check', label: 'Prüfung Konfidenzniveau gegen Systembewertung', hint: 'Anh. I Nr. 2 legt nur die Eckwerte fest; für „mittel“ ist das Konfidenzniveau fachlich zu begründen.' },
  { cell: 'C18', alias: 'materiality', kind: 'input', type: 'percent', format: RATE, default: 0.02, label: 'Signifikanzschwelle (höchstens 2 %)', hint: 'Anh. I Nr. 1 i. V. m. Anh. XX Nr. 5.9 VO (EU) 2021/1060.' },
  { cell: 'C19', alias: 'checkMateriality', kind: 'formula', type: 'check', label: 'Prüfung Signifikanzschwelle' },
  { cell: 'C20', alias: 'tolerableError', kind: 'formula', type: 'amount', format: EUR, label: 'Zulässiger Fehler (TE = Signifikanzschwelle × BV)', hint: 'Anh. II: TE höchstens 2 % der gesamten Ausgaben.' },
  { cell: 'C21', alias: 'anticipatedErrorRate', kind: 'input', type: 'percent', format: RATE, label: 'Voraussichtliche Fehlerquote', hint: 'Anh. I Nr. 4: Pilotstichprobe, historische Daten oder fachkundiges Ermessen.' },
  { cell: 'C22', alias: 'anticipatedError', kind: 'formula', type: 'amount', format: EUR, label: 'Voraussichtlicher Fehler (AE = voraussichtliche Fehlerquote × BV)' },
  { cell: 'C23', alias: 'checkTolerableError', kind: 'formula', type: 'check', label: 'Prüfung TE > AE' },
  { cell: 'C24', alias: 'anticipatedDeviationPeriod1', kind: 'input', type: 'decimal', format: DEC4, label: 'Voraussichtliche Standardabweichung der Fehlerquoten Zeitraum 1 (σ_r1)' },
  { cell: 'C25', alias: 'anticipatedDeviationPeriod2', kind: 'input', type: 'decimal', format: DEC4, label: 'Voraussichtliche Standardabweichung der Fehlerquoten Zeitraum 2 (σ_r2)' },
  { cell: 'C26', alias: 'anticipatedDeviationPeriod3', kind: 'input', type: 'decimal', format: DEC4, label: 'Voraussichtliche Standardabweichung der Fehlerquoten Zeitraum 3 (σ_r3)' },
  { cell: 'C27', alias: 'weightedDeviation', kind: 'formula', type: 'decimal', format: DEC4, label: 'Gewichtete Standardabweichung (σ_rw1+2+3)' },
  { cell: 'C28', alias: 'recalculationApproach', kind: 'input', type: 'choice', format: '@', list: 'recalculation', default: 'Standard (Art. 5 Abs. 6 Buchst. a)', label: 'Ansatz der Neuberechnung des Stichprobenumfangs', hint: 'Art. 5 Abs. 6 Buchst. a (Standard) bzw. b (global); bei begrenztem Umfang zusätzlich Art. 5 Abs. 7 UAbs. 4 Buchst. a (Erhöhung).' },
]

const size: FieldDefinition[] = [
  { cell: 'C29', alias: 'computedSampleSize', kind: 'formula', type: 'integer', format: INT, label: 'Rechnerischer Gesamtumfang (n_1+2+3)', interpretation: ROUNDING_INTERPRETATION },
  { cell: 'C30', alias: 'programmeCategory', kind: 'input', type: 'choice', list: 'category', label: 'Kategorie des Programms nach Anh. XI Tabelle 2 VO (EU) 2021/1060 (1–4)', hint: 'Art. 5 Abs. 7 UAbs. 1 DelVO; ErwG 10.' },
  { cell: 'C31', alias: 'article83', kind: 'input', type: 'choice', format: '@', list: 'yesNo', default: 'Nein', label: 'Verbesserte angemessene Regelungen nach Art. 83 VO (EU) 2021/1060 (Ja/Nein)', hint: 'Anh. I Buchst. a DelVO: Stichprobe von 30 Einheiten.' },
  { cell: 'C32', alias: 'applyLimitedSize', kind: 'input', type: 'choice', format: '@', list: 'yesNo', default: 'Nein', label: 'Begrenzten Stichprobenumfang anwenden (Ja/Nein)', hint: 'Art. 5 Abs. 7: Anwendung auf eine Stichprobe für die gesamte Grundgesamtheit (UAbs. 2).' },
  { cell: 'C33', alias: 'checkLimitedSize', kind: 'formula', type: 'check', label: 'Zulässigkeit des begrenzten Stichprobenumfangs' },
  { cell: 'C34', alias: 'limitedSampleSize', kind: 'formula', type: 'integer', format: INT, label: 'Begrenzter Stichprobenumfang (Einheiten) (n_lim)', hint: 'Angerechnet werden alle Einheiten der Zufallsschichten und nur die hochwertigen Einheiten umfassender Schichten (Art. 5 Abs. 7 UAbs. 3).' },
  { cell: 'C35', alias: 'sampleSize', kind: 'result', type: 'integer', format: INT, label: 'Anzuwendender Gesamtumfang (mind. 30; ggf. begrenzt)' },
  { cell: 'C36', alias: 'sampleSizePeriod1', kind: 'result', type: 'integer', format: INT, label: 'Stichprobenumfang Zeitraum 1 (n_1)' },
  { cell: 'C37', alias: 'plannedSampleSizePeriod2', kind: 'formula', type: 'integer', format: INT, label: 'Geplanter Umfang Zeitraum 2 (n_2)' },
  { cell: 'C38', alias: 'plannedSampleSizePeriod3', kind: 'formula', type: 'integer', format: INT, label: 'Geplanter Umfang Zeitraum 3 (n_3)' },
]

const period1: FieldDefinition[] = [
  { cell: 'C39', alias: 'cutOffPeriod1', kind: 'formula', type: 'amount', format: EUR, label: 'Grenzwert für hochwertige Einheiten (BV1/n1) (BV/n)', hint: 'Art. 5 Abs. 2 UAbs. 2: hochwertige Einheiten über dem Auswahlintervall werden vollständig geprüft.' },
  { cell: 'C40', alias: 'highValueUnitsPeriod1', kind: 'input', type: 'integer', format: INT, label: 'Anzahl hochwertiger Einheiten (BV > Grenzwert) (n_e)' },
  { cell: 'C41', alias: 'highValueBookValuePeriod1', kind: 'input', type: 'amount', format: EUR, label: 'Buchwert der hochwertigen Einheiten (BV_e)' },
  { cell: 'C42', alias: 'randomStratumBookValuePeriod1', kind: 'formula', type: 'amount', format: EUR, label: 'Buchwert der Zufallsschicht (niedrigwertige Einheiten) (BV_s)' },
  { cell: 'C43', alias: 'randomStratumUnitsPeriod1', kind: 'formula', type: 'integer', format: INT, label: 'Anzahl der in der Zufallsschicht auszuwählenden Einheiten (n_s)', interpretation: HIGH_VALUE_INTERPRETATION },
  { cell: 'C44', alias: 'checkMinimumUnitsPeriod1', kind: 'formula', type: 'check', label: 'Mindestens drei Einheiten in der Zufallsschicht' },
  { cell: 'C45', alias: 'samplingIntervalPeriod1', kind: 'formula', type: 'amount', format: EUR, label: 'Auswahlintervall (BV_s / n_s) (SI)', hint: 'Art. 2 Nr. 9; Art. 5 Abs. 2 UAbs. 2 DelVO.' },
  { cell: 'C46', alias: 'iterationUnitsPeriod1', kind: 'input', type: 'integer', format: INT, label: 'Einheiten der Zufallsschicht mit BV > Auswahlintervall (Iteration)', hint: 'Solche Einheiten sind der hochwertigen Schicht zuzuordnen; Grenzwert und Intervall sind neu zu berechnen.' },
  { cell: 'C47', alias: 'checkIterationPeriod1', kind: 'formula', type: 'check', label: 'Prüfung Iteration' },
  { cell: 'C48', alias: 'highValueErrorsPeriod1', kind: 'input', type: 'amount', format: EUR, label: 'Summe der Fehler in den hochwertigen Einheiten (ΣE_e)', hint: 'Bei Unterstichproben: auf die Stichprobeneinheit hochgerechneter Fehler (Art. 8 Abs. 3; Blatt 17).' },
  { cell: 'C49', alias: 'errorRateSumPeriod1', kind: 'input', type: 'decimal', format: DEC4, label: 'Summe der Fehlerquoten der Stichprobe der Zufallsschicht (Σ E_i/BV_i)' },
  { cell: 'C50', alias: 'sampleDeviationPeriod1', kind: 'input', type: 'decimal', format: DEC4, label: 'Standardabweichung der Fehlerquoten in der Stichprobe der Zufallsschicht (s_r)', hint: 'Aus derselben Stichprobe wie die Hochrechnung (Anh. II Nr. 1).' },
]

const recalculation2: FieldDefinition[] = [
  { cell: 'C51', alias: 'bookValuePeriod2', kind: 'input', type: 'amount', format: EUR, label: 'Buchwert Zeitraum 2 (Ist) (BV_2)' },
  { cell: 'C52', alias: 'populationSizePeriod2', kind: 'input', type: 'integer', format: INT, label: 'Anzahl Einheiten Zeitraum 2 (Ist) (N_2)' },
  { cell: 'C53', alias: 'updatedPlannedBookValuePeriod3', kind: 'input', type: 'amount', format: EUR, label: 'Aktualisierte Prognose Buchwert Zeitraum 3 (BV_3)' },
  { cell: 'C54', alias: 'updatedPlannedPopulationSizePeriod3', kind: 'input', type: 'integer', format: INT, label: 'Aktualisierte Prognose Anzahl Einheiten Zeitraum 3 (N_3)' },
  { cell: 'C55', alias: 'updatedDeviationPeriod2', kind: 'input', type: 'decimal', format: DEC4, label: 'Aktualisierte Standardabweichung Zeitraum 2 (σ_r2)' },
  { cell: 'C56', alias: 'updatedDeviationPeriod3', kind: 'input', type: 'decimal', format: DEC4, label: 'Aktualisierte Standardabweichung Zeitraum 3 (σ_r3)' },
  { cell: 'C57', alias: 'updatedAnticipatedErrorRate', kind: 'input', type: 'percent', format: RATE, label: 'Aktualisierte voraussichtliche Fehlerquote (leer = Wert aus I)' },
  { cell: 'C58', alias: 'updatedPlannedBookValue', kind: 'formula', type: 'amount', format: EUR, label: 'Buchwert des Geschäftsjahres (aktualisiert) (BV)' },
  { cell: 'C59', alias: 'updatedTolerableError', kind: 'formula', type: 'amount', format: EUR, label: 'Zulässiger Fehler (aktualisiert) (TE)' },
  { cell: 'C60', alias: 'updatedAnticipatedError', kind: 'formula', type: 'amount', format: EUR, label: 'Voraussichtlicher Fehler (aktualisiert) (AE)' },
  { cell: 'C61', alias: 'recalculationDeviationPeriod1', kind: 'formula', type: 'decimal', format: DEC4, label: 'Standardabweichung Zeitraum 1 (s, ersatzweise σ) (s_r1)' },
  { cell: 'C62', alias: 'bookValuePeriods2And3', kind: 'formula', type: 'amount', format: EUR, label: 'Buchwert Zeiträume 2 und 3 (BV_2+3)' },
  { cell: 'C63', alias: 'weightedDeviationPeriods2And3', kind: 'formula', type: 'decimal', format: DEC4, label: 'Gewichtete Standardabweichung Zeiträume 2 und 3 (σ_rw2+3)' },
  { cell: 'C64', alias: 'standardDenominator', kind: 'formula', type: 'amount', format: EUR, label: 'Nenner (TE − AE)² − z²·BV₁²/n₁·s²_r1' },
  { cell: 'C65', alias: 'standardSampleSizePeriods2And3', kind: 'formula', type: 'integer', format: INT, label: 'Standard: n₂₊₃ = (z·BV₂₊₃·σ_rw2+3)² / Nenner (n_2+3)' },
  { cell: 'C66', alias: 'standardSampleSizePeriod2', kind: 'formula', type: 'integer', format: INT, label: 'Standard: Umfang Zeitraum 2 (n_2)' },
  { cell: 'C67', alias: 'standardPlannedSampleSizePeriod3', kind: 'formula', type: 'integer', format: INT, label: 'Standard: geplanter Umfang Zeitraum 3 (n_3)' },
  { cell: 'C68', alias: 'globalWeightedDeviation', kind: 'formula', type: 'decimal', format: DEC4, label: 'Global: gewichtete Standardabweichung (σ_rw)' },
  { cell: 'C69', alias: 'globalComputedSampleSize', kind: 'formula', type: 'integer', format: INT, label: 'Global: rechnerischer Gesamtumfang' },
  { cell: 'C70', alias: 'globalSampleSize', kind: 'formula', type: 'integer', format: INT, label: 'Global: anzuwendender Gesamtumfang' },
  { cell: 'C71', alias: 'globalAdditionalUnitsPeriod1', kind: 'formula', type: 'integer', format: INT, label: 'Global: Zusatzeinheiten Zeitraum 1' },
  { cell: 'C72', alias: 'globalSampleSizePeriod2', kind: 'formula', type: 'integer', format: INT, label: 'Global: Umfang Zeitraum 2 (n_2)' },
  { cell: 'C73', alias: 'globalPlannedSampleSizePeriod3', kind: 'formula', type: 'integer', format: INT, label: 'Global: geplanter Umfang Zeitraum 3 (n_3)' },
  { cell: 'C74', alias: 'increasedSampleSizePeriod2', kind: 'formula', type: 'integer', format: INT, label: 'Begrenzt: erhöhter Umfang Zeitraum 2 (n_2)', hint: 'Art. 5 Abs. 7 UAbs. 4 Buchst. a; proportionale Erhöhung als Vorschlag.', interpretation: INCREASE_INTERPRETATION },
  { cell: 'C75', alias: 'sampleSizePeriod2', kind: 'result', type: 'integer', format: INT, label: 'Anzuwendender Umfang Zeitraum 2 (mind. 3) (n_2)' },
  { cell: 'C76', alias: 'updatedPlannedSampleSizePeriod3', kind: 'formula', type: 'integer', format: INT, label: 'Fortgeschriebener Planumfang Zeitraum 3 (n_3)' },
  { cell: 'C77', alias: 'recalculatedSampleSizePeriod1', kind: 'formula', type: 'integer', format: INT, label: 'Umfang Zeitraum 1 nach erster Neuberechnung (n_1)' },
]

const period2: FieldDefinition[] = [
  { cell: 'C78', alias: 'cutOffPeriod2', kind: 'formula', type: 'amount', format: EUR, label: 'Grenzwert für hochwertige Einheiten (BV2/n2) (BV/n)', hint: 'Art. 5 Abs. 2 UAbs. 2: hochwertige Einheiten über dem Auswahlintervall werden vollständig geprüft.' },
  { cell: 'C79', alias: 'highValueUnitsPeriod2', kind: 'input', type: 'integer', format: INT, label: 'Anzahl hochwertiger Einheiten (BV > Grenzwert) (n_e)' },
  { cell: 'C80', alias: 'highValueBookValuePeriod2', kind: 'input', type: 'amount', format: EUR, label: 'Buchwert der hochwertigen Einheiten (BV_e)' },
  { cell: 'C81', alias: 'randomStratumBookValuePeriod2', kind: 'formula', type: 'amount', format: EUR, label: 'Buchwert der Zufallsschicht (niedrigwertige Einheiten) (BV_s)' },
  { cell: 'C82', alias: 'randomStratumUnitsPeriod2', kind: 'formula', type: 'integer', format: INT, label: 'Anzahl der in der Zufallsschicht auszuwählenden Einheiten (n_s)' },
  { cell: 'C83', alias: 'checkMinimumUnitsPeriod2', kind: 'formula', type: 'check', label: 'Mindestens drei Einheiten in der Zufallsschicht' },
  { cell: 'C84', alias: 'samplingIntervalPeriod2', kind: 'formula', type: 'amount', format: EUR, label: 'Auswahlintervall (BV_s / n_s) (SI)', hint: 'Art. 2 Nr. 9; Art. 5 Abs. 2 UAbs. 2 DelVO.' },
  { cell: 'C85', alias: 'iterationUnitsPeriod2', kind: 'input', type: 'integer', format: INT, label: 'Einheiten der Zufallsschicht mit BV > Auswahlintervall (Iteration)', hint: 'Solche Einheiten sind der hochwertigen Schicht zuzuordnen; Grenzwert und Intervall sind neu zu berechnen.' },
  { cell: 'C86', alias: 'checkIterationPeriod2', kind: 'formula', type: 'check', label: 'Prüfung Iteration' },
  { cell: 'C87', alias: 'highValueErrorsPeriod2', kind: 'input', type: 'amount', format: EUR, label: 'Summe der Fehler in den hochwertigen Einheiten (ΣE_e)', hint: 'Bei Unterstichproben: auf die Stichprobeneinheit hochgerechneter Fehler (Art. 8 Abs. 3; Blatt 17).' },
  { cell: 'C88', alias: 'errorRateSumPeriod2', kind: 'input', type: 'decimal', format: DEC4, label: 'Summe der Fehlerquoten der Stichprobe der Zufallsschicht (Σ E_i/BV_i)' },
  { cell: 'C89', alias: 'sampleDeviationPeriod2', kind: 'input', type: 'decimal', format: DEC4, label: 'Standardabweichung der Fehlerquoten in der Stichprobe der Zufallsschicht (s_r)', hint: 'Aus derselben Stichprobe wie die Hochrechnung (Anh. II Nr. 1).' },
]

const recalculation3: FieldDefinition[] = [
  { cell: 'C90', alias: 'bookValuePeriod3', kind: 'input', type: 'amount', format: EUR, label: 'Buchwert Zeitraum 3 (Ist) (BV_3)' },
  { cell: 'C91', alias: 'populationSizePeriod3', kind: 'input', type: 'integer', format: INT, label: 'Anzahl Einheiten Zeitraum 3 (Ist) (N_3)' },
  { cell: 'C92', alias: 'finalDeviationPeriod3', kind: 'input', type: 'decimal', format: DEC4, label: 'Aktualisierte Standardabweichung Zeitraum 3 (σ_r3)' },
  { cell: 'C93', alias: 'finalAnticipatedErrorRate', kind: 'input', type: 'percent', format: RATE, label: 'Aktualisierte voraussichtliche Fehlerquote (leer = vorheriger Wert)' },
  { cell: 'C94', alias: 'bookValue', kind: 'formula', type: 'amount', format: EUR, label: 'Buchwert des Geschäftsjahres (BV₁ + BV₂ + BV₃)' },
  { cell: 'C95', alias: 'finalTolerableError', kind: 'formula', type: 'amount', format: EUR, label: 'Zulässiger Fehler (TE)' },
  { cell: 'C96', alias: 'finalAnticipatedError', kind: 'formula', type: 'amount', format: EUR, label: 'Voraussichtlicher Fehler (AE)' },
  { cell: 'C97', alias: 'recalculationDeviationPeriod2', kind: 'formula', type: 'decimal', format: DEC4, label: 'Standardabweichung Zeitraum 2 (s, ersatzweise σ) (s_r2)' },
  { cell: 'C98', alias: 'finalStandardDenominator', kind: 'formula', type: 'amount', format: EUR, label: 'Nenner (TE − AE)² − z²·BV₁²/n₁·s²_r1 − z²·BV₂²/n₂·s²_r2' },
  { cell: 'C99', alias: 'standardSampleSizePeriod3', kind: 'formula', type: 'integer', format: INT, label: 'Standard: n₃ = (z·BV₃·σ_r3)² / Nenner (n_3)' },
  { cell: 'C100', alias: 'finalGlobalWeightedDeviation', kind: 'formula', type: 'decimal', format: DEC4, label: 'Global: gewichtete Standardabweichung (σ_rw)' },
  { cell: 'C101', alias: 'finalGlobalComputedSampleSize', kind: 'formula', type: 'integer', format: INT, label: 'Global: rechnerischer Gesamtumfang' },
  { cell: 'C102', alias: 'finalGlobalSampleSize', kind: 'formula', type: 'integer', format: INT, label: 'Global: anzuwendender Gesamtumfang' },
  { cell: 'C103', alias: 'finalGlobalAdditionalUnitsPeriod1', kind: 'formula', type: 'integer', format: INT, label: 'Global: weitere Zusatzeinheiten Zeitraum 1' },
  { cell: 'C104', alias: 'globalAdditionalUnitsPeriod2', kind: 'formula', type: 'integer', format: INT, label: 'Global: Zusatzeinheiten Zeitraum 2' },
  { cell: 'C105', alias: 'globalSampleSizePeriod3', kind: 'formula', type: 'integer', format: INT, label: 'Global: Umfang Zeitraum 3 (n_3)' },
  { cell: 'C106', alias: 'increasedSampleSizePeriod3', kind: 'formula', type: 'integer', format: INT, label: 'Begrenzt: erhöhter Umfang Zeitraum 3 (n_3)', interpretation: INCREASE_INTERPRETATION },
  { cell: 'C107', alias: 'finalSampleSizePeriod1', kind: 'formula', type: 'integer', format: INT, label: 'Endgültiger Umfang Zeitraum 1 (n_1)' },
  { cell: 'C108', alias: 'finalSampleSizePeriod2', kind: 'formula', type: 'integer', format: INT, label: 'Endgültiger Umfang Zeitraum 2 (n_2)' },
  { cell: 'C109', alias: 'sampleSizePeriod3', kind: 'result', type: 'integer', format: INT, label: 'Anzuwendender Umfang Zeitraum 3 (mind. 3 und Auffüllung auf 30 Einheiten) (n_3)', hint: 'Art. 5 Abs. 5.' },
  { cell: 'C110', alias: 'checkLimitedSizeKept', kind: 'formula', type: 'check', label: 'Einhaltung des begrenzten Stichprobenumfangs' },
  { cell: 'C111', alias: 'checkMinimumSize', kind: 'formula', type: 'check', label: 'Mindestumfang des Geschäftsjahres' },
]

const period3: FieldDefinition[] = [
  { cell: 'C112', alias: 'cutOffPeriod3', kind: 'formula', type: 'amount', format: EUR, label: 'Grenzwert für hochwertige Einheiten (BV3/n3) (BV/n)', hint: 'Art. 5 Abs. 2 UAbs. 2: hochwertige Einheiten über dem Auswahlintervall werden vollständig geprüft.' },
  { cell: 'C113', alias: 'highValueUnitsPeriod3', kind: 'input', type: 'integer', format: INT, label: 'Anzahl hochwertiger Einheiten (BV > Grenzwert) (n_e)' },
  { cell: 'C114', alias: 'highValueBookValuePeriod3', kind: 'input', type: 'amount', format: EUR, label: 'Buchwert der hochwertigen Einheiten (BV_e)' },
  { cell: 'C115', alias: 'randomStratumBookValuePeriod3', kind: 'formula', type: 'amount', format: EUR, label: 'Buchwert der Zufallsschicht (niedrigwertige Einheiten) (BV_s)' },
  { cell: 'C116', alias: 'randomStratumUnitsPeriod3', kind: 'formula', type: 'integer', format: INT, label: 'Anzahl der in der Zufallsschicht auszuwählenden Einheiten (n_s)' },
  { cell: 'C117', alias: 'checkMinimumUnitsPeriod3', kind: 'formula', type: 'check', label: 'Mindestens drei Einheiten in der Zufallsschicht' },
  { cell: 'C118', alias: 'samplingIntervalPeriod3', kind: 'formula', type: 'amount', format: EUR, label: 'Auswahlintervall (BV_s / n_s) (SI)', hint: 'Art. 2 Nr. 9; Art. 5 Abs. 2 UAbs. 2 DelVO.' },
  { cell: 'C119', alias: 'iterationUnitsPeriod3', kind: 'input', type: 'integer', format: INT, label: 'Einheiten der Zufallsschicht mit BV > Auswahlintervall (Iteration)', hint: 'Solche Einheiten sind der hochwertigen Schicht zuzuordnen; Grenzwert und Intervall sind neu zu berechnen.' },
  { cell: 'C120', alias: 'checkIterationPeriod3', kind: 'formula', type: 'check', label: 'Prüfung Iteration' },
  { cell: 'C121', alias: 'highValueErrorsPeriod3', kind: 'input', type: 'amount', format: EUR, label: 'Summe der Fehler in den hochwertigen Einheiten (ΣE_e)', hint: 'Bei Unterstichproben: auf die Stichprobeneinheit hochgerechneter Fehler (Art. 8 Abs. 3; Blatt 17).' },
  { cell: 'C122', alias: 'errorRateSumPeriod3', kind: 'input', type: 'decimal', format: DEC4, label: 'Summe der Fehlerquoten der Stichprobe der Zufallsschicht (Σ E_i/BV_i)' },
  { cell: 'C123', alias: 'sampleDeviationPeriod3', kind: 'input', type: 'decimal', format: DEC4, label: 'Standardabweichung der Fehlerquoten in der Stichprobe der Zufallsschicht (s_r)', hint: 'Aus derselben Stichprobe wie die Hochrechnung (Anh. II Nr. 1).' },
  { cell: 'C124', alias: 'finalRandomUnitsPeriod1', kind: 'formula', type: 'integer', format: INT, label: 'Endgültige Zufallseinheiten Zeitraum 1 (n_1s)' },
  { cell: 'C125', alias: 'finalRandomUnitsPeriod2', kind: 'formula', type: 'integer', format: INT, label: 'Endgültige Zufallseinheiten Zeitraum 2 (n_2s)' },
]

const projection: FieldDefinition[] = [
  { cell: 'C126', alias: 'exhaustiveStratumError', kind: 'formula', type: 'amount', format: EUR, label: 'Fehler der umfassenden Schichten (EE_e)' },
  { cell: 'C127', alias: 'randomStratumError', kind: 'formula', type: 'amount', format: EUR, label: 'Extrapolierter Fehler der Zufallsschichten (EE_s)' },
  { cell: 'C128', alias: 'projectedError', kind: 'result', type: 'amount', format: EUR, label: 'Extrapolierter Fehler EE' },
  { cell: 'C129', alias: 'precision', kind: 'result', type: 'amount', format: EUR, label: 'Genauigkeit SE = z·√(Σ BV²_ts/n_ts·s²_rt)' },
  { cell: 'C130', alias: 'systemicErrors', kind: 'input', type: 'amount', format: EUR, label: 'Abgegrenzte systembedingte Fehler (Betrag)', hint: 'Art. 2 Nr. 20, 21; Art. 8 Abs. 1 DelVO.' },
  { cell: 'C131', alias: 'anomalousErrors', kind: 'input', type: 'amount', format: EUR, label: 'Nicht berichtigte anomale Fehler (Betrag)', hint: 'Art. 2 Nr. 20, 21; Art. 8 Abs. 1 DelVO.' },
  { cell: 'C132', alias: 'upperErrorLimit', kind: 'result', type: 'amount', format: EUR, label: 'Obere Fehlergrenze (EE + SE + systembedingte + nicht berichtigte anomale Fehler)', hint: 'Art. 2 Nr. 20 DelVO.' },
  { cell: 'C133', alias: 'lowerErrorLimit', kind: 'formula', type: 'amount', format: EUR, label: 'Untere Fehlergrenze (EE − SE + systembedingte + nicht berichtigte anomale Fehler)', hint: 'Art. 2 Nr. 21 i. V. m. Nr. 17, 24 DelVO: nur beim zweiseitigen Test.' },
  { cell: 'C134', alias: 'relativePrecision', kind: 'formula', type: 'percent', format: RATE, label: 'Relative Genauigkeit (SE / BV)' },
  { cell: 'C135', alias: 'projectedErrorRate', kind: 'formula', type: 'percent', format: RATE, label: 'Extrapolierte Zufallsfehlerquote (EE / BV)' },
  { cell: 'C136', alias: 'totalErrorRate', kind: 'result', type: 'percent', format: RATE, label: 'Gesamtfehlerquote ((EE + systembedingte + nicht berichtigte anomale Fehler) / BV)', hint: 'Art. 8 Abs. 1 DelVO; endgültige Berechnung inkl. TH-Pauschale und Anh. III in Blatt 18.' },
  { cell: 'C137', alias: 'upperErrorLimitRate', kind: 'result', type: 'percent', format: RATE, label: 'Obere Fehlergrenze in % von BV' },
  { cell: 'C138', alias: 'assessment', kind: 'formula', type: 'check', label: 'Würdigung gegen die Signifikanzschwelle', interpretation: UPPER_LIMIT_INTERPRETATION },
]

export const definition: MethodDefinition = {
  sheet: '07_MUS_3Z',
  number: '07',
  title: 'MUS-Standardansatz – drei Stichprobenzeiträume, nicht geschichtet',
  shortTitle: 'MUS, 3 Zeiträume',
  legalBasis: 'Art. 4 Abs. 1; Art. 5 Abs. 1 Buchst. a, Abs. 5–7; Art. 8; Anhang I; Anhang II Nr. 1.3 DelVO (EU) 2023/67',
  sections: [
    { id: 'H', title: 'Grundgesamtheit und Prognose', fields: population },
    { id: 'I', title: 'Stichprobenparameter', reference: 'Anhang I', fields: parameters },
    { id: 'J', title: 'Stichprobenumfang „Erster Zeitraum“', reference: 'Anhang II Nr. 1.3', fields: size },
    { id: 'K', title: 'Auswahl und Ergebnisse Zeitraum 1', fields: period1 },
    { id: 'L', title: 'Neuberechnung nach Zeitraum 1 („Zweiter Zeitraum“, Anhang II Nr. 1.3)', fields: recalculation2 },
    { id: 'M', title: 'Auswahl und Ergebnisse Zeitraum 2', fields: period2 },
    { id: 'N', title: 'Neuberechnung nach Zeitraum 2 („Dritter Zeitraum“, Anhang II Nr. 1.3)', fields: recalculation3 },
    { id: 'O', title: 'Auswahl und Ergebnisse Zeitraum 3', fields: period3 },
    { id: 'P', title: 'Hochrechnung und Genauigkeit', reference: 'Anhang II Nr. 1.3; Art. 8', fields: projection },
  ],
  summary: {
    primary: { cell: 'C35', label: 'Anzuwendender Gesamtumfang', unit: 'Einheiten', reason: 'C29' },
    rows: [
      { cell: 'C107', label: 'Umfang Zeitraum 1 n_1' },
      { cell: 'C108', label: 'Umfang Zeitraum 2 n_2' },
      { cell: 'C109', label: 'Umfang Zeitraum 3 n_3' },
      { cell: 'C128', label: 'Extrapolierter Fehler' },
      { cell: 'C129', label: 'Genauigkeit SE' },
      { cell: 'C136', label: 'Gesamtfehlerquote', strong: true },
      { cell: 'C137', label: 'Obere Fehlergrenze', strong: true },
    ],
    gauge: { threshold: 'C18', rate: 'C136', upper: 'C137' },
  },
}
