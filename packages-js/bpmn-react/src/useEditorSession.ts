/**
 * One editor session in React: creates the framework-free session, actions
 * and exporter on mount (so React's strict mode can dispose and recreate
 * them), imports the XML and keeps props, callbacks and view state in sync.
 */

import { useEffect, useRef, useState } from 'react'
import {
  createEditorActions,
  createEditorSession,
  createExporter,
  createStore,
  initialUiState,
  isLocked,
  savePayload,
  type EditorActions,
  type EditorSession,
  type Store,
  type Translate,
  type UiState,
} from '@auditcore/bpmn-flowaudit/ui'
import type { DiagramInfo, ProfileData } from '@auditcore/bpmn-flowaudit'
import { defaultEditorFactory } from './editorFactory'
import type { FlowauditEditorProps } from './editorProps'
import { useI18n } from './i18n'

export interface EditorRuntime {
  session: EditorSession
  actions: EditorActions
  ui: Store<UiState>
  save: () => Promise<void>
  isReadonly: () => boolean
  profile: () => ProfileData | null
}

/** Structural ref types, valid with the typings of React 18 and 19. */
type Latest = { readonly current: FlowauditEditorProps }
export type HostRef = { current: HTMLDivElement | null }

function readonlyNow(latest: Latest, session: EditorSession | null): boolean {
  const props = latest.current
  return isLocked(Boolean(props.readonly), props.lockApproved ?? true, session?.editor.store.get().info ?? null)
}

function handlers(latest: Latest, runtime: () => EditorRuntime, ui: Store<UiState>) {
  const call = <K extends keyof FlowauditEditorProps>(name: K) => latest.current[name] as ((...args: never[]) => void) | undefined
  return {
    save: () => void runtime().save(),
    newDiagram: () => call('onNew')?.(),
    analysis: () => call('onAnalysis')?.(),
    share: () => call('onShare')?.(),
    excel: () => call('onExportExcel')?.(),
    approve: async (info: DiagramInfo) => latest.current.onApprove?.({ xml: await runtime().session.editor.exportXml(), info }),
    message: (text: string) => ui.set({ message: text }),
  }
}

function createRuntime(latest: Latest, host: () => HTMLElement | null, t: Translate): EditorRuntime {
  const props = latest.current
  const ui = createStore<UiState>(initialUiState())
  const factory = props.editorFactory ?? defaultEditorFactory
  let runtime: EditorRuntime | null = null
  const session = createEditorSession({
    ui,
    host,
    factory,
    locale: props.locale ?? 'de',
    ports: props.ports ?? {},
    profile: () => latest.current.profile ?? null,
    readonly: () => readonlyNow(latest, session),
    onXml: (xml) => latest.current.onXmlChange?.(xml),
    onError: (message) => (ui.set({ message: t('editor.importError', { message }) }), latest.current.onError?.(message)),
  })
  const exporter = createExporter({ editor: session.editor, factory, name: () => latest.current.name ?? '', diagramId: () => latest.current.diagramId, profile: () => latest.current.profile ?? null, author: () => latest.current.author ?? '', replacements: () => latest.current.replacements ?? {}, palette: props.palette })
  const actions = createEditorActions(session, handlers(latest, () => runtime as EditorRuntime, ui), { profile: () => latest.current.profile ?? null, roleAliases: () => latest.current.roleAliases ?? [], exporter, t })
  const save = async () => {
    if (readonlyNow(latest, session)) return
    // Always mark the editor saved, even without a callback (as the Vue `save` does).
    const payload = await savePayload(session)
    latest.current.onSave?.(payload)
  }
  runtime = { session, actions, ui, save, isReadonly: () => readonlyNow(latest, session), profile: () => latest.current.profile ?? null }
  return runtime
}

/** Reports selection and diagram info changes to the callbacks. */
function useReports(runtime: EditorRuntime | null, latest: Latest): void {
  useEffect(() => {
    if (!runtime) return undefined
    const { editor, selection } = runtime.session
    let elementId: string | null = null
    let info = editor.store.get().info
    const stopSelection = selection.store.subscribe(() => {
      const next = selection.store.get().element?.id ?? null
      if (next === elementId) return
      elementId = next
      latest.current.onSelectionChange?.(next)
    })
    const stopInfo = editor.store.subscribe(() => {
      const next = editor.store.get().info
      if (next === info) return
      info = next
      latest.current.onInfoChange?.(next)
    })
    return () => {
      stopSelection()
      stopInfo()
    }
  }, [runtime, latest])
}

/** Applies prop changes after mount: XML, profile, theme. */
function usePropSync(runtime: EditorRuntime | null, props: FlowauditEditorProps): void {
  const profileSeen = useRef(props.profile)
  useEffect(() => {
    if (runtime) void runtime.session.load(props.xml)
  }, [runtime, props.xml])
  useEffect(() => {
    if (!runtime || profileSeen.current === props.profile) return
    profileSeen.current = props.profile
    runtime.session.applyProfile()
  }, [runtime, props.profile])
  useEffect(() => {
    if (runtime && props.theme) runtime.actions.setTheme(props.theme)
  }, [runtime, props.theme])
}

export function useEditorSession(props: FlowauditEditorProps, host: HostRef): EditorRuntime | null {
  const { t } = useI18n()
  const latest = useRef(props)
  const translate = useRef(t)
  const [runtime, setRuntime] = useState<EditorRuntime | null>(null)

  useEffect(() => {
    latest.current = props
    translate.current = t
  })

  // The session lives as long as the component; later prop changes are synced separately.
  useEffect(() => {
    const created = createRuntime(latest, () => host.current, (key, params) => translate.current(key, params))
    created.session.mount()
    setRuntime(created)
    void created.session.load(latest.current.xml).then(() => latest.current.onReady?.())
    return () => created.session.dispose()
  }, [host])

  useReports(runtime, latest)
  usePropSync(runtime, props)
  return runtime
}
