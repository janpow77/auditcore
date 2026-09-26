/** Board-Aktionen aus der Kernlogik (`createKanbanActions`): lokal optimistisch, danach über den Port. */
import type { KanbanActions } from '@auditcore/kanban-core'
import type { KanbanBoardState } from './useKanbanBoard'

export type { KanbanActions } from '@auditcore/kanban-core'

export function useKanbanActions(state: KanbanBoardState): KanbanActions {
  return state.controller.actions
}
