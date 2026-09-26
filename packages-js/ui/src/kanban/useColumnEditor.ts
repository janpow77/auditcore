/** Vue-Anbindung des Spalteneditors (`createColumnEditor` aus `@auditcore/kanban-core`). */
import { computed } from 'vue'
import { createColumnEditor, DEFAULT_LIMITS, selectColumnEditor } from '@auditcore/kanban-core'
import { useStore } from '../composables/useStore'

export function useColumnEditor(maxColumns = DEFAULT_LIMITS.columns_max) {
  const editor = createColumnEditor(maxColumns)
  const state = useStore(editor.store)
  const view = computed(() => selectColumnEditor(state.value, maxColumns))
  return {
    draft: computed(() => state.value.draft),
    problem: computed(() => state.value.problem),
    canAdd: computed(() => view.value.canAdd),
    canRemove: computed(() => view.value.canRemove),
    dirty: computed(() => view.value.dirty),
    removed: computed(() => view.value.removed),
    reset: editor.reset,
    add: editor.add,
    remove: editor.remove,
    move: editor.move,
    update: editor.update,
    validated: editor.validated,
  }
}
