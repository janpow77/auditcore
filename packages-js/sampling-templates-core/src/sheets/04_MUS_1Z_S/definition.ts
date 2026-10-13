/**
 * Methodendefinition Blatt 04_MUS_1Z_S. Erzeugt mit `scripts/generate-definition.mjs`
 * und von Hand geprüft. Schichtzeilen tragen `columns: STRATA_COLUMNS`: `cell` ist die
 * Zelle der ersten Schicht (Spalte D), `total` die Summenzelle in Spalte C, soweit die
 * Vorlage eine hat. Fundstellen stehen in diesem Blatt in Spalte K.
 */
import type { MethodDefinition } from '../../model/definition'
import { STRATA_COLUMNS } from '../../model/strata'

export const definition: MethodDefinition = {
  sheet: '04_MUS_1Z_S',
  number: '04',
  title: 'MUS-Standardansatz – ein Stichprobenzeitraum, geschichtet',
  shortTitle: 'MUS, 1 Zeitraum, geschichtet',
  legalBasis: 'Art. 4 Abs. 2 und 3; Art. 5 Abs. 1 Buchst. a, Abs. 2, 4, 5 und 7; Art. 8; Anhang I; Anhang II Nr. 1.1 DelVO (EU) 2023/67',
  sections: [
    {
      id: 'H', title: 'Zu prüfende Grundgesamtheit', reference: 'Art. 3, Art. 4 Abs. 2',
      fields: [
        { cell: 'C4', alias: 'programme', kind: 'input', type: 'text', format: '@', label: 'Programm(e) / CCI', hint: 'Art. 3 Abs. 1 und 2 DelVO.' },
        { cell: 'C5', alias: 'accountingYear', kind: 'input', type: 'text', format: '@', label: 'Geschäftsjahr' },
        { cell: 'C6', alias: 'samplingUnit', kind: 'input', type: 'text', format: '@', label: 'Stichprobeneinheit (z. B. Vorhaben, Ausgabenerklärung, Zahlungsantrag)' },
        { cell: 'C7', alias: 'stratificationCriterion', kind: 'input', type: 'text', format: '@', label: 'Schichtungskriterium (z. B. Programm, Fonds, zwischengeschaltete Stelle, Risiko)', hint: 'Art. 4 Abs. 2 DelVO.' },
        { cell: 'D9', alias: 'stratumBookValue', kind: 'input', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, total: 'C9', label: 'Buchwert je Schicht (BV_h)', hint: 'Summe = angepasste Grundgesamtheit (Abgleich mit Blatt 02 unten).' },
        { cell: 'D10', alias: 'stratumUnits', kind: 'input', type: 'integer', format: '#,##0', columns: STRATA_COLUMNS, total: 'C10', label: 'Anzahl Stichprobeneinheiten je Schicht (N_h)' },
        { cell: 'C11', alias: 'populationDifference', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Abweichung zur angepassten Grundgesamtheit in Blatt 02' },
      ],
    },
    {
      id: 'I', title: 'Stichprobenparameter', reference: 'Anhang I',
      fields: [
        { cell: 'C12', alias: 'systemReliability', kind: 'input', type: 'choice', format: '@', list: 'reliability', label: 'Zuverlässigkeit des Verwaltungs- und Kontrollsystems (hoch / mittel / gering)', hint: 'Anh. I Nr. 2: Bewertung unter Berücksichtigung der Systemprüfungen, so dass das kombinierte Sicherheitsniveau hoch ist.' },
        { cell: 'C13', alias: 'confidenceLevel', kind: 'input', type: 'choice', format: '0%', list: 'confidence', label: 'Konfidenzniveau', hint: 'Anh. I Nr. 2: hoch ≥ 60 %, gering ≥ 90 %; Auswahl aus Blatt 01.' },
        { cell: 'C14', alias: 'testType', kind: 'input', type: 'choice', format: '@', list: 'testType', default: 'zweiseitig', label: 'Testart (zweiseitig / einseitig)', hint: 'Anh. I Nr. 3; Art. 2 Nr. 17 und 18 DelVO.' },
        { cell: 'C15', alias: 'zCoefficient', kind: 'formula', type: 'decimal', format: '0.000', label: "Koeffizient z der Normalverteilung (z / z')", hint: 'Anh. I Nr. 3, Tabelle der z-Werte (95 % außerhalb der Tabelle, siehe Blatt 01).' },
        { cell: 'C16', alias: 'checkConfidence', kind: 'formula', type: 'check', label: 'Prüfung Konfidenzniveau gegen Systembewertung', hint: 'Anh. I Nr. 2 legt nur die Eckwerte fest; für „mittel“ ist das Konfidenzniveau fachlich zu begründen.' },
        { cell: 'C17', alias: 'materiality', kind: 'input', type: 'percent', format: '0.00%', default: 0.02, label: 'Wesentlichkeitsschwelle (höchstens 2 %)', hint: 'Anh. I Nr. 1 i. V. m. Anh. XX Nr. 5.9 VO (EU) 2021/1060.' },
        { cell: 'C18', alias: 'checkMateriality', kind: 'formula', type: 'check', label: 'Prüfung Wesentlichkeitsschwelle' },
        { cell: 'C19', alias: 'tolerableError', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Zulässiger Fehler (TE = Wesentlichkeitsschwelle × BV)', hint: 'Anh. II: TE höchstens 2 % der gesamten Ausgaben.' },
        { cell: 'C20', alias: 'anticipatedErrorRate', kind: 'input', type: 'percent', format: '0.00%', label: 'Voraussichtliche Fehlerquote', hint: 'Anh. I Nr. 4: Pilotstichprobe, historische Daten oder fachkundiges Ermessen.' },
        { cell: 'C21', alias: 'anticipatedError', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Voraussichtlicher Fehler (AE = voraussichtliche Fehlerquote × BV)' },
        { cell: 'C22', alias: 'checkTolerableError', kind: 'formula', type: 'check', label: 'Prüfung TE > AE' },
        { cell: 'D24', alias: 'stratumAnticipatedDeviation', kind: 'input', type: 'decimal', format: '0.0000', columns: STRATA_COLUMNS, label: 'Voraussichtliche Standardabweichung der Fehlerquoten je Schicht (σ_rh)', hint: 'Anh. I Nr. 4.' },
        { cell: 'D25', alias: 'stratumVarianceTerm', kind: 'formula', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, total: 'C25', label: 'Hilfszeile BV_h · σ²_rh' },
        { cell: 'C26', alias: 'weightedDeviation', kind: 'formula', type: 'decimal', format: '0.0000', label: 'Gewichtete Standardabweichung √(Σ BV_h/BV · σ²_rh) (σ_rw)', hint: 'Anh. II Nr. 1.1, geschichtet.' },
      ],
    },
    {
      id: 'J', title: 'Stichprobenumfang', reference: 'Anhang II Nr. 1.1; Art. 5 Abs. 5 und 7',
      fields: [
        { cell: 'C27', alias: 'computedSampleSize', kind: 'formula', type: 'integer', format: '#,##0', label: 'Rechnerischer Stichprobenumfang', formula: 'n = (z · BV · σ_rw / (TE − AE))²' },
        { cell: 'C28', alias: 'programmeCategory', kind: 'input', type: 'choice', list: 'category', label: 'Kategorie des Programms nach Anh. XI Tabelle 2 VO (EU) 2021/1060 (1–4)', hint: 'Art. 5 Abs. 7 UAbs. 1 DelVO; ErwG 10.' },
        { cell: 'C29', alias: 'article83', kind: 'input', type: 'choice', format: '@', list: 'yesNo', default: 'Nein', label: 'Verbesserte angemessene Regelungen nach Art. 83 VO (EU) 2021/1060 (Ja/Nein)', hint: 'Anh. I Buchst. a DelVO: Stichprobe von 30 Einheiten.' },
        { cell: 'C30', alias: 'applyLimitedSize', kind: 'input', type: 'choice', format: '@', list: 'yesNo', default: 'Nein', label: 'Begrenzten Stichprobenumfang anwenden (Ja/Nein)', hint: 'Art. 5 Abs. 7: Anwendung auf eine Stichprobe für die gesamte Grundgesamtheit (UAbs. 2).' },
        { cell: 'C31', alias: 'checkLimitedSize', kind: 'formula', type: 'check', label: 'Zulässigkeit des begrenzten Stichprobenumfangs' },
        { cell: 'C32', alias: 'limitedSampleSize', kind: 'formula', type: 'integer', format: '#,##0', label: 'Begrenzter Stichprobenumfang (Einheiten) (n_lim)', hint: 'Angerechnet werden alle Einheiten der Zufallsschichten und nur die hochwertigen Einheiten umfassender Schichten (Art. 5 Abs. 7 UAbs. 3).' },
        { cell: 'C33', alias: 'sampleSize', kind: 'result', type: 'integer', format: '#,##0', label: 'Anzuwendender Stichprobenumfang (mind. 30; ggf. begrenzt)', hint: 'Art. 5 Abs. 5 und 7.' },
      ],
    },
    {
      id: 'K', title: 'Stichprobenauswahl je Schicht (PPS)',
      fields: [
        { cell: 'D35', alias: 'stratumSampleSize', kind: 'formula', type: 'integer', format: '#,##0', columns: STRATA_COLUMNS, total: 'C35', label: 'Stichprobenumfang je Schicht (aufgerundet)', formula: 'n_h = BV_h/BV · n', hint: 'Aufrundung je Schicht kann die Summe über n heben; bei begrenztem Umfang ggf. manuell anpassen.' },
        { cell: 'D36', alias: 'stratumCutOff', kind: 'formula', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, label: 'Grenzwert je Schicht (BV_h/n_h)' },
        { cell: 'D37', alias: 'stratumHighValueUnits', kind: 'input', type: 'integer', format: '#,##0', columns: STRATA_COLUMNS, total: 'C37', label: 'Anzahl hochwertiger Einheiten je Schicht (n_eh)' },
        { cell: 'D38', alias: 'stratumHighValueBookValue', kind: 'input', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, total: 'C38', label: 'Buchwert der hochwertigen Einheiten je Schicht (BV_eh)' },
        { cell: 'D39', alias: 'stratumRandomBookValue', kind: 'formula', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, total: 'C39', label: 'Buchwert der Zufallsschicht je Schicht (BV_hs)' },
        { cell: 'D40', alias: 'stratumRandomUnits', kind: 'formula', type: 'integer', format: '#,##0', columns: STRATA_COLUMNS, total: 'C40', label: 'In der Zufallsschicht auszuwählende Einheiten (n_hs)' },
        { cell: 'D41', alias: 'checkStratumMinimumUnits', kind: 'formula', type: 'check', columns: STRATA_COLUMNS, label: 'Mindestens drei Einheiten je Zufallsschicht', hint: 'Art. 5 Abs. 5 DelVO.' },
        { cell: 'D42', alias: 'stratumSamplingInterval', kind: 'formula', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, label: 'Auswahlintervall je Schicht (BV_hs / n_hs) (SI_h)' },
        { cell: 'D43', alias: 'stratumIterationUnits', kind: 'input', type: 'integer', format: '#,##0', columns: STRATA_COLUMNS, total: 'C43', label: 'Einheiten mit BV > Auswahlintervall (Iteration)', hint: 'Gegebenenfalls umgliedern und neu berechnen.' },
      ],
    },
    {
      id: 'L', title: 'Prüfergebnisse je Schicht',
      fields: [
        { cell: 'D45', alias: 'stratumHighValueErrors', kind: 'input', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, total: 'C45', label: 'Summe der Fehler in hochwertigen Einheiten (ΣE_eh)' },
        { cell: 'D46', alias: 'stratumErrorRateSum', kind: 'input', type: 'decimal', format: '0.0000', columns: STRATA_COLUMNS, total: 'C46', label: 'Summe der Fehlerquoten der Zufallsschicht (Σ E/BV)' },
        { cell: 'D47', alias: 'stratumSampleDeviation', kind: 'input', type: 'decimal', format: '0.0000', columns: STRATA_COLUMNS, label: 'Standardabweichung der Fehlerquoten der Zufallsschicht (s_rh)' },
      ],
    },
    {
      id: 'M', title: 'Hochrechnung und Genauigkeit', reference: 'Anhang II Nr. 1.1; Art. 8',
      fields: [
        { cell: 'D49', alias: 'stratumExhaustiveError', kind: 'formula', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, total: 'C49', label: 'Fehler der umfassenden Schicht (EE_eh)' },
        { cell: 'D50', alias: 'stratumRandomError', kind: 'formula', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, total: 'C50', label: 'Extrapolierter Fehler der Zufallsschicht (BV_hs/n_hs · Σ E/BV) (EE_sh)' },
        { cell: 'D51', alias: 'stratumProjectedError', kind: 'formula', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, total: 'C51', label: 'Extrapolierter Fehler je Schicht (EE_h)' },
        { cell: 'D52', alias: 'stratumPrecisionTerm', kind: 'formula', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, total: 'C52', label: 'Hilfszeile BV²_hs / n_hs · s²_rh' },
        { cell: 'C53', alias: 'projectedError', kind: 'result', type: 'amount', format: '#,##0.00" €"', label: 'Extrapolierter Fehler', formula: 'EE = EE_e + EE_s' },
        { cell: 'C54', alias: 'precision', kind: 'result', type: 'amount', format: '#,##0.00" €"', label: 'Genauigkeit der Stichprobe', formula: 'SE = z · √(Σ BV²_hs/n_hs · s²_rh)' },
        { cell: 'C55', alias: 'systemicErrors', kind: 'input', type: 'amount', format: '#,##0.00" €"', label: 'Abgegrenzte systembedingte Fehler (Betrag)', hint: 'Art. 2 Nr. 20, 21; Art. 8 Abs. 1 DelVO.' },
        { cell: 'C56', alias: 'anomalousErrors', kind: 'input', type: 'amount', format: '#,##0.00" €"', label: 'Nicht berichtigte anomale Fehler (Betrag)', hint: 'Art. 2 Nr. 20, 21; Art. 8 Abs. 1 DelVO.' },
        { cell: 'C57', alias: 'upperErrorLimit', kind: 'result', type: 'amount', format: '#,##0.00" €"', label: 'Obere Fehlergrenze (EE + SE + systembedingte + nicht berichtigte anomale Fehler)', hint: 'Art. 2 Nr. 20 DelVO.' },
        { cell: 'C58', alias: 'lowerErrorLimit', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Untere Fehlergrenze (EE − SE + systembedingte + nicht berichtigte anomale Fehler)', hint: 'Art. 2 Nr. 21 i. V. m. Nr. 17, 24 DelVO: nur beim zweiseitigen Test.' },
        { cell: 'C59', alias: 'relativePrecision', kind: 'formula', type: 'percent', format: '0.00%', label: 'Relative Genauigkeit (SE / BV)' },
        { cell: 'C60', alias: 'projectedErrorRate', kind: 'formula', type: 'percent', format: '0.00%', label: 'Extrapolierte Zufallsfehlerquote (EE / BV)' },
        { cell: 'C61', alias: 'totalErrorRate', kind: 'result', type: 'percent', format: '0.00%', label: 'Gesamtfehlerquote ((EE + systembedingte + nicht berichtigte anomale Fehler) / BV)', hint: 'Art. 8 Abs. 1 DelVO; endgültige Berechnung inkl. TH-Pauschale und Anh. III in Blatt 18.' },
        { cell: 'C62', alias: 'upperErrorLimitRate', kind: 'result', type: 'percent', format: '0.00%', label: 'Obere Fehlergrenze in % von BV' },
        { cell: 'C63', alias: 'assessment', kind: 'formula', type: 'check', label: 'Würdigung gegen die Wesentlichkeitsschwelle' },
      ],
    },
  ],
  summary: { primary: { cell: 'C33', label: 'Anzuwendender Stichprobenumfang', unit: 'Einheiten', reason: 'C27' }, rows: [{ cell: 'C35', label: 'Summe der Schichtumfänge n_h' }, { cell: 'C37', label: 'davon hochwertig' }, { cell: 'C40', label: 'Zufallsschichten n_hs' }, { cell: 'C53', label: 'Extrapolierter Fehler' }, { cell: 'C54', label: 'Genauigkeit SE' }, { cell: 'C61', label: 'Gesamtfehlerquote', strong: true }, { cell: 'C62', label: 'Obere Fehlergrenze', strong: true }], gauge: { threshold: 'C17', rate: 'C61', upper: 'C62' } },
}
