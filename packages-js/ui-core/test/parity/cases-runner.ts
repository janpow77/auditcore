/**
 * Paritätsfälle von RunnerConsole (Vue `RunnerConsole` ↔ React `FlowauditRunnerConsole`).
 * Synthetische Daten, keine Personendaten.
 */
import { createRunnerMemoryPort, type RunnerPort } from '../../src'
import type { ParityCase } from './cases'

export interface RunnerCaseProps {
  port?: RunnerPort | null
  locale?: 'de' | 'en'
}

export const runnerItems = [{ id: 'a', label: 'Eintrag A' }, { id: 'b', label: 'Eintrag B' }]

export const runnerCases: ReadonlyArray<ParityCase<RunnerCaseProps>> = [
  {
    name: 'Einträge aus dem Port',
    props: () => ({ port: createRunnerMemoryPort(runnerItems) }),
    expect: { texts: ['Eintrag A'], roles: [['button', 'Eintrag B']], counts: { li: 2, '[aria-pressed="true"]': 0 } },
  },
  {
    name: 'leer',
    props: () => ({ port: createRunnerMemoryPort([]) }),
    expect: { texts: ['Keine Einträge vorhanden.'], counts: { li: 0 } },
  },
  {
    name: 'Fehler des Ports, englisch',
    props: () => ({ port: { list: async () => { throw new Error('offline') } }, locale: 'en' }),
    expect: { texts: ['Request rejected: offline'], counts: { '[role="alert"]': 1 } },
  },
]
