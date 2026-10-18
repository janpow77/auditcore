/**
 * Methodendefinition Blatt 05_MUS_2Z. Erzeugt mit `scripts/generate-definition.mjs`
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
  { cell: 'C7', alias: 'bookValuePeriod1', kind: 'input', type: 'amount', format: EUR, label: 'Buchwert Zeitraum 1 (Ist; positive Einheiten) (BV_1)', hint: 'Art. 4 Abs. 1; Art. 2 Nr. 14 DelVO.' },
  { cell: 'C8', alias: 'plannedBookValuePeriod2', kind: 'input', type: 'amount', format: EUR, label: 'Prognostizierter Buchwert Zeitraum 2 (BV_2)' },
  { cell: 'C9', alias: 'populationSizePeriod1', kind: 'input', type: 'integer', format: INT, label: 'Anzahl Stichprobeneinheiten Zeitraum 1 (N_1)' },
  { cell: 'C10', alias: 'plannedPopulationSizePeriod2', kind: 'input', type: 'integer', format: INT, label: 'Prognostizierte Anzahl Stichprobeneinheiten Zeitraum 2 (N_2)' },
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
  { cell: 'C23', alias: 'anticipatedDeviationPeriod1', kind: 'input', type: 'decimal', format: DEC4, label: 'Voraussichtliche Standardabweichung der Fehlerquoten Zeitraum 1 (σ_r1)', hint: 'Anh. I Nr. 4.' },
  { cell: 'C24', alias: 'anticipatedDeviationPeriod2', kind: 'input', type: 'decimal', format: DEC4, label: 'Voraussichtliche Standardabweichung der Fehlerquoten Zeitraum 2 (σ_r2)', hint: 'Ist keine gesonderte Annäherung möglich, gilt derselbe Wert für alle Zeiträume (Anh. II Nr. 1.2, Anmerkungen).' },
  { cell: 'C25', alias: 'weightedDeviation', kind: 'formula', type: 'decimal', format: DEC4, label: 'Gewichtete Standardabweichung √(BV₁/BV₁₊₂·σ²_r1 + BV₂/BV₁₊₂·σ²_r2) (σ_rw1+2)' },
  { cell: 'C26', alias: 'recalculationApproach', kind: 'input', type: 'choice', format: '@', list: 'recalculation', default: 'Standard (Art. 5 Abs. 6 Buchst. a)', label: 'Ansatz der Neuberechnung des Stichprobenumfangs', hint: 'Art. 5 Abs. 6 Buchst. a (Standard) bzw. b (global); bei begrenztem Umfang zusätzlich Art. 5 Abs. 7 UAbs. 4 Buchst. a (Erhöhung).' },
]

const size: FieldDefinition[] = [
  { cell: 'C27', alias: 'computedSampleSize', kind: 'formula', type: 'integer', format: INT, label: 'Rechnerischer Gesamtumfang n₁₊₂ = (z·BV₁₊₂·σ_rw / (TE − AE))² (n_1+2)', interpretation: ROUNDING_INTERPRETATION },
  { cell: 'C28', alias: 'programmeCategory', kind: 'input', type: 'choice', list: 'category', label: 'Kategorie des Programms nach Anh. XI Tabelle 2 VO (EU) 2021/1060 (1–4)', hint: 'Art. 5 Abs. 7 UAbs. 1 DelVO; ErwG 10.' },
  { cell: 'C29', alias: 'article83', kind: 'input', type: 'choice', format: '@', list: 'yesNo', default: 'Nein', label: 'Verbesserte angemessene Regelungen nach Art. 83 VO (EU) 2021/1060 (Ja/Nein)', hint: 'Anh. I Buchst. a DelVO: Stichprobe von 30 Einheiten.' },
  { cell: 'C30', alias: 'applyLimitedSize', kind: 'input', type: 'choice', format: '@', list: 'yesNo', default: 'Nein', label: 'Begrenzten Stichprobenumfang anwenden (Ja/Nein)', hint: 'Art. 5 Abs. 7: Anwendung auf eine Stichprobe für die gesamte Grundgesamtheit (UAbs. 2).' },
  { cell: 'C31', alias: 'checkLimitedSize', kind: 'formula', type: 'check', label: 'Zulässigkeit des begrenzten Stichprobenumfangs' },
  { cell: 'C32', alias: 'limitedSampleSize', kind: 'formula', type: 'integer', format: INT, label: 'Begrenzter Stichprobenumfang (Einheiten) (n_lim)', hint: 'Angerechnet werden alle Einheiten der Zufallsschichten und nur die hochwertigen Einheiten umfassender Schichten (Art. 5 Abs. 7 UAbs. 3).' },
  { cell: 'C33', alias: 'sampleSize', kind: 'result', type: 'integer', format: INT, label: 'Anzuwendender Gesamtumfang (mind. 30; ggf. begrenzt) (n_1+2)' },
  { cell: 'C34', alias: 'sampleSizePeriod1', kind: 'result', type: 'integer', format: INT, label: 'Stichprobenumfang Zeitraum 1 (BV₁/BV₁₊₂ · n₁₊₂) (n_1)' },
  { cell: 'C35', alias: 'plannedSampleSizePeriod2', kind: 'formula', type: 'integer', format: INT, label: 'Geplanter Stichprobenumfang Zeitraum 2 (BV₂/BV₁₊₂ · n₁₊₂) (n_2)' },
]

const selection1: FieldDefinition[] = [
  { cell: 'C36', alias: 'cutOffPeriod1', kind: 'formula', type: 'amount', format: EUR, label: 'Grenzwert für hochwertige Einheiten (BV1/n1) (BV/n)', hint: 'Art. 5 Abs. 2 UAbs. 2: hochwertige Einheiten über dem Auswahlintervall werden vollständig geprüft.' },
  { cell: 'C37', alias: 'highValueUnitsPeriod1', kind: 'input', type: 'integer', format: INT, label: 'Anzahl hochwertiger Einheiten (BV > Grenzwert) (n_e)' },
  { cell: 'C38', alias: 'highValueBookValuePeriod1', kind: 'input', type: 'amount', format: EUR, label: 'Buchwert der hochwertigen Einheiten (BV_e)' },
  { cell: 'C39', alias: 'randomStratumBookValuePeriod1', kind: 'formula', type: 'amount', format: EUR, label: 'Buchwert der Zufallsschicht (niedrigwertige Einheiten) (BV_s)' },
  { cell: 'C40', alias: 'randomStratumUnitsPeriod1', kind: 'formula', type: 'integer', format: INT, label: 'Anzahl der in der Zufallsschicht auszuwählenden Einheiten (n_s)', interpretation: HIGH_VALUE_INTERPRETATION },
  { cell: 'C41', alias: 'checkMinimumUnitsPeriod1', kind: 'formula', type: 'check', label: 'Mindestens drei Einheiten in der Zufallsschicht' },
  { cell: 'C42', alias: 'samplingIntervalPeriod1', kind: 'formula', type: 'amount', format: EUR, label: 'Auswahlintervall (BV_s / n_s) (SI)', hint: 'Art. 2 Nr. 9; Art. 5 Abs. 2 UAbs. 2 DelVO.' },
  { cell: 'C43', alias: 'iterationUnitsPeriod1', kind: 'input', type: 'integer', format: INT, label: 'Einheiten der Zufallsschicht mit BV > Auswahlintervall (Iteration)', hint: 'Solche Einheiten sind der hochwertigen Schicht zuzuordnen; Grenzwert und Intervall sind neu zu berechnen.' },
  { cell: 'C44', alias: 'checkIterationPeriod1', kind: 'formula', type: 'check', label: 'Prüfung Iteration' },
]

const findings1: FieldDefinition[] = [
  { cell: 'C45', alias: 'highValueErrorsPeriod1', kind: 'input', type: 'amount', format: EUR, label: 'Summe der Fehler in den hochwertigen Einheiten (ΣE_e)', hint: 'Bei Unterstichproben: auf die Stichprobeneinheit hochgerechneter Fehler (Art. 8 Abs. 3; Blatt 17).' },
  { cell: 'C46', alias: 'errorRateSumPeriod1', kind: 'input', type: 'decimal', format: DEC4, label: 'Summe der Fehlerquoten der Stichprobe der Zufallsschicht (Σ E_i/BV_i)' },
  { cell: 'C47', alias: 'sampleDeviationPeriod1', kind: 'input', type: 'decimal', format: DEC4, label: 'Standardabweichung der Fehlerquoten in der Stichprobe der Zufallsschicht (s_r)', hint: 'Aus derselben Stichprobe wie die Hochrechnung (Anh. II Nr. 1).' },
]

const recalculation: FieldDefinition[] = [
  { cell: 'C48', alias: 'bookValuePeriod2', kind: 'input', type: 'amount', format: EUR, label: 'Buchwert Zeitraum 2 (Ist) (BV_2)' },
  { cell: 'C49', alias: 'populationSizePeriod2', kind: 'input', type: 'integer', format: INT, label: 'Anzahl Stichprobeneinheiten Zeitraum 2 (Ist) (N_2)' },
  { cell: 'C50', alias: 'updatedDeviationPeriod2', kind: 'input', type: 'decimal', format: DEC4, label: 'Aktualisierte voraussichtliche Standardabweichung der Fehlerquoten Zeitraum 2 (σ_r2)' },
  { cell: 'C51', alias: 'updatedAnticipatedErrorRate', kind: 'input', type: 'percent', format: RATE, label: 'Aktualisierte voraussichtliche Fehlerquote (leer = Wert aus I)' },
  { cell: 'C52', alias: 'bookValue', kind: 'formula', type: 'amount', format: EUR, label: 'Buchwert des Geschäftsjahres (BV₁ + BV₂)' },
  { cell: 'C53', alias: 'updatedTolerableError', kind: 'formula', type: 'amount', format: EUR, label: 'Zulässiger Fehler (aktualisiert) (TE)' },
  { cell: 'C54', alias: 'updatedAnticipatedError', kind: 'formula', type: 'amount', format: EUR, label: 'Voraussichtlicher Fehler (aktualisiert) (AE)' },
  { cell: 'C55', alias: 'recalculationDeviationPeriod1', kind: 'formula', type: 'decimal', format: DEC4, label: 'Standardabweichung Zeitraum 1 für die Neuberechnung (s, ersatzweise σ) (s_r1)', hint: 'Anh. II Nr. 1.2, Anmerkungen: Ist s nicht verfügbar, kann es durch σ ersetzt werden.' },
  { cell: 'C56', alias: 'standardDenominator', kind: 'formula', type: 'amount', format: EUR, label: 'Nenner (TE − AE)² − z²·BV₁²/n₁·s²_r1' },
  { cell: 'C57', alias: 'standardSampleSizePeriod2', kind: 'formula', type: 'integer', format: INT, label: 'Standardneuberechnung n₂ = (z·BV₂·σ_r2)² / Nenner (n_2)', hint: 'Anh. II Nr. 1.2: bei negativem Ergebnis ist der Standardansatz nicht anwendbar.' },
  { cell: 'C58', alias: 'globalWeightedDeviation', kind: 'formula', type: 'decimal', format: DEC4, label: 'Global: gewichtete Standardabweichung mit aktualisierten Werten (σ_rw)' },
  { cell: 'C59', alias: 'globalComputedSampleSize', kind: 'formula', type: 'integer', format: INT, label: 'Global: rechnerischer Gesamtumfang' },
  { cell: 'C60', alias: 'globalSampleSize', kind: 'formula', type: 'integer', format: INT, label: 'Global: anzuwendender Gesamtumfang (mind. 30; ggf. begrenzt)' },
  { cell: 'C61', alias: 'globalSampleSizePeriod1', kind: 'formula', type: 'integer', format: INT, label: 'Global: neu berechneter Umfang Zeitraum 1 (n_1)' },
  { cell: 'C62', alias: 'globalAdditionalUnitsPeriod1', kind: 'formula', type: 'integer', format: INT, label: 'Global: zusätzlich in Zeitraum 1 auszuwählende Einheiten', hint: 'Bereits geprüfte Einheiten bleiben erhalten; Zusatzauswahl aus der Zufallsschicht von Zeitraum 1.' },
  { cell: 'C63', alias: 'globalSampleSizePeriod2', kind: 'formula', type: 'integer', format: INT, label: 'Global: Stichprobenumfang Zeitraum 2 (n_2)' },
  { cell: 'C64', alias: 'underestimationFactor', kind: 'formula', type: 'decimal', format: DEC4, label: 'Begrenzter Umfang: Faktor der Unterschätzung max(BV₂/BV₂ᵖ; N₂/N₂ᵖ; 1)', interpretation: INCREASE_INTERPRETATION },
  { cell: 'C65', alias: 'increasedSampleSizePeriod2', kind: 'formula', type: 'integer', format: INT, label: 'Begrenzter Umfang: erhöhter Stichprobenumfang Zeitraum 2 (n_2)', hint: 'Art. 5 Abs. 7 UAbs. 4 Buchst. a; proportionale Erhöhung als Vorschlag, die DelVO legt die Rechenweise nicht fest.', interpretation: INCREASE_INTERPRETATION },
  { cell: 'C66', alias: 'finalSampleSizePeriod1', kind: 'formula', type: 'integer', format: INT, label: 'Endgültiger Stichprobenumfang Zeitraum 1 (n_1)' },
  { cell: 'C67', alias: 'sampleSizePeriod2', kind: 'result', type: 'integer', format: INT, label: 'Anzuwendender Stichprobenumfang Zeitraum 2 (mind. 3 und Auffüllung auf 30 Einheiten im Geschäftsjahr) (n_2)', hint: 'Art. 5 Abs. 5: Untergrenzen werden auch bei der Neuberechnung eingehalten.' },
  { cell: 'C68', alias: 'checkLimitedSizeKept', kind: 'formula', type: 'check', label: 'Einhaltung des begrenzten Stichprobenumfangs' },
  { cell: 'C69', alias: 'checkMinimumSize', kind: 'formula', type: 'check', label: 'Mindestumfang des Geschäftsjahres' },
]

const selection2: FieldDefinition[] = [
  { cell: 'C70', alias: 'cutOffPeriod2', kind: 'formula', type: 'amount', format: EUR, label: 'Grenzwert für hochwertige Einheiten (BV2/n2) (BV/n)', hint: 'Art. 5 Abs. 2 UAbs. 2: hochwertige Einheiten über dem Auswahlintervall werden vollständig geprüft.' },
  { cell: 'C71', alias: 'highValueUnitsPeriod2', kind: 'input', type: 'integer', format: INT, label: 'Anzahl hochwertiger Einheiten (BV > Grenzwert) (n_e)' },
  { cell: 'C72', alias: 'highValueBookValuePeriod2', kind: 'input', type: 'amount', format: EUR, label: 'Buchwert der hochwertigen Einheiten (BV_e)' },
  { cell: 'C73', alias: 'randomStratumBookValuePeriod2', kind: 'formula', type: 'amount', format: EUR, label: 'Buchwert der Zufallsschicht (niedrigwertige Einheiten) (BV_s)' },
  { cell: 'C74', alias: 'randomStratumUnitsPeriod2', kind: 'formula', type: 'integer', format: INT, label: 'Anzahl der in der Zufallsschicht auszuwählenden Einheiten (n_s)' },
  { cell: 'C75', alias: 'checkMinimumUnitsPeriod2', kind: 'formula', type: 'check', label: 'Mindestens drei Einheiten in der Zufallsschicht' },
  { cell: 'C76', alias: 'samplingIntervalPeriod2', kind: 'formula', type: 'amount', format: EUR, label: 'Auswahlintervall (BV_s / n_s) (SI)', hint: 'Art. 2 Nr. 9; Art. 5 Abs. 2 UAbs. 2 DelVO.' },
  { cell: 'C77', alias: 'iterationUnitsPeriod2', kind: 'input', type: 'integer', format: INT, label: 'Einheiten der Zufallsschicht mit BV > Auswahlintervall (Iteration)', hint: 'Solche Einheiten sind der hochwertigen Schicht zuzuordnen; Grenzwert und Intervall sind neu zu berechnen.' },
  { cell: 'C78', alias: 'checkIterationPeriod2', kind: 'formula', type: 'check', label: 'Prüfung Iteration' },
  { cell: 'C79', alias: 'finalRandomUnitsPeriod1', kind: 'formula', type: 'integer', format: INT, label: 'Endgültige Zufallseinheiten Zeitraum 1 (inkl. globaler Ergänzung) (n_1s)', hint: 'Bei Ergänzung im globalen Ansatz Grenzwert und Ergebnisse von Zeitraum 1 entsprechend fortschreiben.' },
]

const findings2: FieldDefinition[] = [
  { cell: 'C80', alias: 'highValueErrorsPeriod2', kind: 'input', type: 'amount', format: EUR, label: 'Summe der Fehler in den hochwertigen Einheiten (ΣE_e)', hint: 'Bei Unterstichproben: auf die Stichprobeneinheit hochgerechneter Fehler (Art. 8 Abs. 3; Blatt 17).' },
  { cell: 'C81', alias: 'errorRateSumPeriod2', kind: 'input', type: 'decimal', format: DEC4, label: 'Summe der Fehlerquoten der Stichprobe der Zufallsschicht (Σ E_i/BV_i)' },
  { cell: 'C82', alias: 'sampleDeviationPeriod2', kind: 'input', type: 'decimal', format: DEC4, label: 'Standardabweichung der Fehlerquoten in der Stichprobe der Zufallsschicht (s_r)', hint: 'Aus derselben Stichprobe wie die Hochrechnung (Anh. II Nr. 1).' },
]

const projection: FieldDefinition[] = [
  { cell: 'C83', alias: 'exhaustiveStratumError', kind: 'formula', type: 'amount', format: EUR, label: 'Fehler der umfassenden Schichten (Σ E₁ + Σ E₂) (EE_e)' },
  { cell: 'C84', alias: 'randomStratumError', kind: 'formula', type: 'amount', format: EUR, label: 'Extrapolierter Fehler der Zufallsschichten (EE_s)' },
  { cell: 'C85', alias: 'projectedError', kind: 'result', type: 'amount', format: EUR, label: 'Extrapolierter Fehler EE = EE_e + EE_s' },
  { cell: 'C86', alias: 'precision', kind: 'result', type: 'amount', format: EUR, label: 'Genauigkeit SE = z·√(BV²₁s/n₁s·s²_r1 + BV²₂s/n₂s·s²_r2)' },
  { cell: 'C87', alias: 'systemicErrors', kind: 'input', type: 'amount', format: EUR, label: 'Abgegrenzte systembedingte Fehler (Betrag)', hint: 'Art. 2 Nr. 20, 21; Art. 8 Abs. 1 DelVO.' },
  { cell: 'C88', alias: 'anomalousErrors', kind: 'input', type: 'amount', format: EUR, label: 'Nicht berichtigte anomale Fehler (Betrag)', hint: 'Art. 2 Nr. 20, 21; Art. 8 Abs. 1 DelVO.' },
  { cell: 'C89', alias: 'upperErrorLimit', kind: 'result', type: 'amount', format: EUR, label: 'Obere Fehlergrenze (EE + SE + systembedingte + nicht berichtigte anomale Fehler)', hint: 'Art. 2 Nr. 20 DelVO.' },
  { cell: 'C90', alias: 'lowerErrorLimit', kind: 'formula', type: 'amount', format: EUR, label: 'Untere Fehlergrenze (EE − SE + systembedingte + nicht berichtigte anomale Fehler)', hint: 'Art. 2 Nr. 21 i. V. m. Nr. 17, 24 DelVO: nur beim zweiseitigen Test.' },
  { cell: 'C91', alias: 'relativePrecision', kind: 'formula', type: 'percent', format: RATE, label: 'Relative Genauigkeit (SE / BV)' },
  { cell: 'C92', alias: 'projectedErrorRate', kind: 'formula', type: 'percent', format: RATE, label: 'Extrapolierte Zufallsfehlerquote (EE / BV)' },
  { cell: 'C93', alias: 'totalErrorRate', kind: 'result', type: 'percent', format: RATE, label: 'Gesamtfehlerquote ((EE + systembedingte + nicht berichtigte anomale Fehler) / BV)', hint: 'Art. 8 Abs. 1 DelVO; endgültige Berechnung inkl. TH-Pauschale und Anh. III in Blatt 18.' },
  { cell: 'C94', alias: 'upperErrorLimitRate', kind: 'result', type: 'percent', format: RATE, label: 'Obere Fehlergrenze in % von BV' },
  { cell: 'C95', alias: 'assessment', kind: 'formula', type: 'check', label: 'Würdigung gegen die Signifikanzschwelle', interpretation: UPPER_LIMIT_INTERPRETATION },
]

export const definition: MethodDefinition = {
  sheet: '05_MUS_2Z',
  number: '05',
  title: 'MUS-Standardansatz – zwei Stichprobenzeiträume, nicht geschichtet',
  shortTitle: 'MUS, 2 Zeiträume',
  legalBasis: 'Art. 4 Abs. 1; Art. 5 Abs. 1 Buchst. a, Abs. 5–7; Art. 8; Anhang I; Anhang II Nr. 1.2 DelVO (EU) 2023/67',
  sections: [
    { id: 'H', title: 'Grundgesamtheit und Prognose (Beginn Geschäftsjahr / Ende Zeitraum 1)', fields: population },
    { id: 'I', title: 'Stichprobenparameter', reference: 'Anhang I', fields: parameters },
    { id: 'J', title: 'Stichprobenumfang „Erster Zeitraum“', reference: 'Anhang II Nr. 1.2', fields: size },
    { id: 'K', title: 'Auswahl Zeitraum 1 (PPS)', fields: selection1 },
    { id: 'L', title: 'Prüfergebnisse Zeitraum 1', fields: findings1 },
    { id: 'M', title: 'Neuberechnung für Zeitraum 2', reference: 'Art. 5 Abs. 6 und 7; Anhang II Nr. 1.2', fields: recalculation },
    { id: 'N', title: 'Auswahl Zeitraum 2 (PPS)', fields: selection2 },
    { id: 'O', title: 'Prüfergebnisse Zeitraum 2', fields: findings2 },
    { id: 'P', title: 'Hochrechnung und Genauigkeit', reference: 'Anhang II Nr. 1.2; Art. 8', fields: projection },
  ],
  summary: {
    primary: { cell: 'C33', label: 'Anzuwendender Gesamtumfang', unit: 'Einheiten', reason: 'C27' },
    rows: [
      { cell: 'C66', label: 'Umfang Zeitraum 1 n_1' },
      { cell: 'C67', label: 'Umfang Zeitraum 2 n_2' },
      { cell: 'C85', label: 'Extrapolierter Fehler' },
      { cell: 'C86', label: 'Genauigkeit SE' },
      { cell: 'C93', label: 'Gesamtfehlerquote', strong: true },
      { cell: 'C94', label: 'Obere Fehlergrenze', strong: true },
    ],
    gauge: { threshold: 'C17', rate: 'C93', upper: 'C94' },
  },
}
