/**
 * Reine Kartenbefehle (wie commands.py): Rechte, Validierung, Übergang und WIP
 * prüfen, dann neues Board plus Änderungen liefern. Ohne Ein-/Ausgabe – die
 * Oberfläche nutzt sie für optimistische Aktualisierung, der In-Memory-Port als Speicher.
 */
import { KanbanError, raiseIfDenied } from './errors'
import { asOptionalString, parseCardFields, type CardPatch } from './fields'
import { cardsIn, doneColumn, findCard, firstColumn, type Board, type Card, type JsonObject } from './model'
import { authorize, type Action } from './permissions'
import { rankBetween, spreadRanks } from './rank'
import { checkCapacity, checkMove } from './rules'
import { DEFAULT_LIMITS, type Limits } from './validation'

export interface Change {
  kind: string
  card_id: string | null
  data: JsonObject
}

export interface CommandContext {
  actor: string
  now: string
  inherited?: Readonly<Record<string, string>>
  limits?: Limits
  newId?: () => string
}

export interface CommandResult {
  board: Board
  changes: Change[]
  card: Card | null
  warnings: string[]
}

export interface Placement {
  before_id?: string | null
  after_id?: string | null
  index?: number | null
}

function randomId(): string {
  return globalThis.crypto.randomUUID().replace(/-/g, '')
}

export function requireAction(board: Board, ctx: CommandContext, action: Action): void {
  raiseIfDenied(authorize(board, ctx.actor, action, ctx.inherited))
}

/** Nächste Fassung des Boards. */
export function bump(board: Board, ctx: CommandContext, cards: Card[] = board.cards): Board {
  return { ...board, cards, version: board.version + 1, updated_at: ctx.now }
}

export function getCard(board: Board, cardId: string): Card {
  const card = findCard(board, cardId)
  if (!card) throw new KanbanError('CARD_NOT_FOUND', 'Karte nicht gefunden')
  return card
}

/** Einfügeposition unter den Geschwistern (Standard: Ende; Index wird geklemmt). */
export function resolveSlot(siblings: readonly Card[], placement: Placement = {}): number {
  const ids = siblings.map((card) => card.id)
  for (const [anchor, offset] of [[placement.before_id, 0], [placement.after_id, 1]] as const) {
    if (anchor !== null && anchor !== undefined) {
      const position = ids.indexOf(anchor)
      if (position < 0) throw new KanbanError('INVALID_REQUEST', 'Bezugskarte liegt nicht in der Zielspalte')
      return position + offset
    }
  }
  if (placement.index === null || placement.index === undefined) return siblings.length
  return Math.max(0, Math.min(placement.index, siblings.length))
}

function strictlyIncreasing(ranks: readonly string[]): boolean {
  return ranks.every((rank, index) => index === 0 || (ranks[index - 1] as string) < rank)
}

/** Rang für eine Karte an `slot`; verteilt die Spalte nur neu, wenn Ränge kollidieren. */
export function place(siblings: readonly Card[], slot: number): { rank: string; moved: Map<string, string> } {
  const ranks = siblings.map((card) => card.rank)
  if (strictlyIncreasing(ranks)) {
    const low = slot > 0 ? (ranks[slot - 1] ?? null) : null
    const high = slot < ranks.length ? (ranks[slot] ?? null) : null
    return { rank: rankBetween(low, high), moved: new Map() }
  }
  const keys = spreadRanks(siblings.length + 1)
  const [own] = keys.splice(slot, 1)
  return { rank: own as string, moved: new Map(siblings.map((card, index) => [card.id, keys[index] as string])) }
}

function applyRanks(cards: readonly Card[], moved: ReadonlyMap<string, string>): Card[] {
  return cards.map((card) => {
    const rank = moved.get(card.id)
    return rank === undefined ? card : { ...card, rank }
  })
}

function rebalanceChange(moved: ReadonlyMap<string, string>): Change[] {
  if (moved.size === 0) return []
  return [{ kind: 'column.rebalanced', card_id: null, data: { ranks: Object.fromEntries(moved) } }]
}

function slotFrom(fields: Readonly<Record<string, unknown>>, siblings: readonly Card[]): number {
  const index = fields.index
  if (index !== null && index !== undefined && (typeof index !== 'number' || !Number.isInteger(index))) {
    throw new KanbanError('INVALID_REQUEST', "Feld 'index' hat einen ungültigen Typ")
  }
  return resolveSlot(siblings, {
    before_id: asOptionalString('before_id', fields.before_id),
    after_id: asOptionalString('after_id', fields.after_id),
    index: index as number | null | undefined,
  })
}

