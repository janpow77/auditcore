/** Board-Vorlagen: die sieben Vorlagen der WorkspaceSidebar und das cockpit-Auftragsboard. */
import { DEFAULT_COLUMNS, type Column, type TransitionPolicy } from './model'

export interface BoardTemplate {
  key: string
  name: string
  icon: string
  description: string
  columns: Column[]
  transitions?: TransitionPolicy
}

const GRAY = '#6b7280'
const BLUE = '#3b82f6'
const VIOLET = '#8b5cf6'
const AMBER = '#f59e0b'
const RED = '#ef4444'
const GREEN = '#10b981'

function columns(rows: readonly (readonly [string, string, string])[]): Column[] {
  return rows.map(([id, label, color]) => ({ id, label, color, wip_limit: null, done: false, status_aliases: [] }))
}

export const TEMPLATES: readonly BoardTemplate[] = [
  { key: 'standard', name: 'Standard', icon: '📋', description: 'Offen, In Arbeit, Erledigt', columns: DEFAULT_COLUMNS.map((c) => ({ ...c })) },
  {
    key: 'vorhabenpruefung', name: 'Vorhabenprüfung', icon: '🔍', description: 'Auswahl, Prüfung, Entwurf, Kontradiktorisch, Abschluss, Follow-Up',
    columns: columns([['auswahl', 'Auswahl', GRAY], ['pruefung', 'Prüfung', BLUE], ['entwurf', 'Entwurf', AMBER], ['kontradiktorisch', 'Kontradiktorisch', RED], ['abschluss', 'Abschluss', VIOLET], ['followup', 'Follow-Up', GREEN]]),
  },
  {
    key: 'sprint', name: 'Sprint', icon: '🏃', description: 'Backlog, Sprint, In Arbeit, Review, Done',
    columns: columns([['backlog', 'Backlog', GRAY], ['sprint', 'Sprint', BLUE], ['in_arbeit', 'In Arbeit', AMBER], ['review', 'Review', VIOLET], ['done', 'Done', GREEN]]),
  },
  { key: 'einfach', name: 'Einfach', icon: '✅', description: 'To-Do, Erledigt', columns: columns([['todo', 'To-Do', BLUE], ['erledigt', 'Erledigt', GREEN]]) },
  {
    key: 'systempruefung', name: 'Systemprüfung', icon: '🏛️', description: 'Auswahl, Erhebung, Prüfung, Entwurf, Kontradiktorisch, Abschluss',
    columns: columns([['auswahl', 'Auswahl', GRAY], ['erhebung', 'Erhebung', BLUE], ['pruefung', 'Prüfung', '#7c3aed'], ['entwurf', 'Entwurf', AMBER], ['kontradiktorisch', 'Kontradiktorisch', RED], ['abschluss', 'Abschluss', GREEN]]),
  },
  {
    key: 'teamplanung', name: 'Teamplanung', icon: '👥', description: 'Ideen, Geplant, In Arbeit, Erledigt',
    columns: columns([['ideen', 'Ideen', '#ec4899'], ['geplant', 'Geplant', BLUE], ['in_arbeit', 'In Arbeit', AMBER], ['erledigt', 'Erledigt', GREEN]]),
  },
  {
    key: 'jahresplanung', name: 'Jahresplanung', icon: '📅', description: 'Q1, Q2, Q3, Q4, Abgeschlossen',
    columns: columns([['q1', 'Q1', BLUE], ['q2', 'Q2', VIOLET], ['q3', 'Q3', AMBER], ['q4', 'Q4', RED], ['abgeschlossen', 'Abgeschlossen', GREEN]]),
  },
  {
    key: 'cockpit-auftraege', name: 'Aufträge (cockpit)', icon: '🤖', description: 'Eingang, Geplant, Läuft, Rückfrage / Freigabe, Fertig',
    columns: [
      { id: 'eingang', label: 'Eingang', color: GRAY, wip_limit: null, done: false, status_aliases: [] },
      { id: 'geplant', label: 'Geplant', color: BLUE, wip_limit: null, done: false, status_aliases: [] },
      { id: 'laeuft', label: 'Läuft', color: AMBER, wip_limit: null, done: false, status_aliases: [] },
      { id: 'rueckfrage', label: 'Rückfrage / Freigabe', color: RED, wip_limit: null, done: false, status_aliases: ['freigabe', 'unterbrochen'] },
      { id: 'fertig', label: 'Fertig', color: GREEN, wip_limit: null, done: true, status_aliases: ['fehler', 'abgebrochen'] },
    ],
    transitions: { mode: 'restricted', allowed: [['eingang', 'geplant'], ['geplant', 'eingang']], locked_columns: ['laeuft'], fixed_order_columns: [] },
  },
]

export function findTemplate(key: string): BoardTemplate | undefined {
  return TEMPLATES.find((entry) => entry.key === key)
}
