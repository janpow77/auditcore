/**
 * Paritätsfälle von BatchChecks (Vue `BatchChecks` ↔ React `FlowauditBatchChecks`).
 * Synthetische Daten, keine Personendaten.
 */
import { createBatchchecksMemoryPort, type BatchchecksPort } from '../../src'
import type { ParityCase } from './cases'

export interface BatchchecksCaseProps {
  port?: BatchchecksPort | null
  locale?: 'de' | 'en'
}

export const batchchecksItems = [{ id: 'a', label: 'Eintrag A' }, { id: 'b', label: 'Eintrag B' }]

export const batchchecksCases: ReadonlyArray<ParityCase<BatchchecksCaseProps>> = [
  {
    name: 'Einträge aus dem Port',
    props: () => ({ port: createBatchchecksMemoryPort(batchchecksItems) }),
    expect: { texts: ['Eintrag A'], roles: [['button', 'Eintrag B']], counts: { li: 2, '[aria-pressed="true"]': 0 } },
  },
  {
    name: 'leer',
    props: () => ({ port: createBatchchecksMemoryPort([]) }),
    expect: { texts: ['Keine Einträge vorhanden.'], counts: { li: 0 } },
  },
  {
    name: 'Fehler des Ports, englisch',
    props: () => ({ port: { list: async () => { throw new Error('offline') } }, locale: 'en' }),
    expect: { texts: ['Request rejected: offline'], counts: { '[role="alert"]': 1 } },
  },
]
