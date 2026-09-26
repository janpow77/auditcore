/**
 * Embeddable editor with the contract of the web component
 * `<flowaudit-bpmn-editor>` (same props, events with the same payload as
 * `CustomEvent.detail`, same ref methods) – natively in React, without Vue
 * and without a custom element.
 */

import { forwardRef, useImperativeHandle, useRef, useState, type CSSProperties } from 'react'
import type { Comment, DiagramInfo, ProfileData, StoragePort, ValidationPort } from '@auditcore/bpmn-flowaudit'
import type { EditorPorts, ElementEventMap, Theme } from '@auditcore/bpmn-flowaudit/ui'
import type { FlowauditEditorHandle } from '../editorProps'
import { FlowauditEditor } from '../FlowauditEditor'
import { useElementSource } from './useElementSource'

export interface FlowauditBpmnEditorProps {
  /** URL of a BPMN file (alternative to `xml` or `diagramId`). */
  src?: string
  /** Base URL of the REST contract (docs/bpmn/rest-api.md). */
  apiBase?: string
  diagramId?: string
  name?: string
  locale?: 'de' | 'en'
  theme?: Theme
  readonly?: boolean
  /** Profile id (loaded from the server or the bundled profiles). */
  profile?: string
  author?: string
  xml?: string
  storage?: StoragePort
  ports?: EditorPorts & { validation?: ValidationPort }
  profileData?: ProfileData | null
  comments?: Comment[]
  onReady?: (detail: ElementEventMap['ready']) => void
  onChange?: (detail: ElementEventMap['change']) => void
  onSave?: (detail: ElementEventMap['save']) => void
  onSelectionChange?: (detail: ElementEventMap['selection-change']) => void
  onDiagramInfoChange?: (detail: ElementEventMap['diagram-info-change']) => void
  onError?: (detail: ElementEventMap['error']) => void
  className?: string
  style?: CSSProperties
}

/** Methods available through the ref (as on the web component). */
export interface FlowauditBpmnEditorHandle {
  element: HTMLElement | null
  getXml(): Promise<string | undefined>
  getSvg(): Promise<string | undefined>
  select(elementId: string): void
  reload(): Promise<void>
}

export const FlowauditBpmnEditor = forwardRef<FlowauditBpmnEditorHandle, FlowauditBpmnEditorProps>(function FlowauditBpmnEditor(props, ref) {
  const root = useRef<HTMLDivElement | null>(null)
  const editor = useRef<FlowauditEditorHandle | null>(null)
  const [saving, setSaving] = useState(false)
  const source = useElementSource(props, (message) => props.onError?.({ message }))

  useImperativeHandle(ref, () => ({
    get element() {
      return root.current
    },
    getXml: async () => (await editor.current?.getXml()) ?? source.xml,
    getSvg: async () => editor.current?.getSvg(),
    select: (elementId: string) => void editor.current?.select(elementId),
    reload: source.reload,
  }))

  const onSave = async (payload: { xml: string; info: DiagramInfo | null }) => {
    setSaving(true)
    try {
      await source.persist(payload.xml)
      props.onSave?.(payload)
    } catch (error) {
      props.onError?.({ message: (error as Error).message })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div ref={root} className={props.className ? `flowaudit-bpmn-editor ${props.className}` : 'flowaudit-bpmn-editor'} style={props.style}>
      <FlowauditEditor
        ref={editor}
        xml={source.xml}
        name={props.name || props.diagramId || ''}
        diagramId={props.diagramId}
        profile={source.profile}
        ports={source.ports}
        locale={props.locale ?? 'de'}
        theme={props.theme ?? 'auto'}
        readonly={Boolean(props.readonly)}
        author={props.author ?? ''}
        comments={props.comments ?? []}
        saving={saving}
        onXmlChange={(xml) => (source.setXml(xml), props.onChange?.({ xml }))}
        onSave={(payload) => void onSave(payload)}
        onReady={() => props.onReady?.({ diagramId: props.diagramId })}
        onSelectionChange={(elementId) => props.onSelectionChange?.({ elementId })}
        onInfoChange={(info) => props.onDiagramInfoChange?.({ info })}
        onError={(message) => props.onError?.({ message })}
      />
    </div>
  )
})
