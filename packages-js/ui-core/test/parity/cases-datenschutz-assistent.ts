/** Gemeinsame Paritätsfälle des Datenschutz-Assistenten (Vue ↔ React). */
import type { AssistantPort } from '../../src'
import { activityId, consultation, fakeAssistantPort, free, providers, suggested, table } from '../dataprotection/fake-assistant-port'
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
      texts: ['Datenschutz-Assistent', 'Schritt 1 von 11', '1 Gegenstand der Verarbeitung', '1.7 Werden personenbezogene Daten verarbeitet', 'Zuständig: Fachbereich', 'Zuständig: IT-Betrieb', 'Zuständig: Recht/Datenschutz', '1.8 Bestehen zu Kapitel 1 noch offene Punkte?'],
      roles: [['navigation', /Schritte/], ['button', 'Weiter'], ['tab', 'Assistent'], ['combobox', 'Bearbeitungsweise']],
      counts: { 'fieldset.fa-assistant__question': 8, '.fa-assistant__role': 8, '[aria-current="step"]': 1, '.fa-assistant__steps button:disabled': 9 },
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
  {
    name: 'JA-Zweig mit Übermittlungstabelle, eingerückt und mit Fundstelle',
    props: () => ({ port: fakeAssistantPort(table), activityId }),
    expect: {
      texts: ['5.4.1 Übermittlungen:', 'Fundstelle: § 65 Abs. 1 HDSIG', 'Rechtsgrundlage *', 'Zeile hinzufügen'],
      roles: [['table', /Übermittlungen/], ['textbox', 'Empfänger 1']],
      counts: { '.fa-assistant__question--depth-1': 1, 'table.fa-assistant__table': 1 },
    },
  },
  {
    name: 'Dienstleister: Tatsachen beim IT-Betrieb, Einordnung mit Auswahl beim Recht',
    props: () => ({ port: fakeAssistantPort(providers), activityId }),
    expect: {
      texts: ['3.7.1 Dienstleister und ihre Leistungen:', '3.7.2 Rechtliche Einordnung der Dienstleister:', 'Leitlinien 07/2020'],
      roles: [['combobox', 'Einordnung 1'], ['option', 'Auftragsverarbeiter'], ['option', 'in Vorbereitung']],
      counts: { 'table.fa-assistant__table': 2, '.fa-assistant__role--recht': 3 },
    },
  },
  {
    name: 'Konsultation: Datum der Einleitung als Datumsfeld',
    props: () => ({ port: fakeAssistantPort(consultation), activityId }),
    expect: {
      texts: ['11.1.1 Datum der Einleitung der Konsultation:'],
      counts: { 'input[type="date"]': 1 },
    },
  },
  { name: 'ohne Port', props: () => ({}), expect: { texts: ['Kein Port übergeben'], counts: { '[role="alert"]': 1 } } },
  {
    name: 'ohne Tätigkeit',
    props: () => ({ port: fakeAssistantPort() }),
    expect: { texts: ['Keine Tätigkeit gewählt'], counts: { '[role="alert"]': 1 } },
  },
]
