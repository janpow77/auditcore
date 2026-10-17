/**
 * Methodendefinition Blatt 09_SRS_1Z_S. Erzeugt mit `scripts/generate-definition.mjs` und von Hand
 * geprüft. Schichtzeilen tragen `columns: STRATA_COLUMNS`: `cell` ist die Zelle der ersten Schicht
 * (Spalte D), `total` die Summenzelle in Spalte C, soweit die Vorlage eine hat. Bezeichnungen
 * (Spalte B) und Fundstellen (Spalte K) entsprechen der Vorlage; in die Bezeichnung eingebettete
 * Formeln stehen als Kurzschreibweise in `formula`.
 */
import type { MethodDefinition } from '../../model/definition'
import { STRATA_COLUMNS } from '../../model/strata'

export const definition: MethodDefinition = {
  sheet: '09_SRS_1Z_S',
  number: '09',
  title: 'Einfaches Zufallsstichprobenverfahren – ein Zeitraum, geschichtet',
  shortTitle: 'Zufallsstichprobe, 1 Zeitraum, geschichtet',
  legalBasis: 'Art. 4 Abs. 2 und 3; Art. 5 Abs. 1 Buchst. b, Abs. 3–5 und 7; Art. 8; Anhang I; Anhang II Nr. 2.1 (geschichtet) DelVO (EU) 2023/67',
  sections: [
    {
      id: 'H', title: 'Zu prüfende Grundgesamtheit', reference: 'Art. 3, Art. 4 Abs. 2',
      fields: [
        { cell: 'C4', alias: 'programme', kind: 'input', type: 'text', format: '@', label: 'Programm(e) / CCI', hint: 'Art. 3 Abs. 1 und 2 DelVO.' },
        { cell: 'C5', alias: 'accountingYear', kind: 'input', type: 'text', format: '@', label: 'Geschäftsjahr' },
        { cell: 'C6', alias: 'samplingUnit', kind: 'input', type: 'text', format: '@', label: 'Stichprobeneinheit (z. B. Vorhaben, Ausgabenerklärung, Zahlungsantrag)' },
        { cell: 'C7', alias: 'stratificationCriterion', kind: 'input', type: 'text', format: '@', label: 'Schichtungskriterium', hint: 'Art. 4 Abs. 2 DelVO.' },
        { cell: 'C8', alias: 'exhaustiveBookValue', kind: 'input', type: 'amount', format: '#,##0.00" €"', label: 'Buchwert der umfassenden Schicht (fakultativ) (BV_e)', hint: 'Art. 5 Abs. 3; Art. 2 Nr. 11 DelVO.' },
        { cell: 'C9', alias: 'exhaustiveUnits', kind: 'input', type: 'integer', format: '#,##0', label: 'Anzahl Einheiten der umfassenden Schicht (N_e)' },
        { cell: 'C10', alias: 'exhaustiveHighValueUnits', kind: 'input', type: 'integer', format: '#,##0', label: 'davon hochwertige Einheiten (Anrechnung auf begrenzten Umfang)', hint: 'Art. 5 Abs. 7 UAbs. 3 DelVO.' },
        { cell: 'D12', alias: 'stratumUnits', kind: 'input', type: 'integer', format: '#,##0', columns: STRATA_COLUMNS, total: 'C12', label: 'Anzahl Einheiten je Zufallsschicht (N_h)' },
        { cell: 'D13', alias: 'stratumBookValue', kind: 'input', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, total: 'C13', label: 'Buchwert je Zufallsschicht (BV_h)' },
        { cell: 'C14', alias: 'bookValue', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Buchwert der Grundgesamtheit (Zufallsschichten + umfassende Schicht) (BV)' },
        { cell: 'C15', alias: 'populationDifference', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Abweichung zur angepassten Grundgesamtheit in Blatt 02' },
      ],
    },
    {
      id: 'I', title: 'Stichprobenparameter', reference: 'Anhang I',
      fields: [
        { cell: 'C16', alias: 'systemReliability', kind: 'input', type: 'choice', format: '@', list: 'reliability', label: 'Zuverlässigkeit des Verwaltungs- und Kontrollsystems (hoch / mittel / gering)', hint: 'Anh. I Nr. 2: Bewertung unter Berücksichtigung der Systemprüfungen, so dass das kombinierte Sicherheitsniveau hoch ist.' },
        { cell: 'C17', alias: 'confidenceLevel', kind: 'input', type: 'choice', format: '0%', list: 'confidence', label: 'Konfidenzniveau', hint: 'Anh. I Nr. 2: hoch ≥ 60 %, gering ≥ 90 %; Auswahl aus Blatt 01.' },
        { cell: 'C18', alias: 'testType', kind: 'input', type: 'choice', format: '@', list: 'testType', default: 'zweiseitig', label: 'Testart (zweiseitig / einseitig)', hint: 'Anh. I Nr. 3; Art. 2 Nr. 17 und 18 DelVO.' },
        { cell: 'C19', alias: 'zCoefficient', kind: 'formula', type: 'decimal', format: '0.000', label: "Koeffizient z der Normalverteilung (z / z')", hint: 'Anh. I Nr. 3, Tabelle der z-Werte (95 % außerhalb der Tabelle, siehe Blatt 01).' },
        { cell: 'C20', alias: 'checkConfidence', kind: 'formula', type: 'check', label: 'Prüfung Konfidenzniveau gegen Systembewertung', hint: 'Anh. I Nr. 2 legt nur die Eckwerte fest; für „mittel“ ist das Konfidenzniveau fachlich zu begründen.' },
        { cell: 'C21', alias: 'materiality', kind: 'input', type: 'percent', format: '0.00%', default: 0.02, label: 'Wesentlichkeitsschwelle (höchstens 2 %)', hint: 'Anh. I Nr. 1 i. V. m. Anh. XX Nr. 5.9 VO (EU) 2021/1060.' },
        { cell: 'C22', alias: 'checkMateriality', kind: 'formula', type: 'check', label: 'Prüfung Wesentlichkeitsschwelle' },
        { cell: 'C23', alias: 'tolerableError', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Zulässiger Fehler (TE = Wesentlichkeitsschwelle × BV)', hint: 'Anh. II: TE höchstens 2 % der gesamten Ausgaben.' },
        { cell: 'C24', alias: 'anticipatedErrorRate', kind: 'input', type: 'percent', format: '0.00%', label: 'Voraussichtliche Fehlerquote', hint: 'Anh. I Nr. 4: Pilotstichprobe, historische Daten oder fachkundiges Ermessen.' },
        { cell: 'C25', alias: 'anticipatedError', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Voraussichtlicher Fehler (AE = voraussichtliche Fehlerquote × BV)' },
        { cell: 'C26', alias: 'checkTolerableError', kind: 'formula', type: 'check', label: 'Prüfung TE > AE' },
        { cell: 'D28', alias: 'stratumAnticipatedDeviation', kind: 'input', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, label: 'Voraussichtliche Standardabweichung der Fehler je Schicht (σ_eh)' },
        { cell: 'D29', alias: 'stratumVarianceTerm', kind: 'formula', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, total: 'C29', label: 'Hilfszeile N_h · σ²_eh' },
        { cell: 'C30', alias: 'weightedDeviation', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Gewichtete Standardabweichung √(Σ N_h/N · σ²_eh) (σ_w)' },
      ],
    },
    {
      id: 'J', title: 'Stichprobenumfang', reference: 'Anhang II Nr. 2.1, geschichtet',
      fields: [
        { cell: 'C31', alias: 'computedSampleSize', kind: 'formula', type: 'integer', format: '#,##0', label: 'Rechnerischer Umfang', formula: 'n = (N·z·σ_w / (TE − AE))²' },
        { cell: 'C32', alias: 'programmeCategory', kind: 'input', type: 'choice', list: 'category', label: 'Kategorie des Programms nach Anh. XI Tabelle 2 VO (EU) 2021/1060 (1–4)', hint: 'Art. 5 Abs. 7 UAbs. 1 DelVO; ErwG 10.' },
        { cell: 'C33', alias: 'article83', kind: 'input', type: 'choice', format: '@', list: 'yesNo', default: 'Nein', label: 'Verbesserte angemessene Regelungen nach Art. 83 VO (EU) 2021/1060 (Ja/Nein)', hint: 'Anh. I Buchst. a DelVO: Stichprobe von 30 Einheiten.' },
        { cell: 'C34', alias: 'applyLimitedSize', kind: 'input', type: 'choice', format: '@', list: 'yesNo', default: 'Nein', label: 'Begrenzten Stichprobenumfang anwenden (Ja/Nein)', hint: 'Art. 5 Abs. 7: Anwendung auf eine Stichprobe für die gesamte Grundgesamtheit (UAbs. 2).' },
        { cell: 'C35', alias: 'checkLimitedSize', kind: 'formula', type: 'check', label: 'Zulässigkeit des begrenzten Stichprobenumfangs' },
        { cell: 'C36', alias: 'limitedSampleSize', kind: 'formula', type: 'integer', format: '#,##0', label: 'Begrenzter Stichprobenumfang (Einheiten) (n_lim)', hint: 'Angerechnet werden alle Einheiten der Zufallsschichten und nur die hochwertigen Einheiten umfassender Schichten (Art. 5 Abs. 7 UAbs. 3).' },
        { cell: 'C37', alias: 'minimumRandomSize', kind: 'formula', type: 'integer', format: '#,##0', label: 'Mindestumfang der Zufallsstichprobe', hint: 'Art. 5 Abs. 5.' },
        { cell: 'C38', alias: 'limitedSizeNet', kind: 'formula', type: 'integer', format: '#,##0', label: 'Begrenzter Umfang abzüglich hochwertiger Einheiten' },
        { cell: 'C39', alias: 'sampleSize', kind: 'result', type: 'integer', format: '#,##0', label: 'Anzuwendender Umfang der Zufallsstichprobe' },
        { cell: 'D41', alias: 'stratumSampleSize', kind: 'formula', type: 'integer', format: '#,##0', columns: STRATA_COLUMNS, total: 'C41', label: 'Stichprobenumfang je Schicht', formula: 'n_h = N_h/N · n' },
        { cell: 'D42', alias: 'checkStratumMinimumUnits', kind: 'formula', type: 'check', columns: STRATA_COLUMNS, label: 'Mindestens drei Einheiten je Zufallsschicht', hint: 'Art. 5 Abs. 5.' },
      ],
    },
    {
      id: 'K', title: 'Prüfergebnisse',
      fields: [
        { cell: 'C43', alias: 'exhaustiveErrors', kind: 'input', type: 'amount', format: '#,##0.00" €"', label: 'Summe der Fehler in der umfassenden Schicht (ΣE_e)' },
        { cell: 'D45', alias: 'stratumSampleBookValueSum', kind: 'input', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, total: 'C45', label: 'Summe der Buchwerte der Stichprobe (Σ BV_i)' },
        { cell: 'D46', alias: 'stratumErrorSum', kind: 'input', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, total: 'C46', label: 'Summe der Fehler der Stichprobe (Σ E_i)' },
        { cell: 'D47', alias: 'stratumSampleRatioDeviation', kind: 'input', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, label: 'Standardabweichung der Variablen q (s_qh)' },
      ],
    },
    {
      id: 'L', title: 'Hochrechnung (Verhältnisschätzung) und Genauigkeit',
      fields: [
        { cell: 'D49', alias: 'stratumProjectedError', kind: 'formula', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, total: 'C49', label: 'Extrapolierter Fehler je Schicht (EE_sh)', formula: 'BV_h · Σ E / Σ BV' },
        { cell: 'D50', alias: 'stratumPrecisionTerm', kind: 'formula', type: 'amount', format: '#,##0.00" €"', columns: STRATA_COLUMNS, total: 'C50', label: 'Hilfszeile N_h · s²_qh' },
        { cell: 'C51', alias: 'exhaustiveStratumError', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Fehler der umfassenden Schicht (EE_e)' },
        { cell: 'C52', alias: 'projectedError', kind: 'result', type: 'amount', format: '#,##0.00" €"', label: 'Extrapolierter Fehler', formula: 'EE = EE_e + Σ EE_sh' },
        { cell: 'C53', alias: 'precision', kind: 'result', type: 'amount', format: '#,##0.00" €"', label: 'Genauigkeit', formula: 'SE = N · z · s_qw / √n mit s²_qw = Σ N_h/N · s²_qh', hint: 'Anh. II Nr. 2.1 (geschichtet); setzt proportionale Aufteilung voraus.' },
        { cell: 'C54', alias: 'systemicErrors', kind: 'input', type: 'amount', format: '#,##0.00" €"', label: 'Abgegrenzte systembedingte Fehler (Betrag)', hint: 'Art. 2 Nr. 20, 21; Art. 8 Abs. 1 DelVO.' },
        { cell: 'C55', alias: 'anomalousErrors', kind: 'input', type: 'amount', format: '#,##0.00" €"', label: 'Nicht berichtigte anomale Fehler (Betrag)', hint: 'Art. 2 Nr. 20, 21; Art. 8 Abs. 1 DelVO.' },
        { cell: 'C56', alias: 'upperErrorLimit', kind: 'result', type: 'amount', format: '#,##0.00" €"', label: 'Obere Fehlergrenze (EE + SE + systembedingte + nicht berichtigte anomale Fehler)', hint: 'Art. 2 Nr. 20 DelVO.' },
        { cell: 'C57', alias: 'lowerErrorLimit', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Untere Fehlergrenze (EE − SE + systembedingte + nicht berichtigte anomale Fehler)', hint: 'Art. 2 Nr. 21 i. V. m. Nr. 17, 24 DelVO: nur beim zweiseitigen Test.' },
        { cell: 'C58', alias: 'relativePrecision', kind: 'formula', type: 'percent', format: '0.00%', label: 'Relative Genauigkeit (SE / BV)' },
        { cell: 'C59', alias: 'projectedErrorRate', kind: 'formula', type: 'percent', format: '0.00%', label: 'Extrapolierte Zufallsfehlerquote (EE / BV)' },
        { cell: 'C60', alias: 'totalErrorRate', kind: 'result', type: 'percent', format: '0.00%', label: 'Gesamtfehlerquote ((EE + systembedingte + nicht berichtigte anomale Fehler) / BV)', hint: 'Art. 8 Abs. 1 DelVO; endgültige Berechnung inkl. TH-Pauschale und Anh. III in Blatt 18.' },
        { cell: 'C61', alias: 'upperErrorLimitRate', kind: 'result', type: 'percent', format: '0.00%', label: 'Obere Fehlergrenze in % von BV' },
        { cell: 'C62', alias: 'assessment', kind: 'formula', type: 'check', label: 'Würdigung gegen die Wesentlichkeitsschwelle' },
      ],
    },
  ],
  summary: {
    primary: { cell: 'C39', label: 'Anzuwendender Umfang der Zufallsstichprobe', unit: 'Einheiten', reason: 'C31' },
    rows: [{ cell: 'C41', label: 'Summe der Schichtumfänge n_h' }, { cell: 'C12', label: 'Zufallsschichten N' }, { cell: 'C52', label: 'Extrapolierter Fehler' }, { cell: 'C53', label: 'Genauigkeit SE' }, { cell: 'C60', label: 'Gesamtfehlerquote', strong: true }, { cell: 'C61', label: 'Obere Fehlergrenze', strong: true }],
    gauge: { threshold: 'C21', rate: 'C60', upper: 'C61' },
  },
}
