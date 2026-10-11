// Vue-Anbindung des Assistenten-Zustandsautomaten aus @auditcore/ui-core.

import { computed, type ComputedRef, type Ref } from 'vue'
import {
  assistantView,
  createAssistantController,
  type AssistantController,
  type AssistantData,
  type AssistantPort,
  type AssistantView,
  type DataProtectionError,
  type DataProtectionTranslate,
  type WorkspaceOverview,
} from '@auditcore/ui-core'
import { useStore } from '../composables/useStore'

export interface AssistantHooks {
  onChange?: (overview: WorkspaceOverview) => void
  onError?: (error: DataProtectionError) => void
}

export interface AssistantVueState {
  controller: AssistantController
  state: Readonly<Ref<AssistantData>>
  view: ComputedRef<AssistantView>
}

export function useAssistant(
  port: () => AssistantPort | null,
  activityId: () => string,
  t: () => DataProtectionTranslate,
  hooks: AssistantHooks = {},
): AssistantVueState {
  const controller = createAssistantController({ ...hooks, port, activityId, t })
  const state = useStore(controller.store)
  return { controller, state, view: computed(() => assistantView(state.value)) }
}
