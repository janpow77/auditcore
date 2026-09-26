/**
 * Paritätsfälle von „Kennung prüfen“ (Vue `IdentifierCheck` ↔ React
 * `FlowauditIdentifierCheck`). Port mit Antworten des echten
 * auditcore_identifiers.web, synthetische Kennungen.
 */
import type { IdentifiersPort } from '../../src'
import { fakeIdentifiersPort } from '../identifiers/fake-port'
import type { ParityCase } from './cases'

export interface IdentifierCaseProps {
  port?: IdentifiersPort | null
  locale?: 'de' | 'en'
}

export const identifierCases: ReadonlyArray<ParityCase<IdentifierCaseProps>> = [
  {
    name: 'Katalog geladen, empfohlenes Profil und erste Art vorgewählt',
    props: () => ({ port: fakeIdentifiersPort() }),
    expect: {
      texts: ['Einzelprüfung', 'Stapelprüfung aus Tabelle', 'Streng (Standard) (empfohlen)', 'Herkunft und Zweck des Profils'],
      roles: [['combobox', 'Prüfprofil'], ['combobox', 'Kennungsart'], ['textbox', 'Wert'], ['button', 'Prüfen']],
      counts: { '[data-testid="ident-country"]': 0, 'input[type="file"]': 1, '[data-testid="ident-kind"] option': 8 },
    },
  },
  { name: 'ohne Port', props: () => ({}), expect: { texts: ['Kein Port übergeben'], counts: { form: 0 } } },
  {
    name: 'Fehler beim Laden',
    props: () => ({ port: fakeIdentifiersPort('catalogue') }),
    expect: { texts: ['Anfrage abgelehnt: Dienst nicht erreichbar'], counts: { '[role="alert"]': 1, form: 0 } },
  },
  {
    name: 'englisch mit Rückfall auf Deutsch',
    props: () => ({ port: fakeIdentifiersPort(), locale: 'en' }),
    expect: { texts: ['Einzelprüfung'], roles: [['button', 'Check'], ['combobox', 'Check profile'], ['combobox', 'Identifier type']] },
  },
]
