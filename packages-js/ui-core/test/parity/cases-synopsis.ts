/** Paritätsfälle der Synopse (Vue `FaSynopsis` ↔ React `FlowauditSynopsis`); Fixtures des echten Python-Backends. */
import type { Comparison, SynopsisPort } from '../../src'
import { article, checklist, standard } from '../synopsis/fixtures'
import type { ParityCase } from './cases'

export interface SynopsisCaseProps {
  comparison?: Comparison | null
  comparisonId?: string
  port?: SynopsisPort | null
  editable?: boolean
  layout?: 'side-by-side' | 'inline'
  oldLabel?: string
  newLabel?: string
  locale?: 'de' | 'en'
}

const port = (comparison: Comparison): SynopsisPort => ({
  load: async () => comparison,
  updateRows: async () => comparison,
  exportUrl: (id, format) => `/api/synopsis/comparisons/${id}/export?format=${format}`,
})

export const synopsisCases: ReadonlyArray<ParityCase<SynopsisCaseProps>> = [
  {
    name: 'Standardvergleich nebeneinander',
    props: () => ({ comparison: standard }),
    expect: {
      texts: ['3 geändert · 2 entfallen · 3 neu', 'keine Prüfungsentscheidung', '8 Änderungen in dieser Ansicht'],
      roles: [['heading', standard.title], ['region', 'Ansicht, Filter und Export'], ['button', 'Nächste Änderung']],
      counts: { article: 8, 'h4.fa-synopsis-row__side-title': 16 },
    },
  },
  {
    name: 'Inline-Ansicht mit eigenen Bezeichnungen',
    props: () => ({ comparison: standard, layout: 'inline', oldLabel: 'Richtlinie 2025', newLabel: 'Richtlinie 2026' }),
    expect: { counts: { '.fa-synopsis-row__inline': 8, '.fa-synopsis-row__sides': 0 } },
  },
  {
    name: 'Checkliste bearbeitbar mit Server-Exporten',
    props: () => ({ comparison: checklist, editable: true, port: port(checklist) }),
    expect: {
      texts: ['5 von 6 Zeilen für die Ausgabe ausgewählt'],
      roles: [['link', 'Word (DOCX)'], ['checkbox', /Nur ausgewählte/]],
      counts: { '.fa-synopsis-row__include input': 5, textarea: 5 },
    },
  },
  {
    name: 'Gesetzessynopse mit offenen Befehlen',
    props: () => ({ comparison: article }),
    expect: { roles: [['region', 'Offene Änderungsbefehle']], counts: { details: 1 } },
  },
  { name: 'ohne Vergleich', props: () => ({}), expect: { texts: ['Kein Vergleich ausgewählt.'] } },
  {
    name: 'englische Oberfläche',
    props: () => ({ comparison: standard, locale: 'en' }),
    expect: { roles: [['button', 'Next change']] },
  },
]
