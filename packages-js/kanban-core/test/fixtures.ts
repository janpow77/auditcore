import { SCHEMA_VERSION, type Board, type Card, type Column } from '../src'

export function column(id: string, extra: Partial<Column> = {}): Column {
  return { id, label: id.toUpperCase(), color: '#6b7280', wip_limit: null, done: false, status_aliases: [], ...extra }
}

export function card(id: string, columnId: string, rank: string, extra: Partial<Card> = {}): Card {
  return {
    id, column_id: columnId, rank, title: `Karte ${id}`, description: '', priority: 'mittel', tags: [], assignees: [],
    due: null, color: null, image: null, badge: null, checklist: [], links: [], attachments: [],
    created_at: '2026-09-01T08:00:00+00:00', updated_at: '2026-09-01T08:00:00+00:00', extra: {}, ...extra,
  }
}

export function board(extra: Partial<Board> = {}): Board {
  return {
    schema_version: SCHEMA_VERSION, id: 'b1', title: 'Prüfung 2026', icon: '📋', owner_id: 'owner', version: 1,
    pinned: false, archived: false, created_at: '', updated_at: '',
    columns: [column('offen'), column('in_arbeit', { wip_limit: 2 }), column('erledigt')],
    cards: [card('a', 'offen', 'V'), card('b', 'offen', 'k'), card('c', 'in_arbeit', 'V')],
    labels: [], shares: [{ user_id: 'editor', permission: 'edit', shared_by: 'owner', created_at: null }, { user_id: 'reader', permission: 'read', shared_by: 'owner', created_at: null }],
    transitions: { mode: 'free', allowed: [], locked_columns: [], fixed_order_columns: [] }, wip_mode: 'block', extra: {}, ...extra,
  }
}

export const ctx = (actor = 'owner') => ({ actor, now: '2026-09-25T12:00:00+00:00', newId: () => 'neu' })
