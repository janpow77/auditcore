/** Vue-Anbindung der Boardliste (`createBoardListController` aus `@flowaudit/kanban-core`). */
import { computed } from 'vue'
import { createBoardListController, selectBoardList, type BoardPort } from '@flowaudit/kanban-core'
import { useStore } from '../composables/useStore'

export { sortBoards } from '@flowaudit/kanban-core'

export function useBoardList(port: () => BoardPort | null | undefined) {
  const controller = createBoardListController(port)
  const state = useStore(controller.store)
  const view = computed(() => selectBoardList(state.value))
  return {
    boards: computed(() => state.value.boards),
    own: computed(() => view.value.own),
    shared: computed(() => view.value.shared),
    loading: computed(() => state.value.loading),
    error: computed(() => state.value.error),
    canCreate: computed(() => controller.canCreate()),
    load: controller.load,
    togglePin: controller.togglePin,
    remove: controller.remove,
    create: controller.create,
  }
}
