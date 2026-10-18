/**
 * Methodendefinition Blatt 16_NS_PPS_S. Erzeugt mit `scripts/generate-definition.mjs`
 * aus der Zellbeschreibung der Vorlage und von Hand geprüft: Abschnitte,
 * Reihenfolge, Zellen, Zahlenformate und Fundstellen (Spalte K) entsprechen der
 * Vorlage; eingebettete Formeln stehen als Kurzschreibweise in `formula`.
 * Schichtzeilen tragen `columns: STRATA_COLUMNS`: `cell` ist die Zelle der ersten
 * Schicht (Spalte D), `total` die Summenzelle in Spalte C, soweit die Vorlage eine hat.
 * Der Hinweis in Zelle B7 der Vorlage (Stichprobenzeiträume als Schichten) hat dort
 * keine eigene Wertzelle; er steht als Erläuterung an der ersten Schichtzeile.
 */
import type { MethodDefinition } from '../../model/definition'
import { STRATA_COLUMNS } from '../../model/strata'
import { NONSTATISTICAL_ALLOCATION_INTERPRETATION } from '../shared/interpretations'

const EUR = '#,##0.00" €"'
const INT = '#,##0'
const RATE = '0.00%'
const DEC4 = '0.0000'

export const definition: MethodDefinition = {
  sheet: '16_NS_PPS_S',
  number: '16',
  title: 'Nichtstatistisches Verfahren – PPS-Auswahl, geschichtet',
  shortTitle: 'Nichtstatistisch, PPS, geschichtet',
  legalBasis: 'Art. 6 Abs. 1 Buchst. a und UAbs. 2–3, Abs. 2; Art. 8 Abs. 2; Anhang II Nr. 1.1 (geschichtet) DelVO (EU) 2023/67',
  sections: [
    {
      id: 'H', title: 'Zu prüfende Grundgesamtheit', reference: 'Art. 3, Art. 4',
      fields: [
        { cell: 'C4', alias: 'programme', kind: 'input', type: 'text', format: '@', label: 'Programm(e) / CCI', hint: 'Art. 3 Abs. 1 und 2 DelVO.' },
        { cell: 'C5', alias: 'accountingYear', kind: 'input', type: 'text', format: '@', label: 'Geschäftsjahr' },
        { cell: 'C6', alias: 'samplingUnit', kind: 'input', type: 'text', format: '@', label: 'Stichprobeneinheit (z. B. Vorhaben, Ausgabenerklärung, Zahlungsantrag)' },
        { cell: 'D9', alias: 'stratumBookValue', kind: 'input', type: 'amount', format: EUR, columns: STRATA_COLUMNS, total: 'C9', label: 'Buchwert je Schicht (BV_h)', hint: 'Stichprobenzeiträume können wie Schichten erfasst werden (Art. 6 Abs. 1 UAbs. 2).' },
        { cell: 'D10', alias: 'stratumUnits', kind: 'input', type: 'integer', format: INT, columns: STRATA_COLUMNS, total: 'C10', label: 'Anzahl Einheiten je Schicht (N_h)' },
        { cell: 'C11', alias: 'populationSize', kind: 'formula', type: 'integer', format: INT, label: 'Anzahl Einheiten der Grundgesamtheit (N)' },
        { cell: 'C12', alias: 'checkAdmissibility', kind: 'formula', type: 'check', label: 'Zulässigkeit des nichtstatistischen Verfahrens (N < 300)' },
      ],
    },
    {
      id: 'I', title: 'Stichprobe',
      fields: [
        { cell: 'C13', alias: 'sampleSize', kind: 'input', type: 'integer', format: INT, label: 'Stichprobenumfang (fachliches Ermessen)' },
        { cell: 'D15', alias: 'stratumSampleSize', kind: 'formula', type: 'integer', format: INT, columns: STRATA_COLUMNS, total: 'C15', label: 'Umfang je Schicht', formula: 'n_h = BV_h/BV · n', interpretation: NONSTATISTICAL_ALLOCATION_INTERPRETATION },
        { cell: 'C16', alias: 'minimumCoverage', kind: 'formula', type: 'integer', format: INT, label: 'Mindesterfassung 10 % der Stichprobeneinheiten (aufgerundet)', hint: 'Art. 79 Abs. 2 VO (EU) 2021/1060; Art. 6 Abs. 2 DelVO: Einheiten umfassender Schichten werden eingerechnet. Bei Wechsel nach Art. 6 Abs. 3 bezieht sich der Mindestumfang auf das gesamte Geschäftsjahr.' },
        { cell: 'C17', alias: 'checkCoverage', kind: 'formula', type: 'check', label: 'Prüfung Mindesterfassung' },
        { cell: 'D18', alias: 'stratumCutOff', kind: 'formula', type: 'amount', format: EUR, columns: STRATA_COLUMNS, label: 'Grenzwert je Schicht (BV/n)' },
        { cell: 'D19', alias: 'stratumHighValueUnits', kind: 'input', type: 'integer', format: INT, columns: STRATA_COLUMNS, total: 'C19', label: 'Anzahl hochwertiger Einheiten (n_eh)' },
        { cell: 'D20', alias: 'stratumHighValueBookValue', kind: 'input', type: 'amount', format: EUR, columns: STRATA_COLUMNS, total: 'C20', label: 'Buchwert der hochwertigen Einheiten (BV_eh)' },
        { cell: 'D21', alias: 'stratumRandomBookValue', kind: 'formula', type: 'amount', format: EUR, columns: STRATA_COLUMNS, total: 'C21', label: 'Buchwert der Zufallsschicht (BV_hs)' },
        { cell: 'D22', alias: 'stratumRandomUnits', kind: 'formula', type: 'integer', format: INT, columns: STRATA_COLUMNS, total: 'C22', label: 'Auszuwählende Zufallseinheiten (n_hs)' },
        { cell: 'D23', alias: 'stratumSamplingInterval', kind: 'formula', type: 'amount', format: EUR, columns: STRATA_COLUMNS, label: 'Auswahlintervall (SI_h)' },
      ],
    },
    {
      id: 'J', title: 'Prüfergebnisse',
      fields: [
        { cell: 'D25', alias: 'stratumHighValueErrors', kind: 'input', type: 'amount', format: EUR, columns: STRATA_COLUMNS, total: 'C25', label: 'Summe der Fehler in hochwertigen Einheiten (ΣE_eh)' },
        { cell: 'D26', alias: 'stratumErrorRateSum', kind: 'input', type: 'decimal', format: DEC4, columns: STRATA_COLUMNS, total: 'C26', label: 'Summe der Fehlerquoten der Zufallsschicht (Σ E/BV)' },
      ],
    },
    {
      id: 'K', title: 'Hochrechnung', reference: 'Art. 8 Abs. 2',
      fields: [
        { cell: 'D28', alias: 'stratumProjectedError', kind: 'formula', type: 'amount', format: EUR, columns: STRATA_COLUMNS, total: 'C28', label: 'Extrapolierter Fehler je Schicht (EE_h)' },
        { cell: 'C29', alias: 'exhaustiveStratumError', kind: 'formula', type: 'amount', format: EUR, label: 'Fehler der umfassenden Schichten (EE_e)' },
        { cell: 'C30', alias: 'projectedError', kind: 'result', type: 'amount', format: EUR, label: 'Extrapolierter Fehler EE' },
        { cell: 'C31', alias: 'systemicErrors', kind: 'input', type: 'amount', format: EUR, label: 'Abgegrenzte systembedingte Fehler (Betrag)', hint: 'Art. 2 Nr. 20, 21; Art. 8 Abs. 1 DelVO.' },
        { cell: 'C32', alias: 'anomalousErrors', kind: 'input', type: 'amount', format: EUR, label: 'Nicht berichtigte anomale Fehler (Betrag)', hint: 'Art. 2 Nr. 20, 21; Art. 8 Abs. 1 DelVO.' },
        { cell: 'C33', alias: 'projectedErrorRate', kind: 'formula', type: 'percent', format: RATE, label: 'Extrapolierte Zufallsfehlerquote', formula: 'EE / BV' },
        { cell: 'C34', alias: 'totalErrorRate', kind: 'result', type: 'percent', format: RATE, label: 'Gesamtfehlerquote', formula: '(EE + systembedingte + nicht berichtigte anomale Fehler) / BV', hint: 'Art. 8 Abs. 1 DelVO; endgültige Berechnung inkl. TH-Pauschale und Anh. III in Blatt 18.' },
        { cell: 'C35', alias: 'materiality', kind: 'input', type: 'percent', format: RATE, default: 0.02, label: 'Signifikanzschwelle', hint: 'Anh. I Nr. 1 DelVO.' },
        { cell: 'C36', alias: 'assessment', kind: 'formula', type: 'check', label: 'Würdigung gegen die Signifikanzschwelle', hint: 'Beim nichtstatistischen Verfahren werden Genauigkeit und obere Fehlergrenze nicht berechnet (Art. 8 Abs. 2).' },
      ],
    },
  ],
  summary: {
    primary: { cell: 'C34', label: 'Gesamtfehlerquote (blattbezogen)', unit: '' },
    rows: [
      { cell: 'C11', label: 'Einheiten der Grundgesamtheit (N)' },
      { cell: 'C15', label: 'Summe der Schichtumfänge n_h' },
      { cell: 'C16', label: 'Mindesterfassung (10 %)' },
      { cell: 'C19', label: 'davon hochwertig' },
      { cell: 'C22', label: 'Zufallsschichten n_hs' },
      { cell: 'C30', label: 'Extrapolierter Fehler EE', strong: true },
      { cell: 'C33', label: 'Extrapolierte Zufallsfehlerquote' },
    ],
    gauge: { threshold: 'C35', rate: 'C34' },
  },
}
