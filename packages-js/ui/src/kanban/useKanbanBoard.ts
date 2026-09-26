/**
 * Vue-Anbindung des Board-Zustandsautomaten aus `@flowaudit/kanban-core`
 * (`createBoardController`, `selectBoardView`): gleiche Logik wie die
 * React-Fassung, hier als Refs.
 */
import { computed, watch } from 'vue'
import { createBoardController, selectBoardView, type Board, type BoardPort, type CardFilter, type KanbanError } from '@flowaudit/kanban-core'
import { useStore } from '../composables/useStore'

export { columnViews, toKanbanError, uiCapabilities, type ColumnView } from '@flowaudit/kanban-core'

export interface KanbanBoardOptions {
  port: () => BoardPort | null | undefined
  boardId: () => string
  criteria: () => CardFilter
  readOnly?: () => boolean
  today?: () => string | undefined
  onError?: (error: KanbanError) => void
  onChange?: (board: Board) => void
}

export function useKanbanBoard(options: KanbanBoardOptions) {
  const controller = createBoardController(options)
  const state = useStore(controller.store)
  const userId = computed(() => options.port()?.userId ?? '')
  const view = computed(() => selectBoardView(state.value, { userId: userId.value, criteria: options.criteria(), readOnly: options.readOnly?.(), today: options.today?.() }))
  watch([() => options.port(), () => options.boardId()], () => void controller.load())
  return {
    controller,
    board: computed(() => state.value.board),
    loading: computed(() => state.value.loading),
    error: computed(() => state.value.error),
    warnings: computed(() => state.value.warnings),
    userId,
    role: computed(() => view.value.role),
    can: computed(() => view.value.can),
    today: computed(() => view.value.today),
    stats: computed(() => view.value.stats),
    columns: computed(() => view.value.columns),
    load: controller.load,
    mutate: controller.mutate,
  }
}

export type KanbanBoardState = ReturnType<typeof useKanbanBoard>
