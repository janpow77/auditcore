// Vue-Anbindung der Datenbankansicht als Kanban (Zustandsautomat aus @flowaudit/ui-core).

import { computed, type ComputedRef, type Ref } from 'vue'
import type { RecordPort } from '@flowaudit/kanban-core'
import {
  createDbKanbanController,
  dbKanbanView,
  type DbKanbanController,
  type DbKanbanData,
  type DbKanbanHooks,
  type DbKanbanTranslate,
  type DbKanbanView,
} from '@flowaudit/ui-core'
import { useStore } from '../composables/useStore'

export interface DbKanbanSource {
  port: () => RecordPort | null
  t: () => DbKanbanTranslate
  lang: () => string
  editable: () => boolean
}

export interface UseDbKanban {
  controller: DbKanbanController
  state: Readonly<Ref<DbKanbanData>>
  view: ComputedRef<DbKanbanView>
}

export function useDbKanban(source: DbKanbanSource, hooks: DbKanbanHooks = {}): UseDbKanban {
  const controller = createDbKanbanController({ ...hooks, ...source })
  const state = useStore(controller.store)
  const view = computed(() => dbKanbanView(state.value, source.t(), source.lang()))
  return { controller, state, view }
}
