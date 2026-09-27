/**
 * Paritätsfälle der Hochrechnung (Vue `ExtrapolationPanel` ↔ React
 * `FlowauditExtrapolation`). Port mit Antworten des echten Python-Backends,
 * synthetische Daten.
 */
import type { ExtrapolationPort, StratumInput, UnitInput } from '../../src'
import { fakeExtrapolationPort, fixtureStrata, fixtureUnits, groupsFixture, multistageFixture, periodsFixture } from '../extrapolation/fake-port'
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
    name: 'mehrere Zeiträume mit Teilstichprobe (Leitfaden 7.3, 7.6)',
    props: () => ({ port: fakeExtrapolationPort(), strata: periodsFixture.strata, units: periodsFixture.units }),
    expect: {
      texts: ['Aufbau der Stichprobe', 'Teilstichprobe'],
      roles: [['combobox', 'Zeitraum, Zeile 1'], ['textbox', 'Zeitraum, Zeile 2'], ['button', 'Teilstichprobe bearbeiten, Zeile 1'], ['button', 'Teilstichprobe anlegen, Zeile 2']],
      counts: { '[data-testid="extrapolation-strata"] tbody tr': 2, '[data-testid="extrapolation-units"] tbody tr': 6, '[data-testid="extrapolation-subsample"]': 0 },
    },
  },
  {
    name: 'Gruppe von Programmen (Leitfaden 7.8)',
    props: () => ({ port: fakeExtrapolationPort(), strata: groupsFixture.strata, units: groupsFixture.units }),
    expect: {
      texts: ['Programm'],
      roles: [['textbox', 'Programm, Zeile 2'], ['textbox', 'Programm, Zeile 1']],
      counts: { '[data-testid="extrapolation-units"] tbody tr': 9 },
    },
  },
  {
    name: 'Programme über Zeiträume, dreistufige Teilstichprobe (Leitfaden 6.3.4, 6.5.3, 7.8)',
    props: () => ({ port: fakeExtrapolationPort(), strata: multistageFixture.strata, units: multistageFixture.units }),
    expect: {
      texts: ['Programm (optional)'],
      roles: [['textbox', 'Programm (optional), Zeile 3'], ['button', 'Teilstichprobe bearbeiten, Zeile 1']],
      counts: { '[data-testid="extrapolation-strata"] tbody tr': 4, '[data-testid="extrapolation-units"] tbody tr': 8 },
    },
  },
  {
    name: 'englisch mit Rückfall auf Deutsch',
    props: () => ({ port: fakeExtrapolationPort(), strata: fixtureStrata, units: fixtureUnits, locale: 'en' }),
    expect: { texts: ['Verfahren'], roles: [['button', 'Project'], ['combobox', 'Projection method']] },
  },
]
