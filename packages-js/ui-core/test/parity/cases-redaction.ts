/**
 * Paritätsfälle von „PDF schwärzen“ (Vue `PdfRedaction` ↔ React
 * `FlowauditPdfRedaction`). Antworten des echten Python-Dienstes
 * (`ui/demo/redaction_demo.py`), synthetische PDF ohne Personendaten.
 * Prüfansicht und Ergebnis prüfen die Interaktionstests.
 */
import type { RedactionPort } from '../../src'
import { fakeRedactionPort, redactionCatalogueWithoutNer, syntheticPdf } from '../redaction/fake-port'
import type { ParityCase } from './cases'

export interface RedactionCaseProps {
  port?: RedactionPort | null
  locale?: 'de' | 'en'
  file?: Blob | null
  filename?: string
  terms?: readonly string[]
  patterns?: readonly string[]
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
  {
    name: 'bereitgestellte Datei mit Vorgaben',
    props: () => ({ port: fakeRedactionPort(), file: syntheticPdf('arbeitsfassung.pdf'), filename: 'Akte 2026-17.pdf', terms: ['Erika Mustermann'], patterns: ['iban', 'gibt_es_nicht'] }),
    expect: {
      texts: ['Dokument: Akte 2026-17.pdf'],
      counts: { 'input[type="file"]': 0, '[data-testid="redaction-file-provided"]': 1, 'input[data-pattern]:checked': 1, 'input[data-pattern="iban"]:checked': 1 },
    },
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
