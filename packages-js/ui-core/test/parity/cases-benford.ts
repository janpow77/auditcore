/**
 * Paritätsfälle der Benford-Analyse (Vue `BenfordPanel` ↔ React
 * `FlowauditBenford`). Port mit Antworten des echten Python-Backends,
 * synthetische Werte.
 */
import type { BenfordPort } from '../../src'
import { fakeBenfordPort } from '../sampling/fake-port'
import type { ParityCase } from './cases'

export interface BenfordCaseProps {
  port?: BenfordPort | null
  values?: readonly (number | null)[]
  locale?: 'de' | 'en'
}

export const benfordCases: ReadonlyArray<ParityCase<BenfordCaseProps>> = [
  {
    name: 'übergebene Werte, erster Test vorgewählt',
    props: () => ({ port: fakeBenfordPort(), values: [123, 45.6, null, 0] }),
    expect: {
      texts: ['4 Werte übernommen', 'Quelle des Profils'],
      roles: [['combobox', 'Test'], ['combobox', 'Bewertungsprofil'], ['button', 'Analysieren']],
      counts: { 'fieldset': 0, '[data-testid="benford-chart"]': 0 },
    },
  },
  {
    name: 'ohne Werte',
    props: () => ({ port: fakeBenfordPort() }),
    expect: { texts: ['Keine Werte übergeben.'], counts: { 'input[type="file"]': 1 } },
  },
  {
    name: 'Fehler beim Laden',
    props: () => ({ port: fakeBenfordPort('profiles') }),
    expect: { texts: ['Anfrage abgelehnt: Dienst nicht erreichbar'], counts: { '[role="alert"]': 1, 'form': 0 } },
  },
  {
    name: 'englisch mit Rückfall auf Deutsch',
    props: () => ({ port: fakeBenfordPort(), values: [12, 34], locale: 'en' }),
    expect: { texts: ['2 Werte übernommen'], roles: [['button', 'Analyse'], ['combobox', 'Assessment profile']] },
  },
]
