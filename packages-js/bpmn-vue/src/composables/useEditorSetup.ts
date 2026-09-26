/**
 * Setup of one editor in Vue: the framework-free editor session
 * (`createEditorSession`) with a reactive view state, the stores bound to
 * Vue and provided as context, and watchers for props and view state.
 */

import { computed, onBeforeUnmount, reactive, watch, type Ref } from 'vue'
import { createEditorSession, initialUiState, type EditorFactory, type Popover, type UiState } from '@flowaudit/bpmn-flowaudit/ui'
import type { FlowauditModuleOptions, ProfileData, ValidationPort } from '@flowaudit/bpmn-flowaudit'
import { defaultEditorFactory } from '../editor/defaultFactory'
import { bindEditorCore } from '../stores/editorStore'
import { bindSelectionCore } from '../stores/selectionStore'
import { bindValidationCore } from '../stores/validationStore'
import { provideEditorContext, type EditorPorts } from '../stores/context'
import { useStore } from './useStore'

export type { DialogId, Popover, SideView } from '@flowaudit/bpmn-flowaudit/ui'

export interface EditorSetupOptions {
  xml: () => string
  profile: () => ProfileData | null
  readonly: () => boolean
  locale: 'de' | 'en'
  ports: EditorPorts & { validation?: ValidationPort }
  factory?: EditorFactory
  flowaudit?: FlowauditModuleOptions
  onXml: (xml: string) => void
  onError: (message: string) => void
}

export function useEditorSetup(host: Ref<HTMLElement | null>, options: EditorSetupOptions) {
  const ui = reactive<UiState>(initialUiState())
  const session = createEditorSession({ ...options, factory: options.factory ?? defaultEditorFactory, host: () => host.value, ui: { get: () => ui, set: (patch) => Object.assign(ui, patch) } })
  const editor = bindEditorCore(session.editor)
  const selection = bindSelectionCore(session.selection)
  const validation = bindValidationCore(session.validation)
  provideEditorContext({ editor, selection, validation, ports: options.ports, profile: options.profile, readonly: options.readonly })

  const canvas = useStore(session.canvas)
  const popover = computed<Popover | null>({ get: () => canvas.value.popover, set: (value) => session.canvas.set({ popover: value }) })

  watch(options.xml, session.load)
  watch(() => ui.decorations, session.applyDecorations)
  watch(() => [ui.filterOpen, ui.filterKind, ui.filterValue], session.refreshKeyFilter)
  watch(options.profile, session.applyProfile)
  onBeforeUnmount(session.dispose)

  return {
    session,
    editor,
    selection,
    validation,
    ui,
    viewbox: computed(() => canvas.value.viewbox),
    size: computed(() => canvas.value.size),
    palette: computed(() => canvas.value.palette),
    popover,
    mount: session.mount,
    load: session.load,
    setDirection: session.setDirection,
    trigger: session.trigger,
    readonlyNow: computed(options.readonly),
  }
}
