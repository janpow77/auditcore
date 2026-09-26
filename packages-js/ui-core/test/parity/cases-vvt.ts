/** Gemeinsame Paritätsfälle des Verzeichnisses von Verarbeitungstätigkeiten (Vue ↔ React). */
import type { DataProtectionPort } from '../../src'
import { fakePort } from '../dataprotection/fake-port'
import type { ParityCase } from './cases'

export interface VvtCaseProps {
  port?: DataProtectionPort | null
  actor?: string
  editable?: boolean
  locale?: 'de' | 'en'
}

export const vvtCases: ReadonlyArray<ParityCase<VvtCaseProps>> = [
  {
    name: 'Entwurf bearbeitbar (zweite Person)',
    props: () => ({ port: fakePort(), actor: 'daten-b' }),
    expect: {
      texts: ['Fassung 2 – Entwurf', '2 Pflichtangaben fehlen, 2 Hinweise', 'Referat Z 1', 'Referat Z 6'],
      roles: [['navigation', /tätigkeiten/i], ['button', 'Entwurf speichern'], ['button', /Freigeben/]],
      counts: { '.fa-vvt__item': 3, '[data-testid="vvt-detail"] textarea': 14 },
    },
  },
  {
    name: 'Vier-Augen-Hinweis für die bearbeitende Person',
    props: () => ({ port: fakePort(), actor: 'daten-a' }),
    expect: { texts: ['Vier-Augen-Prinzip'], counts: { '[data-testid="vvt-release-hint"]': 1 } },
  },
  {
    name: 'nur Ansicht',
    props: () => ({ port: fakePort(), editable: false }),
    expect: { counts: { textarea: 0, 'dl.fa-dataprotection__dl': 1 } },
  },
  { name: 'ohne Port', props: () => ({}), expect: { texts: ['Kein Port übergeben'], counts: { '[role="alert"]': 1 } } },
  {
    name: 'englisch',
    props: () => ({ port: fakePort(), editable: false, locale: 'en' }),
    expect: { roles: [['heading', /Record of processing activities/]] },
  },
]
