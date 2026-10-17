/**
 * Methodendefinition Blatt 11_SRS_2Z_S. Erzeugt mit `scripts/generate-definition.mjs` und von Hand
 * geprüft. Schichtzeilen tragen `columns: STRATA_COLUMNS`: `cell` ist die Zelle der ersten Schicht
 * (Spalte D), `total` die Summenzelle in Spalte C, soweit die Vorlage eine hat. Bezeichnungen
 * (Spalte B) und Fundstellen (Spalte K) entsprechen der Vorlage. Das Blatt hat keine Verknüpfung
 * zu Blatt 02. Die Unterstichproben (Blatt 17) kennen weder Zeiträume noch Schichten; deshalb
 * trägt kein Feld `subsample`.
 */
import type { MethodDefinition } from '../../model/definition'
import { STRATA_COLUMNS } from '../../model/strata'
import { INCREASE_INTERPRETATION } from '../shared/srs'

export const definition: MethodDefinition = {
  sheet: '11_SRS_2Z_S',
  number: '11',
  title: 'Einfaches Zufallsstichprobenverfahren – zwei Stichprobenzeiträume, geschichtet',
  shortTitle: 'Zufallsstichprobe, 2 Zeiträume, geschichtet',
  legalBasis: 'Art. 4; Art. 5 Abs. 1 Buchst. b, Abs. 3 und 5–7; Art. 8; Anhang I; Anhang II Nr. 2.2 (geschichtet) DelVO (EU) 2023/67',
  sections: [
    {
      id: 'H', title: 'Grundgesamtheit Zeitraum 1 und Prognose Zeitraum 2',
      fields: [
        { cell: 'C4', alias: 'programme', kind: 'input', type: 'text', format: '@', label: 'Programm(e) / CCI', hint: 'Art. 3 Abs. 1 und 2 DelVO.' },
        { cell: 'C5', alias: 'accountingYear', kind: 'input', type: 'text', format: '@', label: 'Geschäftsjahr' },
        { cell: 'C6', alias: 'samplingUnit', kind: 'input', type: 'text', format: '@', label: 'Stichprobeneinheit (z. B. Vorhaben, Ausgabenerklärung, Zahlungsantrag)' },
        { cell: 'C7', alias: 'exhaustiveBookValuePeriod1', kind: 'input', type: 'amount', format: '#,##0.00" €"', label: 'Buchwert der umfassenden Schicht Zeitraum 1 (fakultativ) (BV_e)', hint: 'Art. 5 Abs. 3; Art. 2 Nr. 11 DelVO.' },
        { cell: 'C8', alias: 'exhaustiveUnitsPeriod1', kind: 'input', type: 'integer', format: '#,##0', label: 'Anzahl Einheiten der umfassenden Schicht Zeitraum 1 (N_e)' },
        { cell: 'C9', alias: 'exhaustiveHighValueUnitsPeriod1', kind: 'input', type: 'integer', format: '#,##0', label: 'davon hochwertige Einheiten (Anrechnung auf begrenzten Umfang)', hint: 'Art. 5 Abs. 7 UAbs. 3 DelVO.' },
        { cell: 'D11', alias: 'stratumUnitsPeriod1', kind: 'input', type: 'integer', format: '#,##0', columns: STRATA_COLUMNS, total: 'C11', label: 'Anzahl Einheiten Zeitraum 1 (N_h1)' },
        { cell: 'D12', alias: 'stratumBookValuePeriod1', kind: 'input', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, total: 'C12', label: 'Buchwert Zeitraum 1 (BV_h1)' },
        { cell: 'D13', alias: 'forecastStratumUnitsPeriod2', kind: 'input', type: 'integer', format: '#,##0', columns: STRATA_COLUMNS, total: 'C13', label: 'Prognostizierte Anzahl Einheiten Zeitraum 2 (N_h2)' },
        { cell: 'D14', alias: 'forecastStratumBookValuePeriod2', kind: 'input', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, total: 'C14', label: 'Prognostizierter Buchwert Zeitraum 2 (BV_h2)' },
        { cell: 'C15', alias: 'forecastBookValue', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Prognostizierter Buchwert des Geschäftsjahres (inkl. umfassende Schicht Z1) (BV)' },
        { cell: 'C16', alias: 'forecastRandomStratumPopulation', kind: 'formula', type: 'integer', format: '#,##0', label: 'Prognostizierte Anzahl Einheiten der Zufallsschichten (N_1+2)' },
      ],
    },
    {
      id: 'I', title: 'Stichprobenparameter', reference: 'Anhang I',
      fields: [
        { cell: 'C17', alias: 'systemReliability', kind: 'input', type: 'choice', format: '@', list: 'reliability', label: 'Zuverlässigkeit des Verwaltungs- und Kontrollsystems (hoch / mittel / gering)', hint: 'Anh. I Nr. 2: Bewertung unter Berücksichtigung der Systemprüfungen, so dass das kombinierte Sicherheitsniveau hoch ist.' },
        { cell: 'C18', alias: 'confidenceLevel', kind: 'input', type: 'choice', format: '0%', list: 'confidence', label: 'Konfidenzniveau', hint: 'Anh. I Nr. 2: hoch ≥ 60 %, gering ≥ 90 %; Auswahl aus Blatt 01.' },
        { cell: 'C19', alias: 'testType', kind: 'input', type: 'choice', format: '@', list: 'testType', default: 'zweiseitig', label: 'Testart (zweiseitig / einseitig)', hint: 'Anh. I Nr. 3; Art. 2 Nr. 17 und 18 DelVO.' },
        { cell: 'C20', alias: 'zCoefficient', kind: 'formula', type: 'decimal', format: '0.000', label: "Koeffizient z der Normalverteilung (z / z')", hint: 'Anh. I Nr. 3, Tabelle der z-Werte (95 % außerhalb der Tabelle, siehe Blatt 01).' },
        { cell: 'C21', alias: 'checkConfidence', kind: 'formula', type: 'check', label: 'Prüfung Konfidenzniveau gegen Systembewertung', hint: 'Anh. I Nr. 2 legt nur die Eckwerte fest; für „mittel“ ist das Konfidenzniveau fachlich zu begründen.' },
        { cell: 'C22', alias: 'materiality', kind: 'input', type: 'percent', format: '0.00%', default: 0.02, label: 'Wesentlichkeitsschwelle (höchstens 2 %)', hint: 'Anh. I Nr. 1 i. V. m. Anh. XX Nr. 5.9 VO (EU) 2021/1060.' },
        { cell: 'C23', alias: 'checkMateriality', kind: 'formula', type: 'check', label: 'Prüfung Wesentlichkeitsschwelle' },
        { cell: 'C24', alias: 'tolerableError', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Zulässiger Fehler (TE = Wesentlichkeitsschwelle × BV)', hint: 'Anh. II: TE höchstens 2 % der gesamten Ausgaben.' },
        { cell: 'C25', alias: 'anticipatedErrorRate', kind: 'input', type: 'percent', format: '0.00%', label: 'Voraussichtliche Fehlerquote', hint: 'Anh. I Nr. 4: Pilotstichprobe, historische Daten oder fachkundiges Ermessen.' },
        { cell: 'C26', alias: 'anticipatedError', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Voraussichtlicher Fehler (AE = voraussichtliche Fehlerquote × BV)' },
        { cell: 'C27', alias: 'checkTolerableError', kind: 'formula', type: 'check', label: 'Prüfung TE > AE' },
        { cell: 'D29', alias: 'stratumAnticipatedDeviationPeriod1', kind: 'input', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, label: 'Voraussichtliche Standardabweichung der Fehler Zeitraum 1 (σ_eh1)' },
        { cell: 'D30', alias: 'stratumAnticipatedDeviationPeriod2', kind: 'input', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, label: 'Voraussichtliche Standardabweichung der Fehler Zeitraum 2 (σ_eh2)' },
        { cell: 'D31', alias: 'stratumVarianceTerm', kind: 'formula', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, total: 'C31', label: 'Hilfszeile N_h1·σ²_h1 + N_h2·σ²_h2' },
        { cell: 'C32', alias: 'weightedDeviation', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Gewichtete Standardabweichung (σ_ew1+2)' },
        { cell: 'C33', alias: 'recalculationApproach', kind: 'input', type: 'choice', format: '@', list: 'recalculation', default: 'Standard (Art. 5 Abs. 6 Buchst. a)', label: 'Ansatz der Neuberechnung des Stichprobenumfangs', hint: 'Art. 5 Abs. 6 Buchst. a (Standard) bzw. b (global); bei begrenztem Umfang zusätzlich Art. 5 Abs. 7 UAbs. 4 Buchst. a (Erhöhung).' },
      ],
    },
    {
      id: 'J', title: 'Stichprobenumfang „Erster Zeitraum“',
      fields: [
        { cell: 'C34', alias: 'computedSampleSize', kind: 'formula', type: 'integer', format: '#,##0', label: 'Rechnerischer Gesamtumfang (n_1+2)' },
        { cell: 'C35', alias: 'programmeCategory', kind: 'input', type: 'choice', list: 'category', label: 'Kategorie des Programms nach Anh. XI Tabelle 2 VO (EU) 2021/1060 (1–4)', hint: 'Art. 5 Abs. 7 UAbs. 1 DelVO; ErwG 10.' },
        { cell: 'C36', alias: 'article83', kind: 'input', type: 'choice', format: '@', list: 'yesNo', default: 'Nein', label: 'Verbesserte angemessene Regelungen nach Art. 83 VO (EU) 2021/1060 (Ja/Nein)', hint: 'Anh. I Buchst. a DelVO: Stichprobe von 30 Einheiten.' },
        { cell: 'C37', alias: 'applyLimitedSize', kind: 'input', type: 'choice', format: '@', list: 'yesNo', default: 'Nein', label: 'Begrenzten Stichprobenumfang anwenden (Ja/Nein)', hint: 'Art. 5 Abs. 7: Anwendung auf eine Stichprobe für die gesamte Grundgesamtheit (UAbs. 2).' },
        { cell: 'C38', alias: 'checkLimitedSize', kind: 'formula', type: 'check', label: 'Zulässigkeit des begrenzten Stichprobenumfangs' },
        { cell: 'C39', alias: 'limitedSampleSize', kind: 'formula', type: 'integer', format: '#,##0', label: 'Begrenzter Stichprobenumfang (Einheiten) (n_lim)', hint: 'Angerechnet werden alle Einheiten der Zufallsschichten und nur die hochwertigen Einheiten umfassender Schichten (Art. 5 Abs. 7 UAbs. 3).' },
        { cell: 'C40', alias: 'minimumRandomSize', kind: 'formula', type: 'integer', format: '#,##0', label: 'Mindestumfang der Zufallsstichproben' },
        { cell: 'C41', alias: 'limitedSizeNet', kind: 'formula', type: 'integer', format: '#,##0', label: 'Begrenzter Umfang abzüglich hochwertiger Einheiten' },
        { cell: 'C42', alias: 'sampleSize', kind: 'result', type: 'integer', format: '#,##0', label: 'Anzuwendender Gesamtumfang' },
        { cell: 'D44', alias: 'stratumSampleSizePeriod1', kind: 'formula', type: 'integer', format: '#,##0', columns: STRATA_COLUMNS, total: 'C44', label: 'Umfang Zeitraum 1 je Schicht (N_h1/N · n) (n_h1)' },
        { cell: 'D45', alias: 'stratumPlannedSampleSizePeriod2', kind: 'formula', type: 'integer', format: '#,##0', columns: STRATA_COLUMNS, total: 'C45', label: 'Geplanter Umfang Zeitraum 2 je Schicht (n_h2)' },
        { cell: 'D46', alias: 'checkStratumMinimumUnitsPeriod1', kind: 'formula', type: 'check', columns: STRATA_COLUMNS, label: 'Mindestens drei Einheiten je Zufallsschicht (Z1)', hint: 'Art. 5 Abs. 5.' },
      ],
    },
    {
      id: 'K', title: 'Prüfergebnisse Zeitraum 1',
      fields: [
        { cell: 'C47', alias: 'exhaustiveErrorsPeriod1', kind: 'input', type: 'amount', format: '#,##0.00" €"', label: 'Summe der Fehler in der umfassenden Schicht Zeitraum 1 (ΣE_e)' },
        { cell: 'D49', alias: 'stratumSampleBookValueSumPeriod1', kind: 'input', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, total: 'C49', label: 'Summe der Buchwerte der Stichprobe (Σ BV_i)' },
        { cell: 'D50', alias: 'stratumErrorSumPeriod1', kind: 'input', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, total: 'C50', label: 'Summe der Fehler der Stichprobe (Σ E_i)' },
        { cell: 'D51', alias: 'stratumSampleErrorDeviationPeriod1', kind: 'input', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, label: 'Standardabweichung der Fehler (für Neuberechnung) (s_eh)' },
        { cell: 'D52', alias: 'stratumSampleRatioDeviationPeriod1', kind: 'input', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, label: 'Standardabweichung der Variablen q (s_qh)' },
      ],
    },
    {
      id: 'L', title: 'Neuberechnung für Zeitraum 2', reference: 'Art. 5 Abs. 6 und 7',
      fields: [
        { cell: 'C53', alias: 'exhaustiveBookValuePeriod2', kind: 'input', type: 'amount', format: '#,##0.00" €"', label: 'Buchwert der umfassenden Schicht Zeitraum 2 (fakultativ) (BV_e)', hint: 'Art. 5 Abs. 3; Art. 2 Nr. 11 DelVO.' },
        { cell: 'C54', alias: 'exhaustiveUnitsPeriod2', kind: 'input', type: 'integer', format: '#,##0', label: 'Anzahl Einheiten der umfassenden Schicht Zeitraum 2 (N_e)' },
        { cell: 'C55', alias: 'exhaustiveHighValueUnitsPeriod2', kind: 'input', type: 'integer', format: '#,##0', label: 'davon hochwertige Einheiten (Anrechnung auf begrenzten Umfang)', hint: 'Art. 5 Abs. 7 UAbs. 3 DelVO.' },
        { cell: 'D57', alias: 'stratumUnitsPeriod2', kind: 'input', type: 'integer', format: '#,##0', columns: STRATA_COLUMNS, total: 'C57', label: 'Anzahl Einheiten Zeitraum 2 (Ist) (N_h2)' },
        { cell: 'D58', alias: 'stratumBookValuePeriod2', kind: 'input', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, total: 'C58', label: 'Buchwert Zeitraum 2 (Ist) (BV_h2)' },
        { cell: 'D59', alias: 'stratumUpdatedDeviationPeriod2', kind: 'input', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, label: 'Aktualisierte Standardabweichung der Fehler Zeitraum 2 (σ_eh2)' },
        { cell: 'C60', alias: 'updatedAnticipatedErrorRate', kind: 'input', type: 'percent', format: '0.00%', label: 'Aktualisierte voraussichtliche Fehlerquote (leer = Wert aus I)' },
        { cell: 'C61', alias: 'bookValue', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Buchwert des Geschäftsjahres (BV)' },
        { cell: 'C62', alias: 'updatedTolerableError', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Zulässiger Fehler (aktualisiert) (TE)' },
        { cell: 'C63', alias: 'updatedAnticipatedError', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Voraussichtlicher Fehler (aktualisiert) (AE)' },
        { cell: 'D65', alias: 'stratumRecalculationDeviationPeriod1', kind: 'formula', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, label: 'Standardabweichung Zeitraum 1 (s, ersatzweise σ) (s_eh1)' },
        { cell: 'D66', alias: 'stratumStandardVarianceTermPeriod1', kind: 'formula', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, total: 'C66', label: 'Hilfszeile N²_h1/n_h1 · s²_eh1' },
        { cell: 'D67', alias: 'stratumStandardVarianceTermPeriod2', kind: 'formula', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, total: 'C67', label: 'Hilfszeile N_h2 · σ²_eh2' },
        { cell: 'C68', alias: 'standardDenominator', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Nenner (TE − AE)² − z²·Σ N²_h1/n_h1·s²_eh1' },
        { cell: 'C69', alias: 'standardSampleSizePeriod2', kind: 'formula', type: 'integer', format: '#,##0', label: 'Standard: n₂ = z²·N₂·Σ(N_h2·σ²_eh2) / Nenner (n_2)' },
        { cell: 'D70', alias: 'stratumGlobalVarianceTerm', kind: 'formula', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, total: 'C70', label: 'Hilfszeile global: N_h1·s²_eh1 + N_h2·σ²_eh2' },
        { cell: 'C71', alias: 'globalRandomStratumPopulation', kind: 'formula', type: 'integer', format: '#,##0', label: 'Global: Anzahl Einheiten der Zufallsschichten (N)' },
        { cell: 'C72', alias: 'globalComputedSampleSize', kind: 'formula', type: 'integer', format: '#,##0', label: 'Global: rechnerischer Gesamtumfang' },
        { cell: 'C73', alias: 'globalLimitedSizeNet', kind: 'formula', type: 'integer', format: '#,##0', label: 'Global: begrenzter Umfang abzüglich hochwertiger Einheiten' },
        { cell: 'C74', alias: 'globalSampleSize', kind: 'formula', type: 'integer', format: '#,##0', label: 'Global: anzuwendender Gesamtumfang' },
        { cell: 'D76', alias: 'stratumGlobalAdditionalUnitsPeriod1', kind: 'formula', type: 'integer', format: '#,##0', columns: STRATA_COLUMNS, total: 'C76', label: 'Global: Zusatzeinheiten Zeitraum 1' },
        { cell: 'D77', alias: 'stratumSampleSizePeriod2', kind: 'result', type: 'integer', format: '#,##0', columns: STRATA_COLUMNS, total: 'C77', label: 'Anzuwendender Umfang Zeitraum 2 je Schicht (mind. 3) (n_h2)', interpretation: INCREASE_INTERPRETATION },
        { cell: 'D78', alias: 'stratumFinalSampleSizePeriod1', kind: 'formula', type: 'integer', format: '#,##0', columns: STRATA_COLUMNS, total: 'C78', label: 'Endgültiger Umfang Zeitraum 1 je Schicht (n_h1)' },
        { cell: 'D79', alias: 'checkStratumMinimumUnitsPeriod2', kind: 'formula', type: 'check', columns: STRATA_COLUMNS, label: 'Mindestens drei Einheiten je Zufallsschicht (Z2)', hint: 'Art. 5 Abs. 5.' },
        { cell: 'C80', alias: 'totalSampleSize', kind: 'formula', type: 'integer', format: '#,##0', label: 'Gesamtstichprobe des Geschäftsjahres' },
        { cell: 'C81', alias: 'checkMinimumSize', kind: 'formula', type: 'check', label: 'Mindestumfang des Geschäftsjahres' },
      ],
    },
    {
      id: 'M', title: 'Prüfergebnisse Zeitraum 2',
      fields: [
        { cell: 'C82', alias: 'exhaustiveErrorsPeriod2', kind: 'input', type: 'amount', format: '#,##0.00" €"', label: 'Summe der Fehler in der umfassenden Schicht Zeitraum 2 (ΣE_e)' },
        { cell: 'D84', alias: 'stratumSampleBookValueSumPeriod2', kind: 'input', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, total: 'C84', label: 'Summe der Buchwerte der Stichprobe (Σ BV_i)' },
        { cell: 'D85', alias: 'stratumErrorSumPeriod2', kind: 'input', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, total: 'C85', label: 'Summe der Fehler der Stichprobe (Σ E_i)' },
        { cell: 'D86', alias: 'stratumSampleErrorDeviationPeriod2', kind: 'input', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, label: 'Standardabweichung der Fehler (für Neuberechnung) (s_eh)' },
        { cell: 'D87', alias: 'stratumSampleRatioDeviationPeriod2', kind: 'input', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, label: 'Standardabweichung der Variablen q (s_qh)' },
      ],
    },
    {
      id: 'N', title: 'Hochrechnung (Verhältnisschätzung) und Genauigkeit', reference: 'Anhang II Nr. 2.2, geschichtet',
      fields: [
        { cell: 'D89', alias: 'stratumProjectedError', kind: 'formula', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, total: 'C89', label: 'Extrapolierter Fehler je Schicht (Z1 + Z2) (EE_sh)' },
        { cell: 'D90', alias: 'stratumPrecisionTerm', kind: 'formula', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, total: 'C90', label: 'Hilfszeile N²_h1/n_h1·s²_qh1 + N²_h2/n_h2·s²_qh2' },
        { cell: 'C91', alias: 'exhaustiveStratumError', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Fehler der umfassenden Schichten (EE_e)' },
        { cell: 'C92', alias: 'projectedError', kind: 'result', type: 'amount', format: '#,##0.00" €"', label: 'Extrapolierter Fehler EE' },
        { cell: 'C93', alias: 'precision', kind: 'result', type: 'amount', format: '#,##0.00" €"', label: 'Genauigkeit', formula: 'SE = z·√(Σ…)' },
        { cell: 'C94', alias: 'systemicErrors', kind: 'input', type: 'amount', format: '#,##0.00" €"', label: 'Abgegrenzte systembedingte Fehler (Betrag)', hint: 'Art. 2 Nr. 20, 21; Art. 8 Abs. 1 DelVO.' },
        { cell: 'C95', alias: 'anomalousErrors', kind: 'input', type: 'amount', format: '#,##0.00" €"', label: 'Nicht berichtigte anomale Fehler (Betrag)', hint: 'Art. 2 Nr. 20, 21; Art. 8 Abs. 1 DelVO.' },
        { cell: 'C96', alias: 'upperErrorLimit', kind: 'result', type: 'amount', format: '#,##0.00" €"', label: 'Obere Fehlergrenze (EE + SE + systembedingte + nicht berichtigte anomale Fehler)', hint: 'Art. 2 Nr. 20 DelVO.' },
        { cell: 'C97', alias: 'lowerErrorLimit', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Untere Fehlergrenze (EE − SE + systembedingte + nicht berichtigte anomale Fehler)', hint: 'Art. 2 Nr. 21 i. V. m. Nr. 17, 24 DelVO: nur beim zweiseitigen Test.' },
        { cell: 'C98', alias: 'relativePrecision', kind: 'formula', type: 'percent', format: '0.00%', label: 'Relative Genauigkeit (SE / BV)' },
        { cell: 'C99', alias: 'projectedErrorRate', kind: 'formula', type: 'percent', format: '0.00%', label: 'Extrapolierte Zufallsfehlerquote (EE / BV)' },
        { cell: 'C100', alias: 'totalErrorRate', kind: 'result', type: 'percent', format: '0.00%', label: 'Gesamtfehlerquote ((EE + systembedingte + nicht berichtigte anomale Fehler) / BV)', hint: 'Art. 8 Abs. 1 DelVO; endgültige Berechnung inkl. TH-Pauschale und Anh. III in Blatt 18.' },
        { cell: 'C101', alias: 'upperErrorLimitRate', kind: 'result', type: 'percent', format: '0.00%', label: 'Obere Fehlergrenze in % von BV' },
        { cell: 'C102', alias: 'assessment', kind: 'formula', type: 'check', label: 'Würdigung gegen die Wesentlichkeitsschwelle' },
      ],
    },
  ],
  summary: {
    primary: { cell: 'C80', label: 'Gesamtstichprobe des Geschäftsjahres', unit: 'Einheiten', reason: 'C34' },
    rows: [{ cell: 'C78', label: 'Umfang Zeitraum 1 (Summe n_h1)' }, { cell: 'C77', label: 'Umfang Zeitraum 2 (Summe n_h2)' }, { cell: 'C92', label: 'Extrapolierter Fehler' }, { cell: 'C93', label: 'Genauigkeit SE' }, { cell: 'C100', label: 'Gesamtfehlerquote', strong: true }, { cell: 'C101', label: 'Obere Fehlergrenze', strong: true }],
    gauge: { threshold: 'C22', rate: 'C100', upper: 'C101' },
  },
}
