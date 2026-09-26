/** Such- und Filterzustand der Werkzeugleiste als `CardFilter` der Kernlogik. */
import type { CardFilter, DueState } from '../filtering'
import type { Priority } from '../model'

export interface KanbanFilterState {
  query: string
  priority: Priority | ''
  due: DueState | ''
  tag: string
}

export const EMPTY_FILTER: Readonly<KanbanFilterState> = { query: '', priority: '', due: '', tag: '' }

export function filterCriteria(state: KanbanFilterState): CardFilter {
  return {
    query: state.query,
    priorities: state.priority ? [state.priority] : [],
    due_states: state.due ? [state.due] : [],
    tags: state.tag ? [state.tag] : [],
  }
}
