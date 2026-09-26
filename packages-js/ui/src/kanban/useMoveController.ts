/**
 * Vue-Anbindung von `createMoveController` (Tastatur-Verschieben mit Vorschau,
 * Strg+Pfeile, Ansagen für aria-live); gleiche Logik wie die React-Fassung.
 */
import { computed, nextTick, type Ref } from 'vue'
import { createMoveController, previewColumns, type KanbanActions } from '@auditcore/kanban-core'
import type { Translate } from '../i18n'
import type { KanbanMessageKey } from './messages'
import { useStore } from '../composables/useStore'
import type { KanbanBoardState } from './useKanbanBoard'

export function focusCardIn(root: HTMLElement | null, cardId: string): void {
  root?.querySelector<HTMLElement>(`[data-card-id="${CSS.escape(cardId)}"]`)?.focus()
}

export function useMoveController(state: KanbanBoardState, _actions: KanbanActions, t: Translate<KanbanMessageKey>, root: Ref<HTMLElement | null>) {
  const controller = createMoveController({
    board: state.controller,
    columns: () => state.columns.value,
    canMove: () => state.can.value.move,
    t: () => t,
    focusCard: (cardId) => void nextTick(() => focusCardIn(root.value, cardId)),
  })
  const move = useStore(controller.store)
  return {
    ...controller,
    controller,
    preview: computed(() => move.value.preview),
    grabbed: computed(() => move.value.grabbed),
    announcement: computed(() => move.value.announcement),
    columns: computed(() => previewColumns(state.columns.value, move.value)),
  }
}

export type MoveController = ReturnType<typeof useMoveController>
