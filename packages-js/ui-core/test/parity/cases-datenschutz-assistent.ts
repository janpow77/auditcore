/** Gemeinsame Paritätsfälle des Datenschutz-Assistenten (Vue ↔ React). */
import type { AssistantPort } from '../../src'
import { activityId, fakeAssistantPort, free, suggested } from '../dataprotection/fake-assistant-port'
import type { ParityCase } from './cases'

export interface AssistantCaseProps {
  port?: AssistantPort | null
  activityId?: string
  locale?: 'de' | 'en'
}

export const assistantCases: ReadonlyArray<ParityCase<AssistantCaseProps>> = [
  {
    name: 'geführt: erster Schritt, nur der nächste ist erreichbar',
    props: () => ({ port: fakeAssistantPort(), activityId }),
    expect: {
      texts: ['Datenschutz-Assistent', 'Schritt 1 von 11', 'Verarbeitung und Anwendungsgrenzen beschreiben'],
      roles: [['navigation', /Schritte/], ['button', 'Weiter'], ['tab', 'Assistent'], ['combobox', 'Bearbeitungsweise']],
      counts: { 'fieldset.fa-assistant__question': 6, '[aria-current="step"]': 1, '.fa-assistant__steps button:disabled': 9 },
    },
  },
  {
    name: 'KI-Vorschlag bleibt unbestätigt',
    props: () => ({ port: fakeAssistantPort(suggested), activityId }),
    expect: {
      texts: ['noch nicht bestätigt', 'Vorschlag prüfen und übernehmen', 'Vorschlag unbestätigt', 'unklar – zu klären'],
      counts: { '.fa-dataprotection__alert--warning': 1 },
    },
  },
  {
    name: 'frei: jeder Schritt erreichbar',
    props: () => ({ port: fakeAssistantPort(free), activityId }),
    expect: { texts: ['Schritt 7 von 11'], counts: { '.fa-assistant__steps button:disabled': 0 } },
  },
  { name: 'ohne Port', props: () => ({}), expect: { texts: ['Kein Port übergeben'], counts: { '[role="alert"]': 1 } } },
  {
    name: 'ohne Tätigkeit',
    props: () => ({ port: fakeAssistantPort() }),
    expect: { texts: ['Keine Tätigkeit gewählt'], counts: { '[role="alert"]': 1 } },
  },
]
