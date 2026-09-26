/**
 * Mapping of the React props of `FlowauditBpmnEditor` to the attributes and
 * events of the web component `<flowaudit-bpmn-editor>` (the contract both
 * implementations share; see `ELEMENT_ATTRIBUTES`/`ELEMENT_EVENTS` of the core).
 */

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

export const EVENT_PROPS = {
  onReady: 'ready',
  onChange: 'change',
  onSave: 'save',
  onSelectionChange: 'selection-change',
  onDiagramInfoChange: 'diagram-info-change',
  onError: 'error',
} as const
