/**
 * @flowaudit/bpmn-react – React wrapper around `<flowaudit-bpmn-editor>`
 * (MIT). Importing this module registers the web component.
 */

import '@flowaudit/bpmn-vue/web-component'

export { FlowauditBpmnEditor, type EditorPorts, type FlowauditBpmnEditorHandle, type FlowauditBpmnEditorProps } from './FlowauditBpmnEditor'
export { ATTRIBUTE_PROPS, ELEMENT_NAME, EVENT_PROPS } from './contract'
