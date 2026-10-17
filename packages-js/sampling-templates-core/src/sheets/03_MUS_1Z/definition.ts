/**
 * Methodendefinition Blatt 03_MUS_1Z. Erzeugt mit `scripts/generate-definition.mjs`
 * aus der Zellbeschreibung der Vorlage und von Hand geprüft: Abschnitte,
 * Reihenfolge, Zellen, Zahlenformate und Fundstellen entsprechen der Vorlage;
 * eingebettete Formeln stehen als Kurzschreibweise in `formula`.
 */
import type { FieldDefinition, MethodDefinition } from '../../model/definition'

const EUR = '#,##0.00" €"'
const INT = '#,##0'
const RATE = '0.00%'
const DEC4 = '0.0000'

const population: FieldDefinition[] = [
  { cell: 'C4', alias: 'programme', kind: 'input', type: 'text', format: '@', label: 'Programm(e) / CCI', hint: 'Art. 3 Abs. 1 und 2 DelVO.' },
  { cell: 'C5', alias: 'accountingYear', kind: 'input', type: 'text', format: '@', label: 'Geschäftsjahr' },
  { cell: 'C6', alias: 'samplingUnit', kind: 'input', type: 'text', format: '@', label: 'Stichprobeneinheit (z. B. Vorhaben, Ausgabenerklärung, Zahlungsantrag)' },
  {
    cell: 'C7',
    alias: 'bookValue',
    kind: 'link',
    type: 'amount',
    format: EUR,
    label: 'Buchwert der angepassten zu prüfenden Grundgesamtheit (positive Einheiten) (BV)',
    hint: 'Vorbelegt aus Blatt 02 (Art. 3 Abs. 4–6); bei Bedarf überschreiben.',
    link: { sheet: '02_Grundgesamtheit', cell: 'C51' },
  },
  {
    cell: 'C8',
    alias: 'populationSize',
    kind: 'link',
    type: 'integer',
    format: INT,
    label: 'Umfang der Grundgesamtheit (Anzahl Stichprobeneinheiten) (N)',
    hint: 'Vorbelegt aus Blatt 02.',
    link: { sheet: '02_Grundgesamtheit', cell: 'C52' },
  },
]

const parameters: FieldDefinition[] = [
  {
    cell: 'C9',
    alias: 'systemReliability',
    kind: 'input',
    type: 'choice',
    format: '@',
    list: 'reliability',
    label: 'Zuverlässigkeit des Verwaltungs- und Kontrollsystems (hoch / mittel / gering)',
    hint: 'Anh. I Nr. 2: Bewertung unter Berücksichtigung der Systemprüfungen, so dass das kombinierte Sicherheitsniveau hoch ist.',
  },
  { cell: 'C10', alias: 'confidenceLevel', kind: 'input', type: 'choice', format: '0%', list: 'confidence', label: 'Konfidenzniveau', hint: 'Anh. I Nr. 2: hoch ≥ 60 %, gering ≥ 90 %; Auswahl aus Blatt 01.' },
  { cell: 'C11', alias: 'testType', kind: 'input', type: 'choice', format: '@', list: 'testType', default: 'zweiseitig', label: 'Testart (zweiseitig / einseitig)', hint: 'Anh. I Nr. 3; Art. 2 Nr. 17 und 18 DelVO.' },
  { cell: 'C12', alias: 'zCoefficient', kind: 'formula', type: 'decimal', format: '0.000', label: "Koeffizient z der Normalverteilung (z / z')", hint: 'Anh. I Nr. 3, Tabelle der z-Werte (95 % außerhalb der Tabelle, siehe Blatt 01).' },
  {
    cell: 'C13',
    alias: 'checkConfidence',
    kind: 'formula',
    type: 'check',
    label: 'Prüfung Konfidenzniveau gegen Systembewertung',
    hint: 'Anh. I Nr. 2 legt nur die Eckwerte fest; für „mittel“ ist das Konfidenzniveau fachlich zu begründen.',
  },
  { cell: 'C14', alias: 'materiality', kind: 'input', type: 'percent', format: RATE, default: 0.02, label: 'Wesentlichkeitsschwelle (höchstens 2 %)', hint: 'Anh. I Nr. 1 i. V. m. Anh. XX Nr. 5.9 VO (EU) 2021/1060.' },
  { cell: 'C15', alias: 'checkMateriality', kind: 'formula', type: 'check', label: 'Prüfung Wesentlichkeitsschwelle' },
  { cell: 'C16', alias: 'tolerableError', kind: 'formula', type: 'amount', format: EUR, label: 'Zulässiger Fehler', formula: 'TE = Wesentlichkeitsschwelle × BV', hint: 'Anh. II: TE höchstens 2 % der gesamten Ausgaben.' },
  { cell: 'C17', alias: 'anticipatedErrorRate', kind: 'input', type: 'percent', format: RATE, label: 'Voraussichtliche Fehlerquote', hint: 'Anh. I Nr. 4: Pilotstichprobe, historische Daten oder fachkundiges Ermessen.' },
  { cell: 'C18', alias: 'anticipatedError', kind: 'formula', type: 'amount', format: EUR, label: 'Voraussichtlicher Fehler', formula: 'AE = voraussichtliche Fehlerquote × BV' },
  { cell: 'C19', alias: 'checkTolerableError', kind: 'formula', type: 'check', label: 'Prüfung TE > AE' },
  { cell: 'C20', alias: 'anticipatedDeviation', kind: 'input', type: 'decimal', format: DEC4, label: 'Voraussichtliche Standardabweichung der Fehlerquoten (σ_r)', hint: 'Anh. I Nr. 4.' },
]

