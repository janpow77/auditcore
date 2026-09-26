/**
 * Paritätsfälle der Belegerkennung (Vue `FaExtraction` ↔ React
 * `FlowauditExtraction`). Antworten des echten Python-Dienstes mit
 * Attrappen-Ports, synthetische Belege.
 */
import type { ExtractionPort, ExtractionRun } from '../../src'
import { extractionDisabled, fakeExtractionPort, runDonut, runFailed, runReview } from '../extraction/fake-port'
import type { ParityCase } from './cases'

export interface ExtractionCaseProps {
  port?: ExtractionPort | null
  result?: ExtractionRun | null
  locale?: 'de' | 'en'
}

export const extractionCases: ReadonlyArray<ParityCase<ExtractionCaseProps>> = [
  {
    name: 'Katalog geladen, empfohlenes Profil vorgewählt',
    props: () => ({ port: fakeExtractionPort() }),
    expect: {
      texts: ['höchstens 5 MiB', 'nur für diesen Lauf zwischengespeichert'],
      roles: [['combobox', 'Profil'], ['button', 'Erkennen'], ['option', 'Empfohlen (korrigiertes Verhalten) (empfohlen)']],
      counts: { 'input[type="file"]': 1, '[data-testid="extraction-result"]': 0, 'option:disabled': 0 },
    },
  },
  {
    name: 'ohne Engine abgeschaltet',
    props: () => ({ port: fakeExtractionPort({ catalogue: extractionDisabled }) }),
    expect: { texts: ['keine OCR-Engine angeschlossen'], counts: { form: 0 } },
  },
  { name: 'ohne Port', props: () => ({}), expect: { texts: ['Kein Port übergeben'], counts: { form: 0 } } },
  {
    name: 'Fehler beim Laden',
    props: () => ({ port: fakeExtractionPort({ failing: 'catalogue' }) }),
    expect: { texts: ['Anfrage abgelehnt: Dienst nicht erreichbar'], counts: { '[role="alert"]': 1, form: 0 } },
  },
  {
    name: 'Donut-Ergebnis mit Feldkonfidenz und Befunden',
    props: () => ({ port: fakeExtractionPort(), result: runDonut }),
    expect: {
      texts: ['Prüfung erforderlich', 'keine Prüfungsentscheidung', 'Plausibilität der Donut-Werte', 'verworfen (Plausibilität)', '97 %'],
      roles: [['rowheader', 'Gesamtbetrag']],
      counts: { '[data-testid="extraction-findings"] tbody tr': 2, '[data-field]': 12, '[data-testid="extraction-flags"] li': 2 },
    },
  },
  {
    name: 'Lesequalität prüfen',
    props: () => ({ port: fakeExtractionPort(), result: runReview }),
    expect: { texts: ['mittlere Konfidenz 72 %', 'prüfen', 'Lesequalität der Texterkennung'], counts: { '[data-testid="extraction-findings"] tbody tr': 1 } },
  },
  {
    name: 'fehlgeschlagener Lauf',
    props: () => ({ result: runFailed }),
    expect: { texts: ['Fehlgeschlagen', 'Fehler INVALID_MIME_TYPE', 'Keine Felder erkannt.', 'Keine Auffälligkeiten.'], counts: { '[role="alert"]': 1 } },
  },
  {
    name: 'englisch mit Rückfall auf Deutsch',
    props: () => ({ port: fakeExtractionPort(), locale: 'en' }),
    expect: { texts: ['Upload document'], roles: [['button', 'Extract'], ['combobox', 'Profile']] },
  },
]
