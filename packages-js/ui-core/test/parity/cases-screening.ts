/** Gemeinsame Paritätsfälle der Screening-Trefferprüfung (Vue ↔ React). */
import type { ScreeningPort } from '../../src'
import { fakePort, run } from '../screening/fake-port'
import type { ParityCase } from './cases'

export interface ScreeningCaseProps {
  port?: ScreeningPort | null
  runId?: string
  locale?: 'de' | 'en'
}

export const screeningCases: ReadonlyArray<ParityCase<ScreeningCaseProps>> = [
  {
    name: 'Prüflauf geöffnet: Treffer, Vergleich, Aufschlüsselung, Zweitprüfung',
    props: () => ({ port: fakePort(), runId: run.run_id }),
    expect: {
      texts: ['Screening-Trefferprüfung', 'nicht abgefragt', 'Musterstraße 1, 12345 Musterstadt', 'Ergebniswert', 'wartet auf Zweitprüfung', 'Quellenstand zum Zeitpunkt des Prüflaufs'],
      roles: [['heading', 'Neuer Prüflauf'], ['button', 'Zustimmen'], ['button', 'Nächster offener Treffer'], ['group', 'Abgefragte Listen']],
      counts: { '.fa-screening__subject': 2, '.fa-screening__hit': 2, '.fa-screening__cmp tbody tr': 10 },
    },
  },
  {
    name: 'ohne geöffneten Lauf',
    props: () => ({ port: fakePort() }),
    expect: { texts: ['Prüflauf auswählen oder neu anlegen.', 'Prüflauf starten'], counts: { '.fa-screening__runs li': 1, '[role="alert"]': 0 } },
  },
  {
    name: 'Portfehler',
    props: () => ({ port: fakePort({ settings: async () => Promise.reject(new Error('offline')) }) }),
    expect: { texts: ['Verbindung fehlgeschlagen: offline'], counts: { '[role="alert"]': 1 } },
  },
  { name: 'ohne Port', props: () => ({}), expect: { texts: ['Kein Port übergeben'], counts: { '[role="alert"]': 1 } } },
  {
    name: 'englisch',
    props: () => ({ port: fakePort(), runId: run.run_id, locale: 'en' }),
    expect: { roles: [['heading', 'Screening hit review'], ['button', 'Approve']] },
  },
]
