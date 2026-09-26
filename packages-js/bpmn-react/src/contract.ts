/**
 * Mapping of React props to the attributes and events of
 * `<flowaudit-bpmn-editor>` (see `@flowaudit/bpmn-vue/web-component`).
 */

export const ELEMENT_NAME = 'flowaudit-bpmn-editor'

export const ATTRIBUTE_PROPS = {
  src: 'src',
  apiBase: 'api-base',
  diagramId: 'diagram-id',
  name: 'name',
  locale: 'locale',
  theme: 'theme',
  readonly: 'readonly',
  profile: 'profile',
  author: 'author',
} as const

export type AttributeProp = keyof typeof ATTRIBUTE_PROPS

export const EVENT_PROPS = {
  onReady: 'ready',
  onChange: 'change',
  onSave: 'save',
  onSelectionChange: 'selection-change',
  onDiagramInfoChange: 'diagram-info-change',
  onError: 'error',
} as const

export type EventProp = keyof typeof EVENT_PROPS
