/**
 * Methodendefinition Blatt 08_SRS_1Z. Erzeugt mit `scripts/generate-definition.mjs` aus der
 * Zellbeschreibung der Vorlage und von Hand geprüft: Abschnitte, Reihenfolge, Zellen,
 * Zahlenformate, Bezeichnungen (Spalte B) und Fundstellen (Spalte D) entsprechen der Vorlage;
 * in die Bezeichnung eingebettete Formeln stehen als Kurzschreibweise in `formula`.
 */
import type { MethodDefinition } from '../../model/definition'

export const definition: MethodDefinition = {
  sheet: '08_SRS_1Z',
  number: '08',
  title: 'Einfaches Zufallsstichprobenverfahren – ein Zeitraum, nicht geschichtet',
  shortTitle: 'Zufallsstichprobe, 1 Zeitraum',
  legalBasis: 'Art. 5 Abs. 1 Buchst. b, Abs. 3–5 und 7; Art. 8; Anhang I; Anhang II Nr. 2.1 (Verhältnisschätzung) DelVO (EU) 2023/67',
  sections: [
    {
      id: 'H', title: 'Zu prüfende Grundgesamtheit', reference: 'Art. 3',
      fields: [
        { cell: 'C4', alias: 'programme', kind: 'input', type: 'text', format: '@', label: 'Programm(e) / CCI', hint: 'Art. 3 Abs. 1 und 2 DelVO.' },
        { cell: 'C5', alias: 'accountingYear', kind: 'input', type: 'text', format: '@', label: 'Geschäftsjahr' },
        { cell: 'C6', alias: 'samplingUnit', kind: 'input', type: 'text', format: '@', label: 'Stichprobeneinheit (z. B. Vorhaben, Ausgabenerklärung, Zahlungsantrag)' },
        { cell: 'C7', alias: 'bookValue', kind: 'link', type: 'amount', format: '#,##0.00" €"', link: { sheet: '02_Grundgesamtheit', cell: 'C51' }, label: 'Buchwert der angepassten zu prüfenden Grundgesamtheit (BV)', hint: 'Vorbelegt aus Blatt 02.' },
        { cell: 'C8', alias: 'populationSize', kind: 'link', type: 'integer', format: '#,##0', link: { sheet: '02_Grundgesamtheit', cell: 'C52' }, label: 'Anzahl Stichprobeneinheiten der Grundgesamtheit (N)', hint: 'Vorbelegt aus Blatt 02.' },
        { cell: 'C9', alias: 'exhaustiveBookValue', kind: 'input', type: 'amount', format: '#,##0.00" €"', label: 'Buchwert der umfassenden Schicht (fakultativ) (BV_e)', hint: 'Art. 5 Abs. 3; Art. 2 Nr. 11 DelVO.' },
        { cell: 'C10', alias: 'exhaustiveUnits', kind: 'input', type: 'integer', format: '#,##0', label: 'Anzahl Einheiten der umfassenden Schicht (N_e)' },
        { cell: 'C11', alias: 'exhaustiveHighValueUnits', kind: 'input', type: 'integer', format: '#,##0', label: 'davon hochwertige Einheiten (Anrechnung auf begrenzten Umfang)', hint: 'Art. 5 Abs. 7 UAbs. 3 DelVO.' },
        { cell: 'C12', alias: 'randomStratumBookValue', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Buchwert der Zufallsschicht (BV_s)' },
        { cell: 'C13', alias: 'randomStratumPopulation', kind: 'formula', type: 'integer', format: '#,##0', label: 'Anzahl Einheiten der Zufallsschicht (N_s)' },
      ],
    },
    {
      id: 'I', title: 'Stichprobenparameter', reference: 'Anhang I',
      fields: [
        { cell: 'C14', alias: 'systemReliability', kind: 'input', type: 'choice', format: '@', list: 'reliability', label: 'Zuverlässigkeit des Verwaltungs- und Kontrollsystems (hoch / mittel / gering)', hint: 'Anh. I Nr. 2: Bewertung unter Berücksichtigung der Systemprüfungen, so dass das kombinierte Sicherheitsniveau hoch ist.' },
        { cell: 'C15', alias: 'confidenceLevel', kind: 'input', type: 'choice', format: '0%', list: 'confidence', label: 'Konfidenzniveau', hint: 'Anh. I Nr. 2: hoch ≥ 60 %, gering ≥ 90 %; Auswahl aus Blatt 01.' },
        { cell: 'C16', alias: 'testType', kind: 'input', type: 'choice', format: '@', list: 'testType', default: 'zweiseitig', label: 'Testart (zweiseitig / einseitig)', hint: 'Anh. I Nr. 3; Art. 2 Nr. 17 und 18 DelVO.' },
        { cell: 'C17', alias: 'zCoefficient', kind: 'formula', type: 'decimal', format: '0.000', label: "Koeffizient z der Normalverteilung (z / z')", hint: 'Anh. I Nr. 3, Tabelle der z-Werte (95 % außerhalb der Tabelle, siehe Blatt 01).' },
        { cell: 'C18', alias: 'checkConfidence', kind: 'formula', type: 'check', label: 'Prüfung Konfidenzniveau gegen Systembewertung', hint: 'Anh. I Nr. 2 legt nur die Eckwerte fest; für „mittel“ ist das Konfidenzniveau fachlich zu begründen.' },
        { cell: 'C19', alias: 'materiality', kind: 'input', type: 'percent', format: '0.00%', default: 0.02, label: 'Wesentlichkeitsschwelle (höchstens 2 %)', hint: 'Anh. I Nr. 1 i. V. m. Anh. XX Nr. 5.9 VO (EU) 2021/1060.' },
        { cell: 'C20', alias: 'checkMateriality', kind: 'formula', type: 'check', label: 'Prüfung Wesentlichkeitsschwelle' },
        { cell: 'C21', alias: 'tolerableError', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Zulässiger Fehler (TE = Wesentlichkeitsschwelle × BV)', hint: 'Anh. II: TE höchstens 2 % der gesamten Ausgaben.' },
        { cell: 'C22', alias: 'anticipatedErrorRate', kind: 'input', type: 'percent', format: '0.00%', label: 'Voraussichtliche Fehlerquote', hint: 'Anh. I Nr. 4: Pilotstichprobe, historische Daten oder fachkundiges Ermessen.' },
        { cell: 'C23', alias: 'anticipatedError', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Voraussichtlicher Fehler (AE = voraussichtliche Fehlerquote × BV)' },
        { cell: 'C24', alias: 'checkTolerableError', kind: 'formula', type: 'check', label: 'Prüfung TE > AE' },
        { cell: 'C25', alias: 'anticipatedDeviation', kind: 'input', type: 'amount', format: '#,##0.00" €"', label: 'Voraussichtliche Standardabweichung der Fehler (σ_e)', hint: 'Anh. I Nr. 4.' },
      ],
    },
    {
      id: 'J', title: 'Stichprobenumfang', reference: 'Anhang II Nr. 2.1; Art. 5 Abs. 5 und 7',
      fields: [
        { cell: 'C26', alias: 'computedSampleSize', kind: 'formula', type: 'integer', format: '#,##0', label: 'Rechnerischer Umfang der Zufallsstichprobe', formula: 'n = (N_s·z·σ_e / (TE − AE))²', hint: 'Bei umfassender Schicht wird N der Zufallsschicht verwendet (Genauigkeit nur aus nicht umfassenden Schichten).' },
        { cell: 'C27', alias: 'programmeCategory', kind: 'input', type: 'choice', list: 'category', label: 'Kategorie des Programms nach Anh. XI Tabelle 2 VO (EU) 2021/1060 (1–4)', hint: 'Art. 5 Abs. 7 UAbs. 1 DelVO; ErwG 10.' },
        { cell: 'C28', alias: 'article83', kind: 'input', type: 'choice', format: '@', list: 'yesNo', default: 'Nein', label: 'Verbesserte angemessene Regelungen nach Art. 83 VO (EU) 2021/1060 (Ja/Nein)', hint: 'Anh. I Buchst. a DelVO: Stichprobe von 30 Einheiten.' },
        { cell: 'C29', alias: 'applyLimitedSize', kind: 'input', type: 'choice', format: '@', list: 'yesNo', default: 'Nein', label: 'Begrenzten Stichprobenumfang anwenden (Ja/Nein)', hint: 'Art. 5 Abs. 7: Anwendung auf eine Stichprobe für die gesamte Grundgesamtheit (UAbs. 2).' },
        { cell: 'C30', alias: 'checkLimitedSize', kind: 'formula', type: 'check', label: 'Zulässigkeit des begrenzten Stichprobenumfangs' },
        { cell: 'C31', alias: 'limitedSampleSize', kind: 'formula', type: 'integer', format: '#,##0', label: 'Begrenzter Stichprobenumfang (Einheiten) (n_lim)', hint: 'Angerechnet werden alle Einheiten der Zufallsschichten und nur die hochwertigen Einheiten umfassender Schichten (Art. 5 Abs. 7 UAbs. 3).' },
        { cell: 'C32', alias: 'minimumRandomSize', kind: 'formula', type: 'integer', format: '#,##0', label: 'Mindestumfang der Zufallsstichprobe (30 abzüglich umfassende Schicht, mind. 3)', hint: 'Art. 5 Abs. 5.' },
        { cell: 'C33', alias: 'limitedSizeNet', kind: 'formula', type: 'integer', format: '#,##0', label: 'Begrenzter Umfang abzüglich hochwertiger Einheiten der umfassenden Schicht' },
        { cell: 'C34', alias: 'sampleSize', kind: 'result', type: 'integer', format: '#,##0', label: 'Anzuwendender Umfang der Zufallsstichprobe' },
        { cell: 'C35', alias: 'totalSampleSize', kind: 'formula', type: 'integer', format: '#,##0', label: 'Gesamtstichprobe (Zufallsstichprobe + umfassende Schicht)' },
      ],
    },
    {
      id: 'K', title: 'Prüfergebnisse',
      fields: [
        { cell: 'C36', alias: 'sampleBookValueSum', kind: 'input', type: 'amount', format: '#,##0.00" €"', subsample: 'bookValueSum', label: 'Summe der Buchwerte der Stichprobe der Zufallsschicht (Σ BV_i)' },
        { cell: 'C37', alias: 'errorSum', kind: 'input', type: 'amount', format: '#,##0.00" €"', subsample: 'errorSum', label: 'Summe der Fehler der Stichprobe der Zufallsschicht (Σ E_i)', hint: 'Bei Unterstichproben: hochgerechneter Fehler je Einheit (Art. 8 Abs. 3; Blatt 17).' },
        { cell: 'C38', alias: 'sampleErrorDeviation', kind: 'input', type: 'amount', format: '#,##0.00" €"', label: 'Standardabweichung der Fehler in der Stichprobe (für Neuberechnungen) (s_e)', hint: 'Anh. II Nr. 2.2/2.3.' },
        { cell: 'C39', alias: 'sampleRatioDeviation', kind: 'input', type: 'amount', format: '#,##0.00" €"', label: 'Standardabweichung der Variablen q_i = E_i − (Σ E/Σ BV)·BV_i (s_q)', hint: 'Anh. II Nr. 2.1: Verhältnisschätzung.' },
        { cell: 'C40', alias: 'exhaustiveErrors', kind: 'input', type: 'amount', format: '#,##0.00" €"', subsample: 'highValueErrors', label: 'Summe der Fehler in der umfassenden Schicht (ΣE_e)' },
      ],
    },
    {
      id: 'L', title: 'Hochrechnung (Verhältnisschätzung) und Genauigkeit', reference: 'Anhang II Nr. 2.1; Art. 8',
      fields: [
        { cell: 'C41', alias: 'exhaustiveStratumError', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Fehler der umfassenden Schicht (EE_e)' },
        { cell: 'C42', alias: 'randomStratumError', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Extrapolierter Fehler der Zufallsschicht (EE_s)', formula: 'BV_s · Σ E_i / Σ BV_i' },
        { cell: 'C43', alias: 'projectedError', kind: 'result', type: 'amount', format: '#,##0.00" €"', label: 'Extrapolierter Fehler', formula: 'EE = EE_e + EE_s' },
        { cell: 'C44', alias: 'precision', kind: 'result', type: 'amount', format: '#,##0.00" €"', label: 'Genauigkeit', formula: 'SE = N_s · z · s_q / √n' },
        { cell: 'C45', alias: 'systemicErrors', kind: 'input', type: 'amount', format: '#,##0.00" €"', label: 'Abgegrenzte systembedingte Fehler (Betrag)', hint: 'Art. 2 Nr. 20, 21; Art. 8 Abs. 1 DelVO.' },
        { cell: 'C46', alias: 'anomalousErrors', kind: 'input', type: 'amount', format: '#,##0.00" €"', label: 'Nicht berichtigte anomale Fehler (Betrag)', hint: 'Art. 2 Nr. 20, 21; Art. 8 Abs. 1 DelVO.' },
        { cell: 'C47', alias: 'upperErrorLimit', kind: 'result', type: 'amount', format: '#,##0.00" €"', label: 'Obere Fehlergrenze (EE + SE + systembedingte + nicht berichtigte anomale Fehler)', hint: 'Art. 2 Nr. 20 DelVO.' },
        { cell: 'C48', alias: 'lowerErrorLimit', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Untere Fehlergrenze (EE − SE + systembedingte + nicht berichtigte anomale Fehler)', hint: 'Art. 2 Nr. 21 i. V. m. Nr. 17, 24 DelVO: nur beim zweiseitigen Test.' },
        { cell: 'C49', alias: 'relativePrecision', kind: 'formula', type: 'percent', format: '0.00%', label: 'Relative Genauigkeit (SE / BV)' },
        { cell: 'C50', alias: 'projectedErrorRate', kind: 'formula', type: 'percent', format: '0.00%', label: 'Extrapolierte Zufallsfehlerquote (EE / BV)' },
        { cell: 'C51', alias: 'totalErrorRate', kind: 'result', type: 'percent', format: '0.00%', label: 'Gesamtfehlerquote ((EE + systembedingte + nicht berichtigte anomale Fehler) / BV)', hint: 'Art. 8 Abs. 1 DelVO; endgültige Berechnung inkl. TH-Pauschale und Anh. III in Blatt 18.' },
        { cell: 'C52', alias: 'upperErrorLimitRate', kind: 'result', type: 'percent', format: '0.00%', label: 'Obere Fehlergrenze in % von BV' },
        { cell: 'C53', alias: 'assessment', kind: 'formula', type: 'check', label: 'Würdigung gegen die Wesentlichkeitsschwelle' },
      ],
    },
  ],
  summary: {
    primary: { cell: 'C34', label: 'Anzuwendender Umfang der Zufallsstichprobe', unit: 'Einheiten', reason: 'C26' },
    rows: [{ cell: 'C35', label: 'Gesamtstichprobe' }, { cell: 'C13', label: 'Zufallsschicht N_s' }, { cell: 'C43', label: 'Extrapolierter Fehler' }, { cell: 'C44', label: 'Genauigkeit SE' }, { cell: 'C51', label: 'Gesamtfehlerquote', strong: true }, { cell: 'C52', label: 'Obere Fehlergrenze', strong: true }],
    gauge: { threshold: 'C19', rate: 'C51', upper: 'C52' },
  },
}
