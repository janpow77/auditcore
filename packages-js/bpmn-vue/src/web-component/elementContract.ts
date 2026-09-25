/**
 * Public contract of the web component `<flowaudit-bpmn-editor>`:
 * attributes, properties and events (documented in docs/bpmn/frontend.md;
 * the React wrapper uses the same table).
 */

import type { Comment, DiagramInfo, ProfileData, StoragePort } from '@flowaudit/bpmn-flowaudit'
import type { EditorPorts } from '../stores/context'

export const ELEMENT_NAME = 'flowaudit-bpmn-editor'

/** Attributes (strings) – mirrored as properties in camelCase. */
export const ELEMENT_ATTRIBUTES = ['src', 'api-base', 'diagram-id', 'name', 'locale', 'theme', 'readonly', 'profile', 'author'] as const

/** Events dispatched on the element (`CustomEvent.detail`). */
export interface ElementEventMap {
  ready: { diagramId?: string }
  change: { xml: string }
  save: { xml: string; info: DiagramInfo | null }
  'selection-change': { elementId: string | null }
  'diagram-info-change': { info: DiagramInfo | null }
  error: { message: string }
}

export type ElementEventName = keyof ElementEventMap

export const ELEMENT_EVENTS: ElementEventName[] = ['ready', 'change', 'save', 'selection-change', 'diagram-info-change', 'error']

/** Properties that take objects (set via JavaScript, not as attributes). */
export interface ElementObjectProperties {
  /** BPMN XML (instead of `src` or `diagram-id`). */
  xml?: string
  /** Storage port (JS callbacks) – alternative to `api-base`. */
  storage?: StoragePort
  /** Further ports (legal search, catalogue, validation, ESI). */
  ports?: EditorPorts
  /** Profile data (instead of loading `profile` from the server). */
  profileData?: ProfileData | null
  comments?: Comment[]
}

export type Theme = 'auto' | 'light' | 'dark'
