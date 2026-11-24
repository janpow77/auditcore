/**
 * Paritätsfälle von „PDF schwärzen“ (Vue `PdfRedaction` ↔ React
 * `FlowauditPdfRedaction`). Antworten des echten Python-Dienstes
 * (`ui/demo/redaction_demo.py`), synthetische PDF ohne Personendaten.
 * Prüfansicht und Ergebnis prüfen die Interaktionstests.
 */
import type { RedactionPort } from '../../src'
import { fakeRedactionPort, redactionCatalogueWithoutNer } from '../redaction/fake-port'
import type { ParityCase } from './cases'

export interface RedactionCaseProps {
  port?: RedactionPort | null
  locale?: 'de' | 'en'
}

export const redactionCases: ReadonlyArray<ParityCase<RedactionCaseProps>> = [
  {
    name: 'Katalog mit KI-Namenserkennung',
    props: () => ({ port: fakeRedactionPort() }),
    expect: {
      texts: ['Dokument und Suchkriterien', 'Höchstens 20 MiB und 500 Seiten.', 'Höchstens 200 Begriffe mit je 200 Zeichen.'],
      roles: [['checkbox', 'IBAN'], ['checkbox', 'Personennamen (KI-Erkennung)'], ['checkbox', 'Nur ganze Wörter'], ['button', 'Fundstellen suchen'], ['textbox', 'Eigene Begriffe, ein Begriff je Zeile']],
      counts: { 'input[data-pattern]': 10, 'input[data-pattern]:disabled': 0, 'input[type="file"]': 1, '[data-testid="redaction-review"]': 0 },
    },
  },
  {
    name: 'ohne KI-Namenserkennung',
    props: () => ({ port: fakeRedactionPort({ catalogue: redactionCatalogueWithoutNer }) }),
    expect: { texts: ['Personennamen (KI-Erkennung) (nicht eingerichtet)'], counts: { 'input[data-pattern]:disabled': 1 } },
  },
  { name: 'ohne Port', props: () => ({}), expect: { texts: ['Kein Dienst angebunden (Eigenschaft „port“).'], counts: { form: 0 } } },
  {
    name: 'Fehler beim Laden',
    props: () => ({ port: fakeRedactionPort({ failing: 'catalogue' }) }),
    expect: { texts: ['Anfrage abgelehnt: Dienst nicht erreichbar'], counts: { '[role="alert"]': 1, form: 0 } },
  },
  {
    name: 'englisch',
    props: () => ({ port: fakeRedactionPort(), locale: 'en' }),
    expect: { texts: ['Document and search criteria'], roles: [['button', 'Find occurrences'], ['checkbox', 'Match case']] },
  },
]
