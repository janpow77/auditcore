/**
 * Verschieben per Tastatur (Aufnehmen/Ablegen mit Vorschau, Strg+Pfeile direkt)
 * und gemeinsame Vorschau für das Ziehen mit dem Zeiger. Ansagen stehen im
 * Zustand (`announcement`) für eine aria-live-Region; Texte liefert `t`.
 */
import type { Card } from '../model'
import { findCard } from '../model'
import { checkMove } from '../rules'
import type { ColumnView } from './board'
import type { BoardController } from './boardController'
import { applyPreview, locate, nudgeTarget, placementFor, siblingsOf, stepPreview, type MovePreview } from './movePreview'
import { createKanbanStore, type KanbanStore } from './store'

export type MoveMessageKey = 'grabbed' | 'movedTo' | 'dropped' | 'cancelled' | 'moveDenied' | 'wipWarning'
export type MoveTranslate = (key: MoveMessageKey, params?: Readonly<Record<string, string | number>>) => string
type Step = -1 | 0 | 1

export interface MoveState {
  preview: MovePreview | null
  grabbed: string | null
  announcement: string
}

export interface MoveControllerOptions {
  board: BoardController
  /** Sichtbare Spalten ohne Vorschau (`selectBoardView(...).columns`). */
  columns: () => readonly ColumnView[]
  canMove: () => boolean
  t: () => MoveTranslate
  /** Fokus nach dem nächsten Rendern auf die Karte setzen. */
  focusCard: (cardId: string) => void
}

export interface MoveController {
  store: KanbanStore<MoveState>
  allowed: (cardId: string, columnId: string) => boolean
  setPreview: (preview: MovePreview | null) => void
  commit: (cardId: string, target: MovePreview) => Promise<boolean>
  grab: (card: Card) => void
  cancel: () => void
  step: (dx: Step, dy: Step) => void
  drop: () => Promise<void>
  nudge: (card: Card, dx: Step, dy: Step) => Promise<void>
}

/** Spalten mit der bewegten Karte an der Vorschauposition (für die Anzeige). */
export function previewColumns(columns: readonly ColumnView[], state: MoveState): ColumnView[] {
  return applyPreview(columns, state.preview)
}

function createMoveCore(options: MoveControllerOptions, store: KanbanStore<MoveState>) {
  const board = () => options.board.store.get().board
  const columnLabel = (columnId: string): string => board()?.columns.find((column) => column.id === columnId)?.label ?? columnId
  const titleOf = (cardId: string): string => { const current = board(); return current ? findCard(current, cardId)?.title ?? '' : '' }
  const announce = (announcement: string): void => store.set({ announcement })
  // Jede Bedienung erhöht den Zähler; späte Port-Antworten überschreiben neuere Ansagen nicht.
  let ticket = 0
  const touch = (): number => ++ticket
  const isLatest = (mine: number): boolean => mine === ticket

  function check(cardId: string, columnId: string) {
    const current = board()
    const card = current ? findCard(current, cardId) : undefined
    return current && card ? checkMove(current, card, columnId) : null
  }
  const allowed = (cardId: string, columnId: string): boolean => Boolean(check(cardId, columnId)?.allowed)

  function describe(key: 'grabbed' | 'movedTo', cardId: string): void {
    const shown = previewColumns(options.columns(), store.get())
    const place = locate(shown, cardId)
    if (!place) return
    const count = shown.find((view) => view.column.id === place.columnId)?.cards.length ?? 0
    announce(options.t()(key, { title: titleOf(cardId), column: columnLabel(place.columnId), position: place.index + 1, count }))
  }

  function announceResult(cardId: string, target: MovePreview, warnings: readonly string[] | null): void {
    const t = options.t()
    if (!warnings) {
      const error = options.board.store.get().error
      if (error) announce(t('moveDenied', { reason: error.message }))
      return
    }
    const column = columnLabel(target.columnId)
    const wip = warnings.includes('WIP_LIMIT_REACHED') ? ` ${t('wipWarning', { column })}` : ''
    announce(`${t('dropped', { title: titleOf(cardId), column, position: target.index + 1 })}${wip}`)
  }

  /** Legt die Karte an der Vorschauposition ab und speichert über den Port. */
  async function commit(cardId: string, target: MovePreview): Promise<boolean> {
    const start = locate(options.columns(), cardId)
    store.set({ preview: null })
    if (start && start.columnId === target.columnId && start.index === target.index) return true
    if (!allowed(cardId, target.columnId)) {
      announce(options.t()('moveDenied', { reason: check(cardId, target.columnId)?.message ?? '' }))
      return false
    }
    const placement = placementFor(siblingsOf(options.columns(), target.columnId, cardId), target.index)
    const mine = touch()
    const result = await options.board.actions.move(cardId, target.columnId, placement)
    if (isLatest(mine)) {
      announceResult(cardId, target, result?.warnings ?? null)
      options.focusCard(cardId)
    }
    return Boolean(result)
  }

  return { allowed, describe, commit, titleOf, touch, announce }
}

export function createMoveController(options: MoveControllerOptions): MoveController {
  const store = createKanbanStore<MoveState>({ preview: null, grabbed: null, announcement: '' })
  const core = createMoveCore(options, store)

  function grab(card: Card): void {
    const place = locate(options.columns(), card.id)
    if (!place || !options.canMove()) return
    core.touch()
    store.set({ grabbed: card.id, preview: { cardId: card.id, ...place } })
    core.describe('grabbed', card.id)
  }

  function cancel(): void {
    const cardId = store.get().grabbed
    core.touch()
    store.set({ grabbed: null, preview: null })
    if (!cardId) return
    core.announce(options.t()('cancelled', { title: core.titleOf(cardId) }))
    options.focusCard(cardId)
  }

  function step(dx: Step, dy: Step): void {
    const current = store.get().preview
    const shown = previewColumns(options.columns(), store.get())
    const next = current ? stepPreview(shown, current, dx, dy, (columnId) => core.allowed(current.cardId, columnId)) : null
    if (!current || !next) return
    core.touch()
    store.set({ preview: next })
    core.describe('movedTo', current.cardId)
    options.focusCard(current.cardId)
  }

  async function drop(): Promise<void> {
    const current = store.get().preview
    store.set({ grabbed: null })
    if (current) await core.commit(current.cardId, current)
  }

  /** Strg+Pfeiltaste: sofort eine Position bzw. Spalte weiter (cockpit). */
  async function nudge(card: Card, dx: Step, dy: Step): Promise<void> {
    if (!options.canMove()) return
    const target = nudgeTarget(options.columns(), card.id, dx, dy, (columnId) => core.allowed(card.id, columnId))
    if (target) await core.commit(card.id, target)
  }

  const setPreview = (preview: MovePreview | null): void => store.set({ preview })
  return { store, allowed: core.allowed, setPreview, commit: core.commit, grab, cancel, step, drop, nudge }
}
