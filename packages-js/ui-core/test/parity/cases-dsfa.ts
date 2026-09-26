/**
 * Paritätsfälle der Datenschutz-Folgenabschätzung (Vue `FaDsfa` ↔ React
 * `FlowauditDsfa`). Port mit den Antworten des echten Python-Backends
 * (Fixture `dataprotection-contract.json`, synthetische Daten).
 */
import type { DataProtectionPort } from '../../src'
import { fakePort } from '../dataprotection/fake-port'
import type { ParityCase } from './cases'

export interface DsfaCaseProps {
  port?: DataProtectionPort | null
  activityId?: string
  actor?: string
  editable?: boolean
  locale?: 'de' | 'en'
}

export const dsfaCases: ReadonlyArray<ParityCase<DsfaCaseProps>> = [
  {
    name: 'Übersicht ohne geöffnete Abschätzung',
    props: () => ({ port: fakePort(), actor: 'daten-b' }),
    expect: {
      texts: ['Datenschutz-Folgenabschätzung', 'Freigabe mit Auflagen'],
      roles: [['button', 'Öffnen: Vorhabenprüfung mit Stichprobe'], ['heading', 'Verarbeitungstätigkeiten und Stand der Folgenabschätzung']],
      counts: { '[data-testid="dsfa-overview"] tbody tr': 2, '[data-testid="dsfa-head"]': 0 },
    },
  },
  {
    name: 'Entwurf in der Schwellwertanalyse',
    props: () => ({ port: fakePort(), actor: 'daten-b', activityId: 'foerderung' }),
    expect: {
      texts: ['Bewilligung von Zuwendungen', 'unvollständig'],
      roles: [['tab', '1. Schwellwertanalyse'], ['tabpanel', '1. Schwellwertanalyse'], ['button', 'Entwurf speichern']],
      counts: { '[role="tab"][aria-selected="true"]': 1, 'fieldset.fa-dsfa__question[disabled]': 0 },
    },
  },
  {
    name: 'freigegebene, gesperrte Fassung',
    props: () => ({ port: fakePort(), actor: 'daten-b', activityId: 'pruefung' }),
    expect: {
      texts: ['Fassung 1 – freigegeben', 'Diese Fassung ist freigegeben und gesperrt', 'DSFA erforderlich'],
      roles: [['button', 'Neubewertung beginnen']],
      counts: { '[data-question="dsk_nr08_beschaeftigte"].fa-dsfa__question--yes': 1, 'fieldset.fa-dsfa__question:not([disabled])': 0 },
    },
  },
  {
    name: 'nur Ansicht (editable = false)',
    props: () => ({ port: fakePort(), activityId: 'foerderung', editable: false }),
    expect: { counts: { 'fieldset.fa-dsfa__question:not([disabled])': 0 }, texts: ['Bewilligung von Zuwendungen'] },
  },
  { name: 'ohne Port', props: () => ({ port: null }), expect: { texts: ['Kein Port übergeben'], counts: { '[role="alert"]': 1 } } },
  {
    name: 'englische Oberfläche',
    props: () => ({ port: fakePort(), activityId: 'foerderung', locale: 'en' }),
    expect: { texts: ['Data protection impact assessment'], roles: [['tab', '1. Threshold analysis']] },
  },
]