function newCard(id: string, columnId: string, rank: string, title: string, now: string, patch: CardPatch): Card {
  const base: Card = {
    id, column_id: columnId, rank, title, description: '', priority: 'mittel', tags: [], assignees: [], due: null,
    color: null, image: null, badge: null, checklist: [], links: [], attachments: [], created_at: now, updated_at: now, extra: {},
  }
  return { ...base, ...patch }
}

/** Neue Karte in `column_id` (Standard: erste Spalte), angehängt, sofern keine Position angegeben ist. */
export function createCard(board: Board, ctx: CommandContext, fields: Readonly<Record<string, unknown>>): CommandResult {
  requireAction(board, ctx, 'create_card')
  const columnId = asOptionalString('column_id', fields.column_id) || firstColumn(board).id
  const capacity = checkCapacity(board, columnId)
  raiseIfDenied(capacity)
  const patch = parseCardFields(fields, ctx.limits ?? DEFAULT_LIMITS)
  if (patch.title === undefined) throw new KanbanError('VALIDATION_ERROR', 'Titel darf nicht leer sein')
  const cardId = asOptionalString('id', fields.id) || (ctx.newId ?? randomId)()
  if (findCard(board, cardId)) throw new KanbanError('VALIDATION_ERROR', 'Karten-ID existiert bereits')
  const siblings = cardsIn(board, columnId)
  const { rank, moved } = place(siblings, slotFrom(fields, siblings))
  const card = newCard(cardId, columnId, rank, patch.title, ctx.now, patch)
  const changes: Change[] = [{ kind: 'card.created', card_id: card.id, data: { column_id: columnId, rank } }, ...rebalanceChange(moved)]
  return { board: bump(board, ctx, [...applyRanks(board.cards, moved), card]), changes, card, warnings: capacity.warnings }
}

/** Verschiebt vor/hinter eine Karte oder an `index` (Standard: Ende). */
export function moveCard(board: Board, ctx: CommandContext, cardId: string, columnId: string, placement: Placement = {}): CommandResult {
  requireAction(board, ctx, 'move_card')
  const card = getCard(board, cardId)
  const decision = checkMove(board, card, columnId)
  raiseIfDenied(decision)
  const siblings = cardsIn(board, columnId).filter((entry) => entry.id !== cardId)
  const slot = resolveSlot(siblings, placement)
  const { rank, moved } = place(siblings, slot)
  const updated: Card = { ...card, column_id: columnId, rank, updated_at: ctx.now }
  const cards = applyRanks(board.cards, moved).map((entry) => (entry.id === cardId ? updated : entry))
  const data: JsonObject = { from: card.column_id, to: columnId, rank, index: slot }
  const changes: Change[] = [{ kind: 'card.moved', card_id: cardId, data }, ...rebalanceChange(moved)]
  return { board: bump(board, ctx, cards), changes, card: updated, warnings: decision.warnings }
}

/** Ändert Felder; eine andere `column_id` verschiebt ans Ende dieser Spalte. */
export function updateCard(board: Board, ctx: CommandContext, cardId: string, fields: Readonly<Record<string, unknown>>): CommandResult {
  requireAction(board, ctx, 'edit_card')
  const patch = parseCardFields(fields, ctx.limits ?? DEFAULT_LIMITS)
  const card = getCard(board, cardId)
  const target = asOptionalString('column_id', fields.column_id)
  const prefix = target !== null && target !== card.column_id ? moveCard(board, ctx, cardId, target) : null
  const base = prefix?.board ?? board
  const updated: Card = { ...getCard(base, cardId), updated_at: ctx.now, ...patch }
  const cards = base.cards.map((entry) => (entry.id === cardId ? updated : entry))
  const next = prefix ? { ...base, cards } : bump(base, ctx, cards)
  const change: Change = { kind: 'card.updated', card_id: cardId, data: { fields: Object.keys(patch).sort() } }
  return { board: next, changes: [...(prefix?.changes ?? []), change], card: updated, warnings: prefix?.warnings ?? [] }
}

export function deleteCard(board: Board, ctx: CommandContext, cardId: string): CommandResult {
  requireAction(board, ctx, 'delete_card')
  const card = getCard(board, cardId)
  const cards = board.cards.filter((entry) => entry.id !== cardId)
  return { board: bump(board, ctx, cards), changes: [{ kind: 'card.deleted', card_id: cardId, data: { column_id: card.column_id } }], card, warnings: [] }
}

/** Erledigt-Spalte → oben in die erste Spalte; sonst → ans Ende der Erledigt-Spalte. */
export function toggleDone(board: Board, ctx: CommandContext, cardId: string): CommandResult {
  const card = getCard(board, cardId)
  const done = doneColumn(board)
  if (card.column_id === done.id) return moveCard(board, ctx, cardId, firstColumn(board).id, { index: 0 })
  return moveCard(board, ctx, cardId, done.id)
}
