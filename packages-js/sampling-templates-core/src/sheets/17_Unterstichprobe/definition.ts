/**
 * Methodendefinition Blatt 17_Unterstichprobe. Erzeugt mit `scripts/generate-definition.mjs`
 * und von Hand geprüft. Die Vorlage ist „je Stichprobeneinheit zu kopieren“; die
 * Webfassung führt dafür eine Liste von Einheiten (`layout: 'list'`). Abschnitt W
 * gibt es in der Vorlage nicht: Er ordnet die Einheit dem Methodenblatt zu
 * (Hinweis der Webfassung, Zellen W5–W10 sind in der Vorlage unbelegt).
 */
import type { MethodDefinition } from '../../model/definition'

export const definition: MethodDefinition = {
  sheet: '17_Unterstichprobe',
  number: '17',
  title: 'Unterstichprobenverfahren – Fehler einer Stichprobeneinheit',
  shortTitle: 'Unterstichproben',
  legalBasis: 'Art. 2 Nr. 12 und 13; Art. 7; Art. 8 Abs. 3 DelVO (EU) 2023/67',
  layout: 'list',
  listColumns: ['C5', 'C6', 'W5', 'W6', 'W7', 'W8'],
  sections: [
    {
      id: 'A', title: 'Stichprobeneinheit',
      fields: [
        { cell: 'C5', alias: 'unitId', kind: 'input', type: 'text', format: '@', label: 'Kennung der Stichprobeneinheit (Vorhaben / Ausgabenerklärung)' },
        { cell: 'C6', alias: 'unitBookValue', kind: 'input', type: 'amount', format: '#,##0.00" €"', label: 'Buchwert der Stichprobeneinheit (BV_i)' },
        { cell: 'C7', alias: 'subUnitCount', kind: 'input', type: 'integer', format: '#,##0', label: 'Anzahl Unterstichprobeneinheiten (z. B. Rechnungen) (M)', hint: 'Art. 2 Nr. 13 DelVO.' },
      ],
    },
    {
      id: 'B', title: 'Variante 1 – Auswahl mit gleicher Wahrscheinlichkeit', reference: 'Verhältnisschätzung',
      fields: [
        { cell: 'C8', alias: 'exhaustiveBookValue', kind: 'input', type: 'amount', format: '#,##0.00" €"', label: 'Buchwert umfassend geprüfter Unterstichprobeneinheiten (fakultativ) (BV_e)' },
        { cell: 'C9', alias: 'exhaustiveErrors', kind: 'input', type: 'amount', format: '#,##0.00" €"', label: 'Fehler in umfassend geprüften Unterstichprobeneinheiten (ΣE_e)' },
        { cell: 'C10', alias: 'subsampleSize', kind: 'input', type: 'integer', format: '#,##0', label: 'Umfang der Unterstichprobe (Zufallsteil)' },
        { cell: 'C11', alias: 'subsampleBookValue', kind: 'input', type: 'amount', format: '#,##0.00" €"', label: 'Summe der Buchwerte der Unterstichprobe (Σ BV_j)' },
        { cell: 'C12', alias: 'subsampleErrors', kind: 'input', type: 'amount', format: '#,##0.00" €"', label: 'Summe der Fehler der Unterstichprobe (Σ E_j)' },
        { cell: 'C13', alias: 'projectedErrorEqual', kind: 'result', type: 'amount', format: '#,##0.00" €"', label: 'Hochgerechneter Fehler der Stichprobeneinheit (E_i)', formula: 'E_i = E_e + (BV_i − BV_e) · Σ E_j / Σ BV_j' },
        { cell: 'C14', alias: 'errorRateEqual', kind: 'formula', type: 'decimal', format: '0.0000', label: 'Fehlerquote der Stichprobeneinheit (für MUS: Eingabe in Σ E_i/BV_i)' },
      ],
    },
    {
      id: 'C', title: 'Variante 2 – PPS-Auswahl', reference: 'MUS-Standardansatz',
      fields: [
        { cell: 'C15', alias: 'ppsSubsampleSize', kind: 'input', type: 'integer', format: '#,##0', label: 'Umfang der Unterstichprobe (inkl. hochwertiger Unterstichprobeneinheiten)' },
        { cell: 'C16', alias: 'ppsCutOff', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Grenzwert (BV_i/m)', hint: 'Art. 7 UAbs. 2 Satz 3: hochwertige Unterstichprobeneinheiten über dem Auswahlintervall werden geprüft.' },
        { cell: 'C17', alias: 'ppsHighValueUnits', kind: 'input', type: 'integer', format: '#,##0', label: 'Anzahl hochwertiger Unterstichprobeneinheiten (m_e)' },
        { cell: 'C18', alias: 'ppsHighValueBookValue', kind: 'input', type: 'amount', format: '#,##0.00" €"', label: 'Buchwert der hochwertigen Unterstichprobeneinheiten (BV_e)' },
        { cell: 'C19', alias: 'ppsHighValueErrors', kind: 'input', type: 'amount', format: '#,##0.00" €"', label: 'Fehler der hochwertigen Unterstichprobeneinheiten (ΣE_e)' },
        { cell: 'C20', alias: 'ppsSamplingInterval', kind: 'formula', type: 'amount', format: '#,##0.00" €"', label: 'Auswahlintervall (SI)', formula: 'SI = (BV_i − BV_e) / (m − m_e)' },
        { cell: 'C21', alias: 'ppsErrorRateSum', kind: 'input', type: 'decimal', format: '0.0000', label: 'Summe der Fehlerquoten der Zufallsauswahl (Σ E_j/BV_j)' },
        { cell: 'C22', alias: 'projectedErrorPps', kind: 'result', type: 'amount', format: '#,##0.00" €"', label: 'Hochgerechneter Fehler der Stichprobeneinheit (E_i)', formula: 'E_i = ΣE_e + SI · Σ E_j/BV_j' },
        { cell: 'C23', alias: 'errorRatePps', kind: 'formula', type: 'decimal', format: '0.0000', label: 'Fehlerquote der Stichprobeneinheit (E_i/BV_i)' },
      ],
    },
    {
      id: 'W', title: 'Zuordnung im Methodenblatt', reference: 'Hinweis der Webfassung',
      fields: [
        { cell: 'W5', alias: 'methodStratum', kind: 'input', type: 'choice', options: ['Zufallsschicht', 'hochwertige Einheit'], default: 'Zufallsschicht', web: true, label: 'Schicht der Stichprobeneinheit im Methodenblatt', hint: 'Hochwertige Einheiten gehen mit ihrem Fehler in ΣE_e ein, Einheiten der Zufallsschicht mit ihrer Fehlerquote in Σ E_i/BV_i.' },
        { cell: 'W6', alias: 'variant', kind: 'input', type: 'choice', options: ['Variante 1', 'Variante 2'], default: 'Variante 1', web: true, label: 'Maßgebliche Variante der Unterstichprobe', hint: 'Variante 1: Auswahl mit gleicher Wahrscheinlichkeit; Variante 2: PPS-Auswahl.' },
        { cell: 'W9', alias: 'methodStratumNumber', kind: 'input', type: 'integer', format: '0', web: true, label: 'Nummer der Schicht im Methodenblatt (nur geschichtete Verfahren)', hint: 'Von den geschichteten Verfahren übernimmt derzeit Blatt 04 die Summen je Schicht; ohne Nummer wird die Einheit dort nicht übernommen. In den Blättern 06, 09, 11, 14 und 16 sind die Summen von Hand einzutragen.' },
        { cell: 'W10', alias: 'methodPeriod', kind: 'input', type: 'integer', format: '0', web: true, label: 'Stichprobenzeitraum im Methodenblatt (nur Verfahren mit mehreren Zeiträumen)', hint: 'Dient der Zuordnung der Einheit zu einem Zeitraum (1, 2 oder 3). Die Verfahren mit mehreren Zeiträumen (Blätter 05–07 und 10–12) übernehmen derzeit keine Summen aus den Unterstichproben; sie sind dort von Hand einzutragen.' },
        { cell: 'W7', alias: 'unitError', kind: 'result', type: 'amount', format: '#,##0.00" €"', web: true, label: 'Maßgeblicher hochgerechneter Fehler (E_i)' },
        { cell: 'W8', alias: 'unitErrorRate', kind: 'result', type: 'decimal', format: '0.0000', web: true, label: 'Maßgebliche Fehlerquote (E_i/BV_i)' },
      ],
    },
  ],
  summary: { primary: { cell: 'W7', label: 'Maßgeblicher hochgerechneter Fehler der Einheit', unit: '' }, rows: [{ cell: 'W8', label: 'Fehlerquote der Einheit', strong: true }, { cell: 'C13', label: 'Variante 1: hochgerechneter Fehler' }, { cell: 'C22', label: 'Variante 2: hochgerechneter Fehler' }] },
}