const size: FieldDefinition[] = [
  { cell: 'C21', alias: 'computedSampleSize', kind: 'formula', type: 'integer', format: INT, label: 'Rechnerischer Stichprobenumfang', formula: 'n = (z · BV · σ_r / (TE − AE))²', hint: 'Anh. II Nr. 1.1, nicht geschichtet.' },
  { cell: 'C22', alias: 'programmeCategory', kind: 'input', type: 'choice', list: 'category', label: 'Kategorie des Programms nach Anh. XI Tabelle 2 VO (EU) 2021/1060 (1–4)', hint: 'Art. 5 Abs. 7 UAbs. 1 DelVO; ErwG 10.' },
  { cell: 'C23', alias: 'article83', kind: 'input', type: 'choice', format: '@', list: 'yesNo', default: 'Nein', label: 'Verbesserte angemessene Regelungen nach Art. 83 VO (EU) 2021/1060 (Ja/Nein)', hint: 'Anh. I Buchst. a DelVO: Stichprobe von 30 Einheiten.' },
  {
    cell: 'C24',
    alias: 'applyLimitedSize',
    kind: 'input',
    type: 'choice',
    format: '@',
    list: 'yesNo',
    default: 'Nein',
    label: 'Begrenzten Stichprobenumfang anwenden (Ja/Nein)',
    hint: 'Art. 5 Abs. 7: Anwendung auf eine Stichprobe für die gesamte Grundgesamtheit (UAbs. 2).',
  },
  { cell: 'C25', alias: 'checkLimitedSize', kind: 'formula', type: 'check', label: 'Zulässigkeit des begrenzten Stichprobenumfangs' },
  {
    cell: 'C26',
    alias: 'limitedSampleSize',
    kind: 'formula',
    type: 'integer',
    format: INT,
    label: 'Begrenzter Stichprobenumfang (Einheiten) (n_lim)',
    hint: 'Angerechnet werden alle Einheiten der Zufallsschichten und nur die hochwertigen Einheiten umfassender Schichten (Art. 5 Abs. 7 UAbs. 3).',
  },
  { cell: 'C27', alias: 'sampleSize', kind: 'result', type: 'integer', format: INT, label: 'Anzuwendender Stichprobenumfang (mind. 30; ggf. begrenzt)', hint: 'Art. 5 Abs. 5: mindestens 30 Einheiten; Art. 5 Abs. 7: Begrenzung.' },
]

