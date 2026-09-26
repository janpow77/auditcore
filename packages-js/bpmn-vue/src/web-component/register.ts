/**
 * Web component `<flowaudit-bpmn-editor>` (Vue custom element in light DOM,
 * so the editor styles and diagram-js work unchanged). Importing this module
 * registers the element once.
 */

import { defineCustomElement } from 'vue'
import FlowauditBpmnElement from './FlowauditBpmnElement.vue'
import { ELEMENT_NAME } from '@auditcore/bpmn-flowaudit/ui'
import '@auditcore/bpmn-flowaudit/ui.css'

export const FlowauditBpmnEditorElement = defineCustomElement(FlowauditBpmnElement, { shadowRoot: false })

export function registerFlowauditBpmnEditor(name: string = ELEMENT_NAME): void {
  if (typeof customElements !== 'undefined' && !customElements.get(name)) customElements.define(name, FlowauditBpmnEditorElement)
}

registerFlowauditBpmnEditor()

export { ELEMENT_ATTRIBUTES, ELEMENT_EVENTS, ELEMENT_NAME, type ElementEventMap, type ElementEventName, type ElementObjectProperties, type Theme } from '@auditcore/bpmn-flowaudit/ui'
