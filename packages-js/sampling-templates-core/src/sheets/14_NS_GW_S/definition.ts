/**
 * Methodendefinition Blatt 14_NS_GW_S. Erzeugt mit `scripts/generate-definition.mjs`
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

export const definition: MethodDefinition = {
  sheet: '14_NS_GW_S',
  number: '14',
  title: 'Nichtstatistisches Verfahren – Auswahl mit gleicher Wahrscheinlichkeit, geschichtet',
  shortTitle: 'Nichtstatistisch, gleiche Wahrscheinlichkeit, geschichtet',
  legalBasis: 'Art. 6 Abs. 1 UAbs. 2 und 3, Abs. 2; Art. 8 Abs. 2; Anhang II Nr. 2.1 (geschichtet) DelVO (EU) 2023/67',
  sections: [
    {
      id: 'H', title: 'Zu prüfende Grundgesamtheit', reference: 'Art. 3, Art. 4',
      fields: [
        { cell: 'C4', alias: 'programme', kind: 'input', type: 'text', format: '@', label: 'Programm(e) / CCI', hint: 'Art. 3 Abs. 1 und 2 DelVO.' },
        { cell: 'C5', alias: 'accountingYear', kind: 'input', type: 'text', format: '@', label: 'Geschäftsjahr' },
        { cell: 'C6', alias: 'samplingUnit', kind: 'input', type: 'text', format: '@', label: 'Stichprobeneinheit (z. B. Vorhaben, Ausgabenerklärung, Zahlungsantrag)' },
        { cell: 'C8', alias: 'exhaustiveBookValue', kind: 'input', type: 'amount', format: EUR, label: 'Buchwert der umfassenden Schicht (fakultativ) (BV_e)' },
        { cell: 'C9', alias: 'exhaustiveUnits', kind: 'input', type: 'integer', format: INT, label: 'Anzahl Einheiten der umfassenden Schicht (N_e)' },
        { cell: 'D11', alias: 'stratumUnits', kind: 'input', type: 'integer', format: INT, columns: STRATA_COLUMNS, total: 'C11', label: 'Anzahl Einheiten je Schicht (N_h)', hint: 'Stichprobenzeiträume können wie Schichten erfasst werden (Art. 6 Abs. 1 UAbs. 2), da sich die Hochrechnung je Zeitraum additiv zusammensetzt.' },
        { cell: 'D12', alias: 'stratumBookValue', kind: 'input', type: 'amount', format: EUR, columns: STRATA_COLUMNS, total: 'C12', label: 'Buchwert je Schicht (BV_h)' },
        { cell: 'C13', alias: 'bookValue', kind: 'formula', type: 'amount', format: EUR, label: 'Buchwert der Grundgesamtheit (BV)' },
        { cell: 'C14', alias: 'populationSize', kind: 'formula', type: 'integer', format: INT, label: 'Anzahl Einheiten der Grundgesamtheit (N)' },
        { cell: 'C15', alias: 'checkAdmissibility', kind: 'formula', type: 'check', label: 'Zulässigkeit des nichtstatistischen Verfahrens (N < 300)' },
      ],
    },
    {
      id: 'I', title: 'Stichprobe',
      fields: [
        { cell: 'C16', alias: 'randomSampleSize', kind: 'input', type: 'integer', format: INT, label: 'Umfang der Zufallsstichprobe (fachliches Ermessen)' },
        { cell: 'D18', alias: 'stratumSampleSize', kind: 'formula', type: 'integer', format: INT, columns: STRATA_COLUMNS, total: 'C18', label: 'Umfang je Schicht', formula: 'n_h = N_h/N · n', interpretation: NONSTATISTICAL_ALLOCATION_INTERPRETATION },
        { cell: 'C19', alias: 'sampleSize', kind: 'formula', type: 'integer', format: INT, label: 'Gesamtstichprobe' },
        { cell: 'C20', alias: 'minimumCoverage', kind: 'formula', type: 'integer', format: INT, label: 'Mindesterfassung 10 % der Stichprobeneinheiten (aufgerundet)', hint: 'Art. 79 Abs. 2 VO (EU) 2021/1060; Art. 6 Abs. 2 DelVO: Einheiten umfassender Schichten werden eingerechnet. Bei Wechsel nach Art. 6 Abs. 3 bezieht sich der Mindestumfang auf das gesamte Geschäftsjahr.' },
        { cell: 'C21', alias: 'checkCoverage', kind: 'formula', type: 'check', label: 'Prüfung Mindesterfassung' },
      ],
    },
    {
      id: 'J', title: 'Prüfergebnisse',
      fields: [
        { cell: 'C22', alias: 'exhaustiveErrors', kind: 'input', type: 'amount', format: EUR, label: 'Summe der Fehler in der umfassenden Schicht (ΣE_e)' },
        { cell: 'D24', alias: 'stratumSampleBookValueSum', kind: 'input', type: 'amount', format: EUR, columns: STRATA_COLUMNS, total: 'C24', label: 'Summe der Buchwerte der Stichprobe (Σ BV_i)' },
        { cell: 'D25', alias: 'stratumSampleErrorSum', kind: 'input', type: 'amount', format: EUR, columns: STRATA_COLUMNS, total: 'C25', label: 'Summe der Fehler der Stichprobe (Σ E_i)' },
      ],
    },
    {
      id: 'K', title: 'Hochrechnung', reference: 'Verhältnisschätzung; Art. 8 Abs. 2',
      fields: [
        { cell: 'D27', alias: 'stratumRandomError', kind: 'formula', type: 'amount', format: EUR, columns: STRATA_COLUMNS, total: 'C27', label: 'Extrapolierter Fehler je Schicht (EE_sh)' },
        { cell: 'C28', alias: 'exhaustiveStratumError', kind: 'formula', type: 'amount', format: EUR, label: 'Fehler der umfassenden Schicht (EE_e)' },
        { cell: 'C29', alias: 'projectedError', kind: 'result', type: 'amount', format: EUR, label: 'Extrapolierter Fehler EE' },
        { cell: 'C30', alias: 'systemicErrors', kind: 'input', type: 'amount', format: EUR, label: 'Abgegrenzte systembedingte Fehler (Betrag)', hint: 'Art. 2 Nr. 20, 21; Art. 8 Abs. 1 DelVO.' },
        { cell: 'C31', alias: 'anomalousErrors', kind: 'input', type: 'amount', format: EUR, label: 'Nicht berichtigte anomale Fehler (Betrag)', hint: 'Art. 2 Nr. 20, 21; Art. 8 Abs. 1 DelVO.' },
        { cell: 'C32', alias: 'projectedErrorRate', kind: 'formula', type: 'percent', format: RATE, label: 'Extrapolierte Zufallsfehlerquote', formula: 'EE / BV' },
        { cell: 'C33', alias: 'totalErrorRate', kind: 'result', type: 'percent', format: RATE, label: 'Gesamtfehlerquote', formula: '(EE + systembedingte + nicht berichtigte anomale Fehler) / BV', hint: 'Art. 8 Abs. 1 DelVO; endgültige Berechnung inkl. TH-Pauschale und Anh. III in Blatt 18.' },
        { cell: 'C34', alias: 'materiality', kind: 'input', type: 'percent', format: RATE, default: 0.02, label: 'Signifikanzschwelle', hint: 'Anh. I Nr. 1 DelVO.' },
        { cell: 'C35', alias: 'assessment', kind: 'formula', type: 'check', label: 'Würdigung gegen die Signifikanzschwelle', hint: 'Beim nichtstatistischen Verfahren werden Genauigkeit und obere Fehlergrenze nicht berechnet (Art. 8 Abs. 2).' },
      ],
    },
  ],
  summary: {
    primary: { cell: 'C33', label: 'Gesamtfehlerquote (blattbezogen)', unit: '' },
    rows: [
      { cell: 'C14', label: 'Einheiten der Grundgesamtheit (N)' },
      { cell: 'C19', label: 'Gesamtstichprobe' },
      { cell: 'C20', label: 'Mindesterfassung (10 %)' },
      { cell: 'C27', label: 'Extrapolierter Fehler der Zufallsschichten' },
      { cell: 'C29', label: 'Extrapolierter Fehler EE', strong: true },
      { cell: 'C32', label: 'Extrapolierte Zufallsfehlerquote' },
    ],
    gauge: { threshold: 'C34', rate: 'C33' },
  },
}
