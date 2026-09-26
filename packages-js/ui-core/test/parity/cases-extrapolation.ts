/**
 * Paritätsfälle der Hochrechnung (Vue `ExtrapolationPanel` ↔ React
 * `FlowauditExtrapolation`). Port mit Antworten des echten Python-Backends,
 * synthetische Daten.
 */
import type { ExtrapolationPort, StratumInput, UnitInput } from '../../src'
import { fakeExtrapolationPort, fixtureStrata, fixtureUnits } from '../extrapolation/fake-port'
import type { ParityCase } from './cases'

export interface ExtrapolationCaseProps {
  port?: ExtrapolationPort | null
  strata?: readonly StratumInput[]
  units?: readonly UnitInput[]
  locale?: 'de' | 'en'
}

export const extrapolationCases: ReadonlyArray<ParityCase<ExtrapolationCaseProps>> = [
  {
    name: 'Eingaben aus Eigenschaften, keine Methode vorgewählt',
    props: () => ({ port: fakeExtrapolationPort(), strata: fixtureStrata, units: fixtureUnits }),
    expect: {
      texts: ['Verfahren', 'Schichten der Grundgesamtheit', 'Wesentlichkeitsschwelle (%)'],
      roles: [['combobox', 'Hochrechnungsmethode'], ['button', 'Hochrechnen'], ['textbox', 'Kennung, Zeile 1'], ['checkbox', 'Vollerhebung, Zeile 5']],
      counts: { '[data-testid="extrapolation-units"] tbody tr': 5, '[data-testid="extrapolation-strata"] tbody tr': 1, 'optgroup': 2 },
    },
  },
  {
    name: 'ohne Eingaben',
    props: () => ({ port: fakeExtrapolationPort() }),
    expect: { texts: ['Noch keine Einheiten erfasst.'], counts: { '[data-testid="extrapolation-units"]': 0, '[data-testid="extrapolation-strata"] tbody tr': 1 } },
  },
  {
    name: 'Fehler beim Laden',
    props: () => ({ port: fakeExtrapolationPort('profiles', 'Dienst nicht erreichbar') }),
    expect: { texts: ['Anfrage abgelehnt: Dienst nicht erreichbar'], counts: { '[role="alert"]': 1, 'select': 0 } },
  },
  {
    name: 'englisch mit Rückfall auf Deutsch',
    props: () => ({ port: fakeExtrapolationPort(), strata: fixtureStrata, units: fixtureUnits, locale: 'en' }),
    expect: { texts: ['Verfahren'], roles: [['button', 'Project'], ['combobox', 'Projection method']] },
  },
]
