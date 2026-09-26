/**
 * Toolbar actions of the editor in Vue: the framework-free
 * `createEditorActions` with theme and suggestions as refs.
 */

import { computed } from 'vue'
import { createEditorActions, type ActionHandlers, type ActionOptions, type Theme } from '@flowaudit/bpmn-flowaudit/ui'
import { EMPTY_DIAGRAM } from '@flowaudit/bpmn-flowaudit'
import { useStore } from './useStore'
import type { useEditorSetup } from './useEditorSetup'

export type { ActionHandlers, ActionOptions, Theme } from '@flowaudit/bpmn-flowaudit/ui'

export function useEditorActions(setup: ReturnType<typeof useEditorSetup>, handlers: ActionHandlers, options: ActionOptions) {
  const actions = createEditorActions(setup.session, handlers, options)
  const state = useStore(actions.store)
  return {
    ...actions,
    suggestions: computed(() => state.value.suggestions),
    theme: computed<Theme>({ get: () => state.value.theme, set: (theme) => actions.setTheme(theme) }),
    emptyDiagram: EMPTY_DIAGRAM,
  }
}
