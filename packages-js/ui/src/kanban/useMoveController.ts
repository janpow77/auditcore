/**
 * Verschieben per Tastatur (Aufnehmen/Ablegen mit Vorschau, Strg+Pfeile direkt)
 * und gemeinsame Vorschau für das Ziehen mit dem Zeiger. Meldungen gehen an
 * eine aria-live-Region.
 */
import { computed, nextTick, ref, type Ref } from 'vue'
import { checkMove, findCard, type Card } from '@flowaudit/kanban-core'
import type { Translate } from '../i18n'
import type { KanbanMessageKey } from './messages'
import { applyPreview, locate, nudgeTarget, placementFor, siblingsOf, stepPreview, type MovePreview } from './movePreview'
import type { KanbanActions } from './useKanbanActions'
import type { KanbanBoardState } from './useKanbanBoard'

type Step = -1 | 0 | 1

/** Vorschau, Regeln, Ansagen und das Ablegen über den Port. */
function useMoveCore(state: KanbanBoardState, actions: KanbanActions, t: Translate<KanbanMessageKey>, root: Ref<HTMLElement | null>) {
  const preview = ref<MovePreview | null>(null)
  const announcement = ref('')
  const columns = computed(() => applyPreview(state.columns.value, preview.value))
  const columnLabel = (columnId: string): string => state.board.value?.columns.find((column) => column.id === columnId)?.label ?? columnId
  const titleOf = (cardId: string): string => (state.board.value ? findCard(state.board.value, cardId)?.title ?? '' : '')
  // Jede Bedienung erhöht den Zähler; späte Port-Antworten überschreiben neuere Ansagen nicht.
  let ticket = 0
  const touch = (): number => ++ticket

  function check(cardId: string, columnId: string) {
    const board = state.board.value
    const card = board ? findCard(board, cardId) : undefined
    return board && card ? checkMove(board, card, columnId) : null
  }
  const allowed = (cardId: string, columnId: string): boolean => Boolean(check(cardId, columnId)?.allowed)

  function describe(key: 'grabbed' | 'movedTo', cardId: string): void {
    const place = locate(columns.value, cardId)
    if (!place) return
    const count = columns.value.find((view) => view.column.id === place.columnId)?.cards.length ?? 0
    announcement.value = t(key, { title: titleOf(cardId), column: columnLabel(place.columnId), position: place.index + 1, count })
  }

  function focusCard(cardId: string): void {
    void nextTick(() => root.value?.querySelector<HTMLElement>(`[data-card-id="${CSS.escape(cardId)}"]`)?.focus())
  }

  function announceResult(cardId: string, target: MovePreview, warnings: readonly string[] | null): void {
    if (!warnings) {
      if (state.error.value) announcement.value = t('moveDenied', { reason: state.error.value.message })
      return
    }
    const column = columnLabel(target.columnId)
    announcement.value = t('dropped', { title: titleOf(cardId), column, position: target.index + 1 })
    if (warnings.includes('WIP_LIMIT_REACHED')) announcement.value += ` ${t('wipWarning', { column })}`
  }

  /** Legt die Karte an der Vorschauposition ab und speichert über den Port. */
  async function commit(cardId: string, target: MovePreview): Promise<boolean> {
    const start = locate(state.columns.value, cardId)
    preview.value = null
    if (start && start.columnId === target.columnId && start.index === target.index) return true
    if (!allowed(cardId, target.columnId)) {
      announcement.value = t('moveDenied', { reason: check(cardId, target.columnId)?.message ?? '' })
      return false
    }
    const placement = placementFor(siblingsOf(state.columns.value, target.columnId, cardId), target.index)
    const mine = touch()
    const result = await actions.move(cardId, target.columnId, placement)
    if (mine === ticket) {
      announceResult(cardId, target, result?.warnings ?? null)
      focusCard(cardId)
    }
    return Boolean(result)
  }

  return { preview, announcement, columns, allowed, describe, focusCard, commit, titleOf, touch }
}

export function useMoveController(state: KanbanBoardState, actions: KanbanActions, t: Translate<KanbanMessageKey>, root: Ref<HTMLElement | null>) {
  const core = useMoveCore(state, actions, t, root)
  const grabbed = ref<string | null>(null)

  function grab(card: Card): void {
    const place = locate(state.columns.value, card.id)
    if (!place || !state.can.value.move) return
    core.touch()
    grabbed.value = card.id
    core.preview.value = { cardId: card.id, ...place }
    core.describe('grabbed', card.id)
  }

  function cancel(): void {
    const cardId = grabbed.value
    core.touch()
    grabbed.value = null
    core.preview.value = null
    if (!cardId) return
    core.announcement.value = t('cancelled', { title: core.titleOf(cardId) })
    core.focusCard(cardId)
  }

  function step(dx: Step, dy: Step): void {
    const current = core.preview.value
    const next = current ? stepPreview(core.columns.value, current, dx, dy, (columnId) => core.allowed(current.cardId, columnId)) : null
    if (!current || !next) return
    core.touch()
    core.preview.value = next
    core.describe('movedTo', current.cardId)
    core.focusCard(current.cardId)
  }

  async function drop(): Promise<void> {
    const current = core.preview.value
    grabbed.value = null
    if (current) await core.commit(current.cardId, current)
  }

  /** Strg+Pfeiltaste: sofort eine Position bzw. Spalte weiter (cockpit). */
  async function nudge(card: Card, dx: Step, dy: Step): Promise<void> {
    if (!state.can.value.move) return
    const target = nudgeTarget(state.columns.value, card.id, dx, dy, (columnId) => core.allowed(card.id, columnId))
    if (target) await core.commit(card.id, target)
  }

  return { ...core, grabbed, grab, cancel, step, drop, nudge }
}

export type MoveController = ReturnType<typeof useMoveController>
