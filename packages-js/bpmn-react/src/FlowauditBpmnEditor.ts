/**
 * React wrapper around the web component `<flowaudit-bpmn-editor>`.
 *
 * No UI is rebuilt in React: string settings become attributes, objects
 * (XML, ports, profile) are set as element properties through a ref, and
 * the custom events are bound with `addEventListener` to typed `onXyz`
 * callbacks. Works the same with React 18.3 and 19 because nothing relies
 * on React's handling of custom elements.
 */

import { createElement, forwardRef, useEffect, useImperativeHandle, useLayoutEffect, useRef, type CSSProperties } from 'react'
import type { CataloguePort, Comment, DiagramInfo, EsiPort, LegalSearchPort, ProfileData, StoragePort, ValidationPort } from '@flowaudit/bpmn-flowaudit'
import { ATTRIBUTE_PROPS, EVENT_PROPS, ELEMENT_NAME, type AttributeProp, type EventProp } from './contract'

/** Application ports of the editor (same as `EditorPorts` of @flowaudit/bpmn-vue). */
export interface EditorPorts {
  legalSearch?: LegalSearchPort
  catalogue?: CataloguePort
  esi?: EsiPort
  validation?: ValidationPort
}

export interface FlowauditBpmnEditorProps {
  /** URL of a BPMN file (alternative to `xml` or `diagramId`). */
  src?: string
  /** Base URL of the REST contract (docs/bpmn/rest-api.md). */
  apiBase?: string
  diagramId?: string
  name?: string
  locale?: 'de' | 'en'
  theme?: 'auto' | 'light' | 'dark'
  readonly?: boolean
  /** Profile id (loaded from the server or the bundled profiles). */
  profile?: string
  author?: string
  /** Object properties. */
  xml?: string
  storage?: StoragePort
  ports?: EditorPorts
  profileData?: ProfileData | null
  comments?: Comment[]
  /** Events. */
  onReady?: (detail: { diagramId?: string }) => void
  onChange?: (detail: { xml: string }) => void
  onSave?: (detail: { xml: string; info: DiagramInfo | null }) => void
  onSelectionChange?: (detail: { elementId: string | null }) => void
  onDiagramInfoChange?: (detail: { info: DiagramInfo | null }) => void
  onError?: (detail: { message: string }) => void
  className?: string
  style?: CSSProperties
}

/** Methods of the element, available through the ref. */
export interface FlowauditBpmnEditorHandle {
  element: HTMLElement | null
  getXml(): Promise<string | undefined>
  getSvg(): Promise<string | undefined>
  select(elementId: string): void
}

/** The element exposes the methods of its root component (Vue ≥ 3.5). */
interface EditorElement extends HTMLElement {
  getXml?(): Promise<string>
  getSvg?(): Promise<string>
  select?(elementId: string): void
}

const OBJECT_PROPS = ['xml', 'storage', 'ports', 'profileData', 'comments'] as const

function syncAttribute(element: HTMLElement, name: string, value: string | boolean | undefined): void {
  if (value === undefined || value === false || value === '') element.removeAttribute(name)
  else element.setAttribute(name, value === true ? '' : value)
}

export const FlowauditBpmnEditor = forwardRef<FlowauditBpmnEditorHandle, FlowauditBpmnEditorProps>(function FlowauditBpmnEditor(props, ref) {
  const elementRef = useRef<EditorElement | null>(null)
  const callbacks = useRef(props)
  callbacks.current = props

  useLayoutEffect(() => {
    const element = elementRef.current
    if (!element) return
    for (const [prop, attribute] of Object.entries(ATTRIBUTE_PROPS) as [AttributeProp, string][]) syncAttribute(element, attribute, props[prop])
  })

  useLayoutEffect(() => {
    const element = elementRef.current as (EditorElement & Record<string, unknown>) | null
    if (!element) return
    for (const key of OBJECT_PROPS) if (props[key] !== undefined && element[key] !== props[key]) element[key] = props[key]
  })

  useEffect(() => {
    const element = elementRef.current
    if (!element) return undefined
    const listeners = (Object.entries(EVENT_PROPS) as [EventProp, string][]).map(([prop, event]) => {
      const listener = (e: Event) => (callbacks.current[prop] as ((detail: unknown) => void) | undefined)?.((e as CustomEvent).detail)
      element.addEventListener(event, listener)
      return () => element.removeEventListener(event, listener)
    })
    return () => listeners.forEach((remove) => remove())
  }, [])

  useImperativeHandle(ref, () => ({
    get element() {
      return elementRef.current
    },
    getXml: async () => elementRef.current?.getXml?.(),
    getSvg: async () => elementRef.current?.getSvg?.(),
    select: (elementId: string) => elementRef.current?.select?.(elementId),
  }))

  return createElement(ELEMENT_NAME, { ref: elementRef, class: props.className, className: props.className, style: props.style })
})