const selection: FieldDefinition[] = [
  {
    cell: 'C28',
    alias: 'cutOff',
    kind: 'formula',
    type: 'amount',
    format: EUR,
    label: 'Grenzwert für hochwertige Einheiten (BV1/n1) (BV/n)',
    hint: 'Art. 5 Abs. 2 UAbs. 2: hochwertige Einheiten über dem Auswahlintervall werden vollständig geprüft.',
  },
  { cell: 'C29', alias: 'highValueUnits', kind: 'input', type: 'integer', format: INT, label: 'Anzahl hochwertiger Einheiten (BV > Grenzwert) (n_e)' },
  { cell: 'C30', alias: 'highValueBookValue', kind: 'input', type: 'amount', format: EUR, label: 'Buchwert der hochwertigen Einheiten (BV_e)' },
  { cell: 'C31', alias: 'randomStratumBookValue', kind: 'formula', type: 'amount', format: EUR, label: 'Buchwert der Zufallsschicht (niedrigwertige Einheiten) (BV_s)' },
  { cell: 'C32', alias: 'randomStratumUnits', kind: 'formula', type: 'integer', format: INT, label: 'Anzahl der in der Zufallsschicht auszuwählenden Einheiten (n_s)' },
  { cell: 'C33', alias: 'checkMinimumUnits', kind: 'formula', type: 'check', label: 'Mindestens drei Einheiten in der Zufallsschicht' },
  { cell: 'C34', alias: 'samplingInterval', kind: 'formula', type: 'amount', format: EUR, label: 'Auswahlintervall (SI)', formula: 'SI = BV_s / n_s', hint: 'Art. 2 Nr. 9; Art. 5 Abs. 2 UAbs. 2 DelVO.' },
  {
    cell: 'C35',
    alias: 'iterationUnits',
    kind: 'input',
    type: 'integer',
    format: INT,
    label: 'Einheiten der Zufallsschicht mit BV > Auswahlintervall (Iteration)',
    hint: 'Solche Einheiten sind der hochwertigen Schicht zuzuordnen; Grenzwert und Intervall sind neu zu berechnen.',
  },
  { cell: 'C36', alias: 'checkIteration', kind: 'formula', type: 'check', label: 'Prüfung Iteration' },
]

const findings: FieldDefinition[] = [
  {
    cell: 'C37',
    alias: 'highValueErrors',
    kind: 'input',
    type: 'amount',
    format: EUR,
    subsample: 'highValueErrors',
    label: 'Summe der Fehler in den hochwertigen Einheiten (ΣE_e)',
    hint: 'Bei Unterstichproben: auf die Stichprobeneinheit hochgerechneter Fehler (Art. 8 Abs. 3; Blatt 17).',
  },
  { cell: 'C38', alias: 'errorRateSum', kind: 'input', type: 'decimal', format: DEC4, subsample: 'errorRateSum', label: 'Summe der Fehlerquoten der Stichprobe der Zufallsschicht (Σ E_i/BV_i)' },
  { cell: 'C39', alias: 'sampleDeviation', kind: 'input', type: 'decimal', format: DEC4, label: 'Standardabweichung der Fehlerquoten in der Stichprobe der Zufallsschicht (s_r)', hint: 'Aus derselben Stichprobe wie die Hochrechnung (Anh. II Nr. 1).' },
]

