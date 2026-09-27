/**
 * Paritätsfälle der Merkmalsstichprobe (Vue `AttributeSampling` ↔ React
 * `FlowauditAttributeSampling`). Port mit Antworten des echten Backends.
 */
import type { AttributesPort } from '../../src'
import { fakeAttributesPort } from '../attributes/fake-port'
import type { ParityCase } from './cases'

export interface AttributesCaseProps {
  port?: AttributesPort | null
  locale?: 'de' | 'en'
}

export const attributesCases: ReadonlyArray<ParityCase<AttributesCaseProps>> = [
  {
    name: 'Formular nach dem Laden',
    props: () => ({ port: fakeAttributesPort() }),
    expect: {
      texts: ['Merkmalsstichprobe (Systemprüfung)', 'Tolerierbare Abweichungsquote (%)'],
      roles: [['combobox', 'Verfahren'], ['button', 'Auswerten'], ['combobox', 'Faktorprofil (z-Wert)']],
      counts: { select: 3, input: 3 },
    },
  },
  {
    name: 'Fehler beim Laden',
    props: () => ({ port: fakeAttributesPort('profiles') }),
    expect: { texts: ['Anfrage abgelehnt: Dienst nicht erreichbar'], counts: { '[role="alert"]': 1, select: 0 } },
  },
  {
    name: 'englisch mit Rückfall auf Deutsch',
    props: () => ({ port: fakeAttributesPort(), locale: 'en' }),
    expect: { texts: ['Attribute sampling (system audit)', 'Verfahren'], roles: [['button', 'Evaluate']] },
  },
]
