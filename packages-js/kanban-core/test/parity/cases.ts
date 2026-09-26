/**
 * Gemeinsame Paritätsfälle des Kanban-Boards: die Vue-Fassung (`KanbanBoard`,
 * `KanbanBoardList` aus `@auditcore/ui`) und die React-Fassung
 * (`FlowauditKanbanBoard`, `FlowauditKanbanBoards` aus `@auditcore/ui-react`)
 * werden mit denselben Eingaben gerendert und gegen dieselben Erwartungen
 * sowie gegeneinander (DOM) geprüft. Synthetische Daten, keine Personendaten.
 */
import { KanbanError, MemoryBoardPort, SCHEMA_VERSION, type Board, type BoardPort, type Card, type UserRef } from '../../src'

/** Gleiche Form wie `Expectation`/`ParityCase` in `ui-core/test/parity/cases.ts`. */
export interface Expectation {
  texts?: readonly string[]
  roles?: ReadonlyArray<readonly [string, string | RegExp]>
  counts?: Readonly<Record<string, number>>
}

export interface ParityCase<P> {
  name: string
  props: () => P
  expect: Expectation
}

export const TODAY = '2026-09-25'
/** Feste Uhrzeit für Kartenalter und relative Zeiten (beide Fassungen gleich). */
export const NOW = Date.parse('2026-09-25T12:00:00Z')

export const USERS: readonly UserRef[] = [
  { id: 'owner', name: 'Anna Becker', email: 'anna.becker@example.org' },
  { id: 'leser', name: 'Lena Schmidt' },
  { id: 'neu', name: 'Tobias Keller', email: 'tobias.keller@example.org' },
]

function card(id: string, columnId: string, rank: string, extra: Partial<Card> = {}): Card {
  return {
    id, column_id: columnId, rank, title: `Karte ${id}`, description: '', priority: 'mittel', tags: [], assignees: [], due: null,
    color: null, image: null, badge: null, checklist: [], links: [], attachments: [], created_at: '2026-09-20T08:00:00Z', updated_at: '2026-09-21T09:30:00Z', extra: {}, ...extra,
  }
}

export function kanbanBoard(extra: Partial<Board> = {}): Board {
  return {
    schema_version: SCHEMA_VERSION, id: 'b1', title: 'Prüfung 2026', icon: '📋', owner_id: 'owner', version: 1, pinned: false, archived: false,
    created_at: '2026-09-01T00:00:00Z', updated_at: '2026-09-20T00:00:00Z',
    columns: [
      { id: 'offen', label: 'Offen', color: '#7c3aed', wip_limit: null, done: false, status_aliases: [] },
      { id: 'arbeit', label: 'In Arbeit', color: '#f59e0b', wip_limit: 1, done: false, status_aliases: [] },
      { id: 'fertig', label: 'Erledigt', color: '#10b981', wip_limit: null, done: true, status_aliases: [] },
    ],
    cards: [
      card('a', 'offen', 'V', {
        title: 'Belegliste anfordern', badge: 'VP-01', tags: ['EFRE', 'Beleg', 'Frist', 'Vergabe'], due: '2026-09-24', priority: 'hoch',
        description: 'Gesamtbelegliste beim Begünstigten anfordern und auf Vollständigkeit prüfen, bevor die Stichprobe gezogen wird.',
        checklist: [{ text: 'Anschreiben', done: true }, { text: 'Frist setzen', done: false }],
        links: [{ kind: 'vorhaben', target: 'V-2026-17', title: 'Vorhaben 17' }],
        attachments: [{ id: 'f1', filename: 'belegliste.xlsx', mime_type: 'application/vnd.ms-excel', size: 48_200 }],
        assignees: ['owner'],
      }),
      card('b', 'offen', 'k', { title: 'Vergabe prüfen', color: '#1e293b', due: '2026-09-27' }),
      card('c', 'arbeit', 'V', { title: 'Vor-Ort-Prüfung', priority: 'niedrig', due: '2026-10-30' }),
      card('d', 'fertig', 'V', { title: 'Prüfungsankündigung', description: 'versendet' }),
    ],
    labels: [], shares: [{ user_id: 'leser', permission: 'read', shared_by: 'owner', created_at: null }],
    transitions: { mode: 'free', allowed: [], locked_columns: [], fixed_order_columns: [] }, wip_mode: 'block', extra: {}, ...extra,
  }
}

export function kanbanPort(userId = 'owner', value: Board = kanbanBoard()): MemoryBoardPort {
  return new MemoryBoardPort({ userId, boards: [value], users: USERS })
}

