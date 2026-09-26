import { computed, reactive } from 'vue'
import { EMPTY_FILTER, filterCriteria, isFilterActive, type KanbanFilterState } from '@auditcore/kanban-core'

export type { KanbanFilterState } from '@auditcore/kanban-core'

/** Such- und Filterzustand des Boards (Toolbar) als CardFilter der Kernlogik. */
export function useKanbanFilter() {
  const state = reactive<KanbanFilterState>({ ...EMPTY_FILTER })
  const criteria = computed(() => filterCriteria(state))
  const active = computed(() => isFilterActive(criteria.value))
  function reset(): void {
    Object.assign(state, EMPTY_FILTER)
  }
  return { state, criteria, active, reset }
}

export type KanbanFilter = ReturnType<typeof useKanbanFilter>
