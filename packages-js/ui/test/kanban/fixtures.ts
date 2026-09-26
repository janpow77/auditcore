import { MemoryBoardPort, SCHEMA_VERSION, type Board, type Card } from '@auditcore/kanban-core'

export function card(id: string, columnId: string, rank: string, extra: Partial<Card> = {}): Card {
  return {
    id, column_id: columnId, rank, title: `Karte ${id}`, description: '', priority: 'mittel', tags: [], assignees: [], due: null,
    color: null, image: null, badge: null, checklist: [], links: [], attachments: [], created_at: '2026-09-20T08:00:00Z', updated_at: '2026-09-20T08:00:00Z', extra: {}, ...extra,
  }
}

export function board(extra: Partial<Board> = {}): Board {
  return {
    schema_version: SCHEMA_VERSION, id: 'b1', title: 'Prüfung 2026', icon: '📋', owner_id: 'owner', version: 1, pinned: false, archived: false,
    created_at: '2026-09-01T00:00:00Z', updated_at: '2026-09-20T00:00:00Z',
    columns: [
      { id: 'offen', label: 'Offen', color: '#7c3aed', wip_limit: null, done: false, status_aliases: [] },
      { id: 'arbeit', label: 'In Arbeit', color: '#f59e0b', wip_limit: 1, done: false, status_aliases: [] },
      { id: 'fertig', label: 'Erledigt', color: '#10b981', wip_limit: null, done: false, status_aliases: [] },
    ],
    cards: [card('a', 'offen', 'V', { title: 'Belegliste anfordern', tags: ['EFRE'] }), card('b', 'offen', 'k', { title: 'Vergabe prüfen', priority: 'hoch' }), card('c', 'arbeit', 'V')],
    labels: [], shares: [{ user_id: 'leser', permission: 'read', shared_by: 'owner', created_at: null }],
    transitions: { mode: 'free', allowed: [], locked_columns: [], fixed_order_columns: [] }, wip_mode: 'block', extra: {}, ...extra,
  }
}

export function port(userId = 'owner', value: Board = board()): MemoryBoardPort {
  return new MemoryBoardPort({ userId, boards: [value], users: [{ id: 'owner', name: 'Anna Becker' }, { id: 'leser', name: 'Lena Schmidt' }, { id: 'neu', name: 'Tobias Keller' }] })
}

export const flush = (): Promise<void> => new Promise((resolve) => setTimeout(resolve, 0))
