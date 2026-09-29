/**
 * Paritätsfälle von AccountWorkspace (Vue `AccountWorkspace` ↔ React `FlowauditAccountWorkspace`).
 * Synthetische Daten, keine Personendaten.
 */
import { createAccountMemoryPort, type AccountPort } from '../../src'
import type { ParityCase } from './cases'

export interface AccountCaseProps {
  port?: AccountPort | null
  locale?: 'de' | 'en'
}

export const accountItems = [{ id: 'a', label: 'Eintrag A' }, { id: 'b', label: 'Eintrag B' }]

export const accountCases: ReadonlyArray<ParityCase<AccountCaseProps>> = [
  {
    name: 'Einträge aus dem Port',
    props: () => ({ port: createAccountMemoryPort(accountItems) }),
    expect: { texts: ['Eintrag A'], roles: [['button', 'Eintrag B']], counts: { li: 2, '[aria-pressed="true"]': 0 } },
  },
  {
    name: 'leer',
    props: () => ({ port: createAccountMemoryPort([]) }),
    expect: { texts: ['Keine Einträge vorhanden.'], counts: { li: 0 } },
  },
  {
    name: 'Fehler des Ports, englisch',
    props: () => ({ port: { ...createAccountMemoryPort([]), list: async () => { throw new Error('offline') } }, locale: 'en' }),
    expect: { texts: ['Request rejected: offline'], counts: { '[role="alert"]': 1 } },
  },
]
