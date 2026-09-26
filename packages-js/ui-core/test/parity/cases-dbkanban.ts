/**
 * Gemeinsame Paritätsfälle der Datenbankansicht als Kanban (Vue ↔ React).
 * Daten: Tabelle der Python/TS-Paritätsfixture `group.json` (auditcore_kanban).
 */
import type { RecordPort, RecordTable } from '@flowaudit/kanban-core'
import { recordPort, recordTable } from '../dbkanban/fixtures'
import type { ParityCase } from './cases'

export interface DbKanbanCaseProps {
  port?: RecordPort | null
  table?: RecordTable | null
  groupBy?: string
  editable?: boolean
  locale?: 'de' | 'en'
}

export const dbKanbanCases: ReadonlyArray<ParityCase<DbKanbanCaseProps>> = [
  {
    name: 'nach Status gruppiert mit Spalte „Ohne Wert“',
    props: () => ({ port: recordPort() }),
    expect: {
      texts: ['Kanban-Ansicht', 'Ohne Wert', '2 Einträge', 'Vorhaben A', 'Betrag', '1.200', 'in Prüfung'],
      roles: [['combobox', 'Gruppieren nach'], ['searchbox', 'Einträge durchsuchen'], ['heading', 'Ohne Wert'], ['button', 'Eintrag in „erledigt“ hinzufügen']],
      counts: { '.fa-db-kanban-column': 4, '.fa-db-kanban-card': 6, '[draggable="true"]': 6 },
    },
  },
  {
    name: 'gewünschte Gruppierung Fonds',
    props: () => ({ port: recordPort(), groupBy: 'fonds' }),
    expect: { texts: ['JTF', 'Keine Einträge'], counts: { '.fa-db-kanban-column': 4, '[data-column="JTF"] .fa-db-kanban-card': 0, '[data-column=""] .fa-db-kanban-card': 3 } },
  },
  {
    name: 'nur Ansicht aus Tabelle',
    props: () => ({ table: recordTable, editable: false }),
    expect: { texts: ['Nur Lesezugriff'], counts: { '[draggable="true"]': 0, '.fa-db-kanban-column__add': 0, '.fa-db-kanban-card': 6 } },
  },
  {
    name: 'ohne Auswahl-Eigenschaft',
    props: () => ({ table: { properties: [{ id: 'titel', name: 'Titel', type: 'text' }], rows: [] } }),
    expect: { texts: ['keine Auswahl-Eigenschaft'], counts: { '.fa-db-kanban-column': 0 } },
  },
  { name: 'ohne Datenquelle', props: () => ({}), expect: { texts: ['Keine Datenquelle übergeben'], counts: { '[role="alert"]': 1 } } },
  {
    name: 'englisch',
    props: () => ({ port: recordPort(), locale: 'en' }),
    expect: { roles: [['heading', 'Kanban view'], ['heading', 'No value']], texts: ['2 entries'] },
  },
]
