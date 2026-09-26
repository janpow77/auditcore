/**
 * Gemeinsame Paritätsfälle der Vergleichsverwaltung (Vue ↔ React). Daten:
 * Antworten von `auditcore_documents.web` (Fixture `documents-comparisons.json`,
 * synthetische Dokumente).
 */
import type { ComparisonsPort } from '../../src'
import { fakePort, summaries } from '../documents/fake-port'
import type { ParityCase } from './cases'

export interface ComparisonsCaseProps {
  port?: ComparisonsPort | null
  editable?: boolean
  maxUploadBytes?: number
  showSynopsis?: boolean
  locale?: 'de' | 'en'
}

export const comparisonsCases: ReadonlyArray<ParityCase<ComparisonsCaseProps>> = [
  {
    name: 'Liste und Formular mit echten Antworten',
    props: () => ({ port: fakePort(), maxUploadBytes: 5 * 1024 * 1024 }),
    expect: {
      texts: [
        'Dokumentvergleiche',
        'Prüfcheckliste – Fassungen 1 und 2',
        'al_stamm.docx → al_befehle.docx',
        '3 geändert · 1 entfallen · 1 neu · 0 verschoben',
        'Gesetzessynopse',
        'DOCX, DOCM oder PDF, höchstens 5 MiB',
        `${summaries.length} von ${summaries.length} Vergleichen`,
        'auditcore.document_compare 2026.09.2 (Vorgabe)',
      ],
      roles: [
        ['heading', 'Neuer Vergleich'],
        ['heading', 'Gespeicherte Vergleiche'],
        ['button', 'Vergleichen'],
        ['button', 'Ergebnis importieren (JSON)'],
        ['button', '„Prüfcheckliste – Fassungen 1 und 2“ löschen'],
        ['searchbox', 'Vergleiche durchsuchen'],
        ['radio', 'Gesetzessynopse'],
        ['spinbutton', 'Ähnlichkeitsschwelle in Prozent (70–100)'],
      ],
      counts: { '.fa-comparisons-list__item': summaries.length, 'input[type="file"]': 3, 'input[type="checkbox"]': 9 },
    },
  },
  {
    name: 'nur Ansicht',
    props: () => ({ port: fakePort(), editable: false }),
    expect: { counts: { form: 0, '.fa-comparisons-list__item': summaries.length, 'input[type="file"]': 0, '[aria-label$="löschen"]': 0 } },
  },
  {
    name: 'leere Liste',
    props: () => ({ port: fakePort({ list: async () => [] }) }),
    expect: { texts: ['Noch keine Vergleiche gespeichert.', '0 von 0 Vergleichen'], counts: { '.fa-comparisons-list__item': 0 } },
  },
  {
    name: 'Fehler des Servers',
    props: () => ({ port: fakePort({ profiles: async () => Promise.reject(new TypeError('Failed to fetch')) }) }),
    expect: { texts: ['Keine Verbindung zum Server (Failed to fetch).'], counts: { '[role="alert"]': 1 } },
  },
  { name: 'ohne Port', props: () => ({}), expect: { texts: ['Kein Port übergeben'], counts: { '[role="alert"]': 1, form: 0 } } },
  {
    name: 'englisch',
    props: () => ({ port: fakePort(), locale: 'en' }),
    expect: { roles: [['heading', 'Document comparisons'], ['button', 'Compare']], texts: ['Legislative synopsis'] },
  },
]
