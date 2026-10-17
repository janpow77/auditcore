/**
 * Methodendefinition Blatt 13_NS_GW. Erzeugt mit `scripts/generate-definition.mjs`
 * aus der Zellbeschreibung der Vorlage und von Hand geprüft: Abschnitte,
 * Reihenfolge, Zellen, Zahlenformate und Fundstellen (Spalte D) entsprechen der
 * Vorlage; eingebettete Formeln stehen als Kurzschreibweise in `formula`.
 */
import type { MethodDefinition } from '../../model/definition'

const EUR = '#,##0.00" €"'
const INT = '#,##0'
const RATE = '0.00%'

export const definition: MethodDefinition = {
  sheet: '13_NS_GW',
  number: '13',
  title: 'Nichtstatistisches Verfahren – Auswahl mit gleicher Wahrscheinlichkeit, nicht geschichtet',
  shortTitle: 'Nichtstatistisch, gleiche Wahrscheinlichkeit',
  legalBasis: 'Art. 6 Abs. 1 Buchst. b, Abs. 2 und 3; Art. 8 Abs. 2; Anhang II Nr. 2.1 (Verhältnisschätzung) DelVO (EU) 2023/67',
  sections: [
    {
      id: 'H', title: 'Zu prüfende Grundgesamtheit', reference: 'Art. 3',
      fields: [
        { cell: 'C4', alias: 'programme', kind: 'input', type: 'text', format: '@', label: 'Programm(e) / CCI', hint: 'Art. 3 Abs. 1 und 2 DelVO.' },
        { cell: 'C5', alias: 'accountingYear', kind: 'input', type: 'text', format: '@', label: 'Geschäftsjahr' },
        { cell: 'C6', alias: 'samplingUnit', kind: 'input', type: 'text', format: '@', label: 'Stichprobeneinheit (z. B. Vorhaben, Ausgabenerklärung, Zahlungsantrag)' },
        { cell: 'C7', alias: 'bookValue', kind: 'link', type: 'amount', format: EUR, label: 'Buchwert der angepassten Grundgesamtheit (BV)', hint: 'Vorbelegt aus Blatt 02.', link: { sheet: '02_Grundgesamtheit', cell: 'C51' } },
        { cell: 'C8', alias: 'populationSize', kind: 'link', type: 'integer', format: INT, label: 'Anzahl Stichprobeneinheiten (N)', hint: 'Vorbelegt aus Blatt 02.', link: { sheet: '02_Grundgesamtheit', cell: 'C52' } },
        { cell: 'C9', alias: 'checkAdmissibility', kind: 'formula', type: 'check', label: 'Zulässigkeit des nichtstatistischen Verfahrens (N < 300)' },
        { cell: 'C10', alias: 'exhaustiveBookValue', kind: 'input', type: 'amount', format: EUR, label: 'Buchwert der umfassenden Schicht (fakultativ) (BV_e)', hint: 'Art. 6 Abs. 1 UAbs. 3; Art. 5 Abs. 3.' },
        { cell: 'C11', alias: 'exhaustiveUnits', kind: 'input', type: 'integer', format: INT, label: 'Anzahl Einheiten der umfassenden Schicht (N_e)' },
        { cell: 'C12', alias: 'randomStratumBookValue', kind: 'formula', type: 'amount', format: EUR, label: 'Buchwert der Zufallsschicht (BV_s)' },
      ],
    },
    {
      id: 'I', title: 'Stichprobe',
      fields: [
        { cell: 'C13', alias: 'randomSampleSize', kind: 'input', type: 'integer', format: INT, label: 'Umfang der Zufallsstichprobe (fachliches Ermessen)', hint: 'Art. 79 Abs. 2 VO (EU) 2021/1060: ausreichend für einen gültigen Bestätigungsvermerk.' },
        { cell: 'C14', alias: 'sampleSize', kind: 'formula', type: 'integer', format: INT, label: 'Gesamtstichprobe (Zufallsstichprobe + umfassende Schicht)' },
        { cell: 'C15', alias: 'minimumCoverage', kind: 'formula', type: 'integer', format: INT, label: 'Mindesterfassung 10 % der Stichprobeneinheiten (aufgerundet)', hint: 'Art. 79 Abs. 2 VO (EU) 2021/1060; Art. 6 Abs. 2 DelVO: Einheiten umfassender Schichten werden eingerechnet. Bei Wechsel nach Art. 6 Abs. 3 bezieht sich der Mindestumfang auf das gesamte Geschäftsjahr.' },
        { cell: 'C16', alias: 'checkCoverage', kind: 'formula', type: 'check', label: 'Prüfung Mindesterfassung' },
      ],
    },
    {
      id: 'J', title: 'Prüfergebnisse',
      fields: [
        { cell: 'C17', alias: 'sampleBookValueSum', kind: 'input', type: 'amount', format: EUR, subsample: 'bookValueSum', label: 'Summe der Buchwerte der Stichprobe der Zufallsschicht (Σ BV_i)' },
        { cell: 'C18', alias: 'sampleErrorSum', kind: 'input', type: 'amount', format: EUR, subsample: 'errorSum', label: 'Summe der Fehler der Stichprobe der Zufallsschicht (Σ E_i)' },
        { cell: 'C19', alias: 'exhaustiveErrors', kind: 'input', type: 'amount', format: EUR, subsample: 'highValueErrors', label: 'Summe der Fehler in der umfassenden Schicht (ΣE_e)' },
      ],
    },
    {
      id: 'K', title: 'Hochrechnung', reference: 'Verhältnisschätzung; Art. 8 Abs. 2',
      fields: [
        { cell: 'C20', alias: 'exhaustiveStratumError', kind: 'formula', type: 'amount', format: EUR, label: 'Fehler der umfassenden Schicht (EE_e)' },
        { cell: 'C21', alias: 'randomStratumError', kind: 'formula', type: 'amount', format: EUR, label: 'Extrapolierter Fehler der Zufallsschicht (EE_s)', formula: 'EE_s = BV_s · Σ E / Σ BV' },
        { cell: 'C22', alias: 'projectedError', kind: 'result', type: 'amount', format: EUR, label: 'Extrapolierter Fehler EE' },
        { cell: 'C23', alias: 'systemicErrors', kind: 'input', type: 'amount', format: EUR, label: 'Abgegrenzte systembedingte Fehler (Betrag)', hint: 'Art. 2 Nr. 20, 21; Art. 8 Abs. 1 DelVO.' },
        { cell: 'C24', alias: 'anomalousErrors', kind: 'input', type: 'amount', format: EUR, label: 'Nicht berichtigte anomale Fehler (Betrag)', hint: 'Art. 2 Nr. 20, 21; Art. 8 Abs. 1 DelVO.' },
        { cell: 'C25', alias: 'projectedErrorRate', kind: 'formula', type: 'percent', format: RATE, label: 'Extrapolierte Zufallsfehlerquote', formula: 'EE / BV' },
        { cell: 'C26', alias: 'totalErrorRate', kind: 'result', type: 'percent', format: RATE, label: 'Gesamtfehlerquote', formula: '(EE + systembedingte + nicht berichtigte anomale Fehler) / BV', hint: 'Art. 8 Abs. 1 DelVO; endgültige Berechnung inkl. TH-Pauschale und Anh. III in Blatt 18.' },
        { cell: 'C27', alias: 'materiality', kind: 'input', type: 'percent', format: RATE, default: 0.02, label: 'Wesentlichkeitsschwelle', hint: 'Anh. I Nr. 1 DelVO.' },
        { cell: 'C28', alias: 'assessment', kind: 'formula', type: 'check', label: 'Würdigung gegen die Wesentlichkeitsschwelle', hint: 'Beim nichtstatistischen Verfahren werden Genauigkeit und obere Fehlergrenze nicht berechnet (Art. 8 Abs. 2).' },
      ],
    },
  ],
  summary: {
    primary: { cell: 'C26', label: 'Gesamtfehlerquote (blattbezogen)', unit: '' },
    rows: [
      { cell: 'C14', label: 'Gesamtstichprobe' },
      { cell: 'C15', label: 'Mindesterfassung (10 %)' },
      { cell: 'C12', label: 'Buchwert der Zufallsschicht' },
      { cell: 'C21', label: 'Extrapolierter Fehler der Zufallsschicht' },
      { cell: 'C22', label: 'Extrapolierter Fehler EE', strong: true },
      { cell: 'C25', label: 'Extrapolierte Zufallsfehlerquote' },
    ],
    gauge: { threshold: 'C27', rate: 'C26' },
  },
}
