/** Reine Board-Befehle: anlegen, umbenennen/anheften, Spalten konfigurieren, teilen, widerrufen. */
import { bump, requireAction, type Change, type CommandContext, type CommandResult } from './commands'
import { KanbanError, raiseIfDenied } from './errors'
import { cardsIn, DEFAULT_COLUMNS, findColumn, SCHEMA_VERSION, shareFor, type Board, type Card, type Column, type SharePermission, type TransitionPolicy } from './model'
import { checkRevoke, checkShare } from './permissions'
import { rankBetween, spreadRanks } from './rank'
import type { BoardTemplate } from './templates'
import { DEFAULT_LIMITS, validateBoardTitle, validateColumns } from './validation'

function result(board: Board, change: Change): CommandResult {
  return { board, changes: [change], card: null, warnings: [] }
}

export function createBoard(ctx: CommandContext, boardId: string, title = 'Neues Board', icon = '📋', template?: BoardTemplate): CommandResult {
  const limits = ctx.limits ?? DEFAULT_LIMITS
  const board: Board = {
    schema_version: SCHEMA_VERSION, id: boardId, title: validateBoardTitle(title, limits), icon, owner_id: ctx.actor,
    version: 1, pinned: false, archived: false, created_at: ctx.now, updated_at: ctx.now,
    columns: template ? validateColumns(template.columns, limits) : DEFAULT_COLUMNS.map((column) => ({ ...column })),
    cards: [], labels: [], shares: [],
    transitions: template?.transitions ?? { mode: 'free', allowed: [], locked_columns: [], fixed_order_columns: [] },
    wip_mode: 'block', extra: {},
  }
  return result(board, { kind: 'board.created', card_id: null, data: { template: template?.key ?? null } })
}

export interface BoardPatch {
  title?: string
  icon?: string
  pinned?: boolean
  archived?: boolean
}

/** Umbenennen (Eigentümer, Bearbeiten), Anheften/Archivieren (nur Eigentümer). */
export function updateBoard(board: Board, ctx: CommandContext, patch: BoardPatch): CommandResult {
  let next = board
  const changed: string[] = []
  if (patch.title !== undefined || patch.icon !== undefined) {
    requireAction(board, ctx, 'rename')
    const title = patch.title === undefined ? board.title : validateBoardTitle(patch.title, ctx.limits ?? DEFAULT_LIMITS)
    next = { ...next, title, icon: patch.icon ?? board.icon }
    changed.push(...(['title', 'icon'] as const).filter((name) => patch[name] !== undefined))
  }
  if (patch.pinned !== undefined || patch.archived !== undefined) {
    requireAction(board, ctx, 'pin')
    next = { ...next, pinned: patch.pinned ?? board.pinned, archived: patch.archived ?? board.archived }
    changed.push(...(['pinned', 'archived'] as const).filter((name) => patch[name] !== undefined))
  }
  return result(bump(next, ctx), { kind: 'board.updated', card_id: null, data: { fields: changed.sort() } })
}

function restrictPolicy(policy: TransitionPolicy, ids: ReadonlySet<string>): TransitionPolicy {
  return {
    mode: policy.mode,
    allowed: policy.mode === 'restricted' ? policy.allowed.filter(([from, to]) => ids.has(from) && ids.has(to)) : [],
    locked_columns: policy.locked_columns.filter((id) => ids.has(id)).sort(),
    fixed_order_columns: policy.fixed_order_columns.filter((id) => ids.has(id)).sort(),
  }
}

/** Karten entfernter Spalten gehen in bisheriger Reihenfolge ans Ende der Zielspalte. */
function rehome(board: Board, removed: ReadonlySet<string>, target: string): { cards: Card[]; moved: string[] } {
  const orphans = board.columns.filter((column) => removed.has(column.id)).flatMap((column) => cardsIn(board, column.id))
  if (orphans.length === 0) return { cards: board.cards, moved: [] }
  const last = cardsIn(board, target)
  let low = last[last.length - 1]?.rank ?? null
  const replacement = new Map<string, Card>()
  for (const orphan of orphans) {
    low = rankBetween(low, null)
    replacement.set(orphan.id, { ...orphan, column_id: target, rank: low })
  }
  return { cards: board.cards.map((card) => replacement.get(card.id) ?? card), moved: orphans.map((card) => card.id) }
}

/** Ersetzt den Spaltensatz (nur Eigentümer); Karten entfernter Spalten wandern in die erste Spalte. */
export function configureColumns(board: Board, ctx: CommandContext, columns: readonly Column[], transitions?: TransitionPolicy): CommandResult {
  requireAction(board, ctx, 'configure')
  const checked = validateColumns(columns, ctx.limits ?? DEFAULT_LIMITS)
  const ids = new Set(checked.map((column) => column.id))
  const removed = new Set(board.columns.map((column) => column.id).filter((id) => !ids.has(id)))
  const staged: Board = { ...board, columns: checked, transitions: restrictPolicy(transitions ?? board.transitions, ids) }
  const { cards, moved } = rehome(board, removed, (checked[0] as Column).id)
  const data = { removed: [...removed].sort(), moved_cards: moved }
  return result(bump(staged, ctx, cards), { kind: 'board.configured', card_id: null, data })
}

/** Freigabe anlegen oder ändern (Upsert); nur der Eigentümer darf teilen. */
export function shareBoard(board: Board, ctx: CommandContext, userId: string, permission: string): CommandResult {
  raiseIfDenied(checkShare(board, ctx.actor, userId, permission))
  const granted = permission as SharePermission
  const existing = shareFor(board, userId)
  const shares = existing
    ? board.shares.map((share) => (share.user_id === userId ? { ...share, permission: granted } : share))
    : [...board.shares, { user_id: userId, permission: granted, shared_by: ctx.actor, created_at: ctx.now }]
  const kind = existing ? 'share.updated' : 'share.created'
  return result(bump({ ...board, shares }, ctx), { kind, card_id: null, data: { user_id: userId, permission } })
}

/** Eigentümer widerruft jede Freigabe, Empfänger die eigene. */
export function revokeShare(board: Board, ctx: CommandContext, userId: string): CommandResult {
  raiseIfDenied(checkRevoke(board, ctx.actor, userId))
  const shares = board.shares.filter((share) => share.user_id !== userId)
  return result(bump({ ...board, shares }, ctx), { kind: 'share.revoked', card_id: null, data: { user_id: userId } })
}

/** Ersetzt die Ränge einer Spalte durch gleichmäßig verteilte Schlüssel (Reihenfolge bleibt). */
export function respreadColumn(board: Board, ctx: CommandContext, columnId: string): CommandResult {
  requireAction(board, ctx, 'move_card')
  if (!findColumn(board, columnId)) throw new KanbanError('UNKNOWN_COLUMN', `Unbekannte Spalte '${columnId}'`)
  const ordered = cardsIn(board, columnId)
  const keys = spreadRanks(ordered.length)
  const ranks = new Map(ordered.map((card, index) => [card.id, keys[index] as string]))
  const cards = board.cards.map((card) => ({ ...card, rank: ranks.get(card.id) ?? card.rank }))
  return result(bump(board, ctx, cards), { kind: 'column.rebalanced', card_id: null, data: { ranks: Object.fromEntries(ranks) } })
}