const projection: FieldDefinition[] = [
  { cell: 'C40', alias: 'exhaustiveStratumError', kind: 'formula', type: 'amount', format: EUR, label: 'Fehler der umfassenden (hochwertigen) Schicht (EE_e)' },
  { cell: 'C41', alias: 'randomStratumError', kind: 'formula', type: 'amount', format: EUR, label: 'Extrapolierter Fehler der Zufallsschicht (EE_s)', formula: 'EE_s = SI · Σ E_i/BV_i' },
  { cell: 'C42', alias: 'projectedError', kind: 'result', type: 'amount', format: EUR, label: 'Extrapolierter Fehler', formula: 'EE = EE_e + EE_s' },
  { cell: 'C43', alias: 'precision', kind: 'result', type: 'amount', format: EUR, label: 'Genauigkeit der Stichprobe', formula: 'SE = z · BV_s / √n_s · s_r' },
  { cell: 'C44', alias: 'systemicErrors', kind: 'input', type: 'amount', format: EUR, label: 'Abgegrenzte systembedingte Fehler (Betrag)', hint: 'Art. 2 Nr. 20, 21; Art. 8 Abs. 1 DelVO.' },
  { cell: 'C45', alias: 'anomalousErrors', kind: 'input', type: 'amount', format: EUR, label: 'Nicht berichtigte anomale Fehler (Betrag)', hint: 'Art. 2 Nr. 20, 21; Art. 8 Abs. 1 DelVO.' },
  { cell: 'C46', alias: 'upperErrorLimit', kind: 'result', type: 'amount', format: EUR, label: 'Obere Fehlergrenze', formula: 'EE + SE + systembedingte + nicht berichtigte anomale Fehler', hint: 'Art. 2 Nr. 20 DelVO.' },
  {
    cell: 'C47',
    alias: 'lowerErrorLimit',
    kind: 'formula',
    type: 'amount',
    format: EUR,
    label: 'Untere Fehlergrenze',
    formula: 'EE − SE + systembedingte + nicht berichtigte anomale Fehler',
    hint: 'Art. 2 Nr. 21 i. V. m. Nr. 17, 24 DelVO: nur beim zweiseitigen Test.',
  },
  { cell: 'C48', alias: 'relativePrecision', kind: 'formula', type: 'percent', format: RATE, label: 'Relative Genauigkeit', formula: 'SE / BV' },
  { cell: 'C49', alias: 'projectedErrorRate', kind: 'formula', type: 'percent', format: RATE, label: 'Extrapolierte Zufallsfehlerquote', formula: 'EE / BV' },
  {
    cell: 'C50',
    alias: 'totalErrorRate',
    kind: 'result',
    type: 'percent',
    format: RATE,
    label: 'Gesamtfehlerquote',
    formula: '(EE + systembedingte + nicht berichtigte anomale Fehler) / BV',
    hint: 'Art. 8 Abs. 1 DelVO; endgültige Berechnung inkl. TH-Pauschale und Anh. III in Blatt 18.',
  },
  { cell: 'C51', alias: 'upperErrorLimitRate', kind: 'result', type: 'percent', format: RATE, label: 'Obere Fehlergrenze in % von BV' },
  { cell: 'C52', alias: 'assessment', kind: 'formula', type: 'check', label: 'Würdigung gegen die Wesentlichkeitsschwelle' },
]

export const definition: MethodDefinition = {
  sheet: '03_MUS_1Z',
  number: '03',
  title: 'MUS-Standardansatz – ein Stichprobenzeitraum, nicht geschichtet',
  shortTitle: 'MUS, 1 Zeitraum',
  legalBasis: 'Art. 5 Abs. 1 Buchst. a, Abs. 2, 4, 5 und 7; Art. 8; Anhang I; Anhang II Nr. 1.1 DelVO (EU) 2023/67',
  sections: [
    { id: 'H', title: 'Zu prüfende Grundgesamtheit', reference: 'Art. 3', fields: population },
    { id: 'I', title: 'Stichprobenparameter', reference: 'Anhang I', fields: parameters },
    { id: 'J', title: 'Stichprobenumfang', reference: 'Anhang II Nr. 1.1; Art. 5 Abs. 5 und 7', fields: size },
    { id: 'K', title: 'Stichprobenauswahl mit Wahrscheinlichkeit proportional zur Größe', fields: selection },
    { id: 'L', title: 'Prüfergebnisse', fields: findings },
    { id: 'M', title: 'Hochrechnung und Genauigkeit', reference: 'Anhang II Nr. 1.1; Art. 8', fields: projection },
  ],
  summary: {
    primary: { cell: 'C27', label: 'Anzuwendender Stichprobenumfang', unit: 'Einheiten', reason: 'C21' },
    rows: [
      { cell: 'C29', label: 'davon hochwertig' },
      { cell: 'C32', label: 'Zufallsschicht n_s' },
      { cell: 'C34', label: 'Auswahlintervall' },
      { cell: 'C42', label: 'Extrapolierter Fehler' },
      { cell: 'C43', label: 'Genauigkeit SE' },
      { cell: 'C50', label: 'Gesamtfehlerquote', strong: true },
      { cell: 'C51', label: 'Obere Fehlergrenze', strong: true },
    ],
    gauge: { threshold: 'C14', rate: 'C50', upper: 'C51' },
  },
}
