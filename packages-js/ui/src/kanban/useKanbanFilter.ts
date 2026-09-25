import { computed, reactive } from 'vue'
import { isFilterActive, type CardFilter, type DueState, type Priority } from '@flowaudit/kanban-core'

export interface KanbanFilterState {
  query: string
  priority: Priority | ''
  due: DueState | ''
  tag: string
}

/** Such- und Filterzustand des Boards (Toolbar) als CardFilter der Kernlogik. */
export function useKanbanFilter() {
  const state = reactive<KanbanFilterState>({ query: '', priority: '', due: '', tag: '' })
  const criteria = computed<CardFilter>(() => ({
    query: state.query,
    priorities: state.priority ? [state.priority] : [],
    due_states: state.due ? [state.due] : [],
    tags: state.tag ? [state.tag] : [],
  }))
  const active = computed(() => isFilterActive(criteria.value))
  function reset(): void {
    Object.assign(state, { query: '', priority: '', due: '', tag: '' })
  }
  return { state, criteria, active, reset }
}

export type KanbanFilter = ReturnType<typeof useKanbanFilter>
