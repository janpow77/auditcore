/**
 * FlowAudit BPMN editor (native React): toolbar, palette, canvas with page
 * grid, side panel (properties, issues, walk-through, comparison), status
 * bar and dialogs. Same props and events as the Vue `FlowauditEditor`; the
 * XML is controlled through `xml` and `onXmlChange`.
 */

import { forwardRef, useImperativeHandle, useMemo, useRef, type KeyboardEvent } from 'react'
import { createStore, dialogPatch, handleShortcut, initialUiState, INITIAL_EDITOR_STATE, type ActionState } from '@auditcore/bpmn-flowaudit/ui'
import type { KeyKind } from '@auditcore/bpmn-flowaudit'
import { EditorContextProvider, type EditorContext } from './context'
import { EditorCanvas } from './EditorCanvas'
import { EditorChrome, EditorFooter, EditorSide } from './EditorChrome'
import { EditorDialogs } from './EditorDialogs'
import type { FlowauditEditorHandle, FlowauditEditorProps } from './editorProps'
import { classes, useStoreState } from './hooks'
import { I18nProvider } from './i18n'
import { useEditorSession, type EditorRuntime } from './useEditorSession'

const IDLE_UI = createStore(initialUiState())
const IDLE_EDITOR = createStore(INITIAL_EDITOR_STATE)
const IDLE_ACTIONS = createStore<ActionState>({ theme: 'auto', suggestions: [] })

function handleOf(runtime: EditorRuntime | null): FlowauditEditorHandle {
  const session = runtime?.session
  return {
    getXml: async () => session?.editor.exportXml(),
    getSvg: async () => session?.editor.exportSvg(),
    select: (id: string) => Boolean(session?.editor.select(id)),
    highlightKey: (kind: KeyKind, value: string) => session?.updateUi({ filterOpen: true, filterKind: kind, filterValue: value }),
    editor: session?.editor ?? null,
    validation: session?.validation ?? null,
  }
}

function useContextValue(runtime: EditorRuntime | null, props: FlowauditEditorProps): EditorContext | null {
  const ports = props.ports
  return useMemo(() => {
    if (!runtime) return null
    const { editor, selection, validation } = runtime.session
    return { editor, selection, validation, ports: ports ?? {}, profile: runtime.profile, readonly: runtime.isReadonly }
  }, [runtime, ports])
}

function Dialogs({ runtime, props }: { runtime: EditorRuntime | null; props: FlowauditEditorProps }) {
  if (!runtime) return null
  return <EditorDialogs runtime={runtime} name={props.name ?? ''} diagramId={props.diagramId} profiles={props.profiles ?? []} approvals={props.approvals ?? []} ports={props.ports ?? {}} onApplyXml={(xml) => props.onXmlChange?.(xml)} />
}

function shortcutHandler(runtime: EditorRuntime | null) {
  return (event: KeyboardEvent) => {
    if (!runtime) return
    const open = (id: 'search' | 'shortcuts') => () => runtime.ui.set(dialogPatch(runtime.ui.get(), id, true))
    handleShortcut(event.nativeEvent, { save: () => void runtime.save(), search: open('search'), help: open('shortcuts') })
  }
}

const EditorShell = forwardRef<FlowauditEditorHandle, FlowauditEditorProps>(function EditorShell(props, ref) {
  const host = useRef<HTMLDivElement | null>(null)
  const runtime = useEditorSession(props, host)
  const context = useContextValue(runtime, props)
  const ui = useStoreState(runtime?.ui ?? IDLE_UI)
  useStoreState(runtime?.session.editor.store ?? IDLE_EDITOR)
  const { theme } = useStoreState(runtime?.actions.store ?? IDLE_ACTIONS)
  useImperativeHandle(ref, () => handleOf(runtime), [runtime])
  const readonly = runtime ? runtime.isReadonly() : Boolean(props.readonly)
  const parts = { runtime, props, ui, readonly }

  return (
    <EditorContextProvider value={context}>
      <div className={classes('fa-root fa-editor', props.className)} data-fa-theme={theme} lang={props.locale ?? 'de'} onKeyDown={shortcutHandler(runtime)}>
        <EditorChrome {...parts} />
        <div className="fa-editor__body">
          <EditorSide {...parts} part="palette" />
          <main className="fa-editor__main">
            <EditorSide {...parts} part="filter" />
            <EditorCanvas host={host} runtime={runtime} pageView={ui.pageView} readonly={readonly} profile={props.profile ?? null} palette={props.palette} />
            <EditorFooter {...parts} />
          </main>
          <EditorSide {...parts} part="side" />
        </div>
        <Dialogs runtime={runtime} props={props} />
      </div>
    </EditorContextProvider>
  )
})

export const FlowauditEditor = forwardRef<FlowauditEditorHandle, FlowauditEditorProps>(function FlowauditEditor(props, ref) {
  return (
    <I18nProvider locale={props.locale ?? 'de'}>
      <EditorShell {...props} ref={ref} />
    </I18nProvider>
  )
})
