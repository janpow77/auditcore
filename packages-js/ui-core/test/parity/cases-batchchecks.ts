/**
 * Paritätsfälle der Bestandsprüfung (Vue `BatchChecks` ↔ React
 * `FlowauditBatchChecks`). Antworten des echten Python-Dienstes für den
 * synthetischen Beispielbestand, keine Personendaten.
 */
import type { BatchchecksAnswer, BatchchecksPort } from '../../src'
import { batchAnswer, batchAnswerPlain, fakeBatchchecksPort } from '../batchchecks/fake-port'
import type { ParityCase } from './cases'

export interface BatchchecksCaseProps {
  port?: BatchchecksPort | null
  result?: BatchchecksAnswer | null
  locale?: 'de' | 'en'
}

export const batchchecksCases: ReadonlyArray<ParityCase<BatchchecksCaseProps>> = [
  {
    name: 'Katalog geladen, Eingabe bereit',
    props: () => ({ port: fakeBatchchecksPort() }),
    expect: {
      texts: ['Bestand einlesen', 'höchstens 5000 Belege', 'Ergänzungsprüfungen ERG-01 und ERG-02'],
      roles: [['button', 'Bestand prüfen'], ['textbox', 'Ausgewiesenes Gesamtvolumen in EUR (für C-08)']],
      counts: { 'input[type="file"]': 1, fieldset: 0, '[data-testid="batchchecks-result"]': 0 },
    },
  },
  { name: 'ohne Port', props: () => ({}), expect: { texts: ['Kein Port übergeben'], counts: { form: 0 } } },
  {
    name: 'Fehler beim Laden',
    props: () => ({ port: fakeBatchchecksPort({ failing: 'catalogue' }) }),
    expect: { texts: ['Anfrage abgelehnt: Dienst nicht erreichbar'], counts: { '[role="alert"]': 1, form: 0 } },
  },
  {
    name: 'Ergebnis mit Blockade, Regeln und Befunden',
    props: () => ({ port: fakeBatchchecksPort(), result: batchAnswer }),
    expect: {
      texts: ['Blockade', '10 Beleg(e) geprüft', 'manuelle Freigabe erforderlich', 'B-003, B-004', 'Gesamtbestand', 'Nummernlücken bei Lieferant'],
      roles: [['table', /.*/], ['combobox', 'Befunde der Regel']],
      counts: { '[data-testid="batchchecks-rules"] tbody tr': 17, '[data-testid="batchchecks-findings"] tbody tr': batchAnswer.findings.length, '[data-testid="batchchecks-export-csv"]': 0 },
    },
  },
  {
    name: 'Ergebnis ohne Ergänzungsprüfungen, englisch',
    props: () => ({ port: fakeBatchchecksPort(), result: batchAnswerPlain, locale: 'en' }),
    expect: {
      texts: ['Result', 'Warning', 'not checked', 'Nicht geprüft: Ergänzungsprüfungen abgeschaltet.'],
      counts: { '[data-testid="batchchecks-findings"] tbody tr': batchAnswerPlain.findings.length, '[role="alert"]': 0 },
    },
  },
]