/** Port, der beim Laden scheitert (Fehleranzeige mit „Erneut laden“). */
export function failingPort(): BoardPort {
  const port = kanbanPort()
  port.load = () => Promise.reject(new KanbanError('NOT_FOUND', 'Board nicht gefunden'))
  return port
}

export interface KanbanCaseProps {
  port?: BoardPort | null
  boardId?: string
  board?: Board | null
  userId?: string
  users?: readonly UserRef[]
  readOnly?: boolean
  sharedByName?: string
  showFullscreen?: boolean
  today?: string
  locale?: 'de' | 'en'
}

export const kanbanCases: ReadonlyArray<ParityCase<KanbanCaseProps>> = [
  {
    name: 'Board über Port als Eigentümerin',
    props: () => ({ port: kanbanPort(), boardId: 'b1', today: TODAY }),
    expect: {
      texts: ['Prüfung 2026', '1 von 4 erledigt'],
      roles: [['group', 'Kanban-Board'], ['button', 'Aufgabe in Offen hinzufügen'], ['button', 'Board teilen'], ['button', 'Board-Einstellungen'], ['progressbar', '1 von 4 erledigt']],
      counts: { '[data-card-id]': 4, 'section.fa-kanban-column': 3, '.fa-kanban-column__count.is-full': 1, '.fa-kanban-card--done': 1, '.fa-kanban-card--styled': 1 },
    },
  },
  {
    name: 'lokales Board ohne Port',
    props: () => ({ board: kanbanBoard(), userId: 'owner', today: TODAY }),
    expect: { roles: [['button', 'Prüfung 2026']], counts: { '[data-card-id]': 4, '.fa-kanban-card__badge': 1, '.fa-kanban-card__tag': 5 } },
  },
  {
    name: 'nur Lesezugriff für geteilte Person',
    props: () => ({ port: kanbanPort('leser'), boardId: 'b1', sharedByName: 'Anna Becker', today: TODAY }),
    expect: { texts: ['Geteilt von Anna Becker – Nur Lesezugriff'], counts: { '.fa-kanban-column__add': 0, '.fa-kanban-card__check': 0, '.fa-kanban-toolbar__rename': 0 } },
  },
  {
    name: 'gesperrt über readOnly, ohne Vollbild',
    props: () => ({ port: kanbanPort(), boardId: 'b1', readOnly: true, showFullscreen: false, today: TODAY }),
    expect: { texts: ['Nur Lesezugriff'], counts: { '.fa-kanban-column__add': 0, 'button[aria-label="Vollbild (F)"]': 0 } },
  },
  {
    name: 'Ladefehler mit erneutem Laden',
    props: () => ({ port: failingPort(), boardId: 'b1', today: TODAY }),
    expect: { texts: ['Fehler: Board nicht gefunden'], roles: [['button', 'Erneut laden']], counts: { '.fa-kanban-toolbar': 0 } },
  },
  {
    name: 'englische Oberfläche',
    props: () => ({ port: kanbanPort(), boardId: 'b1', locale: 'en', today: TODAY }),
    expect: { texts: ['1 of 4 done'], roles: [['button', 'Add task to Offen'], ['button', 'Share board']] },
  },
]

export interface BoardListCaseProps {
  port?: BoardPort | null
  activeId?: string
  now?: number
  locale?: 'de' | 'en'
}

function listPort(): MemoryBoardPort {
  const shared = kanbanBoard({ id: 'b2', title: 'Systemprüfung', owner_id: 'neu', shares: [{ user_id: 'owner', permission: 'edit', shared_by: 'neu', created_at: null }], updated_at: '2026-09-24T10:00:00Z' })
  const pinned = kanbanBoard({ id: 'b3', title: 'Jahreskontrollbericht', pinned: true, updated_at: '2026-09-10T10:00:00Z' })
  return new MemoryBoardPort({ userId: 'owner', boards: [kanbanBoard(), shared, pinned], users: USERS })
}

export const boardListCases: ReadonlyArray<ParityCase<BoardListCaseProps>> = [
  {
    name: 'eigene und geteilte Boards',
    props: () => ({ port: listPort(), activeId: 'b1', now: NOW }),
    expect: {
      texts: ['Meine Boards', 'Mit mir geteilt', '1/4 Aufgaben', 'Bearbeiten'],
      roles: [['button', 'Neues Board'], ['button', 'Lösen'], ['button', 'Board Prüfung 2026 löschen']],
      counts: { '.fa-kanban-boards__item': 3, '.is-active': 1, '[aria-current="page"]': 1 },
    },
  },
  {
    name: 'ohne Boards',
    props: () => ({ port: new MemoryBoardPort({ userId: 'owner', boards: [], users: USERS }), now: NOW }),
    expect: { texts: ['Noch keine Boards'], counts: { '.fa-kanban-boards__item': 0 } },
  },
]

