/**
 * Methodendefinition Blatt 15_NS_PPS. Erzeugt mit `scripts/generate-definition.mjs`
 * aus der Zellbeschreibung der Vorlage und von Hand geprüft: Abschnitte,
 * Reihenfolge, Zellen, Zahlenformate und Fundstellen (Spalte D) entsprechen der
 * Vorlage; eingebettete Formeln stehen als Kurzschreibweise in `formula`.
 */
import type { MethodDefinition } from '../../model/definition'

const EUR = '#,##0.00" €"'
const INT = '#,##0'
const RATE = '0.00%'
const DEC4 = '0.0000'

export const definition: MethodDefinition = {
  sheet: '15_NS_PPS',
  number: '15',
  title: 'Nichtstatistisches Verfahren – PPS-Auswahl, nicht geschichtet',
  shortTitle: 'Nichtstatistisch, PPS',
  legalBasis: 'Art. 6 Abs. 1 Buchst. a, Abs. 2 und 3; Art. 8 Abs. 2; Anhang II Nr. 1.1 DelVO (EU) 2023/67',
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
      ],
    },
    {
      id: 'I', title: 'Stichprobe', reference: 'Auswahlansatz nach Art. 5 Abs. 2',
      fields: [
        { cell: 'C10', alias: 'sampleSize', kind: 'input', type: 'integer', format: INT, label: 'Stichprobenumfang (fachliches Ermessen, einschließlich hochwertiger Einheiten)' },
        { cell: 'C11', alias: 'minimumCoverage', kind: 'formula', type: 'integer', format: INT, label: 'Mindesterfassung 10 % der Stichprobeneinheiten (aufgerundet)', hint: 'Art. 79 Abs. 2 VO (EU) 2021/1060; Art. 6 Abs. 2 DelVO: Einheiten umfassender Schichten werden eingerechnet. Bei Wechsel nach Art. 6 Abs. 3 bezieht sich der Mindestumfang auf das gesamte Geschäftsjahr.' },
        { cell: 'C12', alias: 'checkCoverage', kind: 'formula', type: 'check', label: 'Prüfung Mindesterfassung' },
        { cell: 'C13', alias: 'cutOff', kind: 'formula', type: 'amount', format: EUR, label: 'Grenzwert für hochwertige Einheiten (BV1/n1) (BV/n)', hint: 'Art. 5 Abs. 2 UAbs. 2: hochwertige Einheiten über dem Auswahlintervall werden vollständig geprüft.' },
        { cell: 'C14', alias: 'highValueUnits', kind: 'input', type: 'integer', format: INT, label: 'Anzahl hochwertiger Einheiten (BV > Grenzwert) (n_e)' },
        { cell: 'C15', alias: 'highValueBookValue', kind: 'input', type: 'amount', format: EUR, label: 'Buchwert der hochwertigen Einheiten (BV_e)' },
        { cell: 'C16', alias: 'randomStratumBookValue', kind: 'formula', type: 'amount', format: EUR, label: 'Buchwert der Zufallsschicht (niedrigwertige Einheiten) (BV_s)' },
        { cell: 'C17', alias: 'randomStratumUnits', kind: 'formula', type: 'integer', format: INT, label: 'Anzahl der in der Zufallsschicht auszuwählenden Einheiten (n_s)' },
        { cell: 'C18', alias: 'checkMinimumUnits', kind: 'formula', type: 'check', label: 'Mindestens drei Einheiten in der Zufallsschicht' },
        { cell: 'C19', alias: 'samplingInterval', kind: 'formula', type: 'amount', format: EUR, label: 'Auswahlintervall (SI)', formula: 'SI = BV_s / n_s', hint: 'Art. 2 Nr. 9; Art. 5 Abs. 2 UAbs. 2 DelVO.' },
        { cell: 'C20', alias: 'iterationUnits', kind: 'input', type: 'integer', format: INT, label: 'Einheiten der Zufallsschicht mit BV > Auswahlintervall (Iteration)', hint: 'Solche Einheiten sind der hochwertigen Schicht zuzuordnen; Grenzwert und Intervall sind neu zu berechnen.' },
        { cell: 'C21', alias: 'checkIteration', kind: 'formula', type: 'check', label: 'Prüfung Iteration' },
      ],
    },
    {
      id: 'J', title: 'Prüfergebnisse',
      fields: [
        { cell: 'C22', alias: 'highValueErrors', kind: 'input', type: 'amount', format: EUR, subsample: 'highValueErrors', label: 'Summe der Fehler in den hochwertigen Einheiten (ΣE_e)' },
        { cell: 'C23', alias: 'errorRateSum', kind: 'input', type: 'decimal', format: DEC4, subsample: 'errorRateSum', label: 'Summe der Fehlerquoten der Zufallsschicht (Σ E_i/BV_i)' },
      ],
    },
    {
      id: 'K', title: 'Hochrechnung', reference: 'Art. 8 Abs. 2',
      fields: [
        { cell: 'C24', alias: 'exhaustiveStratumError', kind: 'formula', type: 'amount', format: EUR, label: 'Fehler der umfassenden Schicht (EE_e)' },
        { cell: 'C25', alias: 'randomStratumError', kind: 'formula', type: 'amount', format: EUR, label: 'Extrapolierter Fehler (EE_s)', formula: 'EE_s = SI · Σ E/BV' },
        { cell: 'C26', alias: 'projectedError', kind: 'result', type: 'amount', format: EUR, label: 'Extrapolierter Fehler EE' },
        { cell: 'C27', alias: 'systemicErrors', kind: 'input', type: 'amount', format: EUR, label: 'Abgegrenzte systembedingte Fehler (Betrag)', hint: 'Art. 2 Nr. 20, 21; Art. 8 Abs. 1 DelVO.' },
        { cell: 'C28', alias: 'anomalousErrors', kind: 'input', type: 'amount', format: EUR, label: 'Nicht berichtigte anomale Fehler (Betrag)', hint: 'Art. 2 Nr. 20, 21; Art. 8 Abs. 1 DelVO.' },
        { cell: 'C29', alias: 'projectedErrorRate', kind: 'formula', type: 'percent', format: RATE, label: 'Extrapolierte Zufallsfehlerquote', formula: 'EE / BV' },
        { cell: 'C30', alias: 'totalErrorRate', kind: 'result', type: 'percent', format: RATE, label: 'Gesamtfehlerquote', formula: '(EE + systembedingte + nicht berichtigte anomale Fehler) / BV', hint: 'Art. 8 Abs. 1 DelVO; endgültige Berechnung inkl. TH-Pauschale und Anh. III in Blatt 18.' },
        { cell: 'C31', alias: 'materiality', kind: 'input', type: 'percent', format: RATE, default: 0.02, label: 'Wesentlichkeitsschwelle', hint: 'Anh. I Nr. 1 DelVO.' },
        { cell: 'C32', alias: 'assessment', kind: 'formula', type: 'check', label: 'Würdigung gegen die Wesentlichkeitsschwelle', hint: 'Beim nichtstatistischen Verfahren werden Genauigkeit und obere Fehlergrenze nicht berechnet (Art. 8 Abs. 2).' },
      ],
    },
  ],
  summary: {
    primary: { cell: 'C30', label: 'Gesamtfehlerquote (blattbezogen)', unit: '' },
    rows: [
      { cell: 'C10', label: 'Stichprobenumfang' },
      { cell: 'C11', label: 'Mindesterfassung (10 %)' },
      { cell: 'C14', label: 'davon hochwertig' },
      { cell: 'C17', label: 'Zufallsschicht n_s' },
      { cell: 'C19', label: 'Auswahlintervall' },
      { cell: 'C26', label: 'Extrapolierter Fehler EE', strong: true },
      { cell: 'C29', label: 'Extrapolierte Zufallsfehlerquote' },
    ],
    gauge: { threshold: 'C31', rate: 'C30' },
  },
}
