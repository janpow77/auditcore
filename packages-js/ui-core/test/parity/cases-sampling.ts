/**
 * Paritätsfälle des Stichprobenrechners (Vue `SamplingPanel` ↔ React
 * `FlowauditSampling`). Port mit Antworten des echten Python-Backends,
 * synthetische Belege, keine Personendaten.
 */
import type { PopulationItem, SamplingPort } from '../../src'
import { fakeSamplingPort, populationItems } from '../sampling/fake-port'
import type { ParityCase } from './cases'

export interface SamplingCaseProps {
  port?: SamplingPort | null
  items?: readonly PopulationItem[]
  locale?: 'de' | 'en'
}

export const samplingCases: ReadonlyArray<ParityCase<SamplingCaseProps>> = [
  {
    name: 'empfohlene Methode mit geschichteter Grundgesamtheit',
    props: () => ({ port: fakeSamplingPort(), items: populationItems }),
    expect: {
      texts: ['Empfohlen', 'portal.mus_poisson', '30 Elemente', '2 Schichten', 'Leer lassen: Der Server erzeugt einen Seed'],
      roles: [['combobox', 'Methode'], ['combobox', 'Konfidenzniveau'], ['combobox', 'Aufteilung auf Schichten'], ['button', 'Stichprobenumfang berechnen'], ['button', 'Aus Grundgesamtheit übernehmen'], ['button', 'Stichprobe ziehen']],
      counts: { '.fa-sampling__card': 4, 'optgroup': 2, '[data-testid="sampling-variant"]': 1, '[data-testid="sampling-redraw"]': 0 },
    },
  },
  {
    name: 'ohne Grundgesamtheit',
    props: () => ({ port: fakeSamplingPort() }),
    expect: {
      texts: ['Keine Grundgesamtheit übergeben.'],
      counts: { '[data-testid="sampling-population"]': 0, '[data-testid="sampling-allocation"]': 0, 'input[type="file"]': 1 },
    },
  },
  {
    name: 'Fehler beim Laden der Profile',
    props: () => ({ port: fakeSamplingPort('profiles', 'Dienst nicht erreichbar') }),
    expect: { texts: ['Anfrage abgelehnt: Dienst nicht erreichbar'], counts: { '[role="alert"]': 1, '.fa-sampling__card': 0 } },
  },
  { name: 'ohne Port', props: () => ({}), expect: { counts: { '.fa-sampling__card': 0, '[role="alert"]': 0 } } },
  {
    name: 'englisch mit Rückfall auf Deutsch',
    props: () => ({ port: fakeSamplingPort(), items: populationItems, locale: 'en' }),
    expect: { texts: ['Grundgesamtheit'], roles: [['button', 'Calculate sample size'], ['button', 'Draw sample'], ['heading', 'Parameters']] },
  },
]
