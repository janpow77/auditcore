/**
 * Web component `<flowaudit-bpmn-editor>` (Vue custom element in light DOM,
 * so the editor styles and diagram-js work unchanged). Importing this module
 * registers the element once.
 */

import { defineCustomElement } from 'vue'
import FlowauditBpmnElement from './FlowauditBpmnElement.vue'
import { ELEMENT_NAME } from './elementContract'
import '../styles/theme.css'

export const FlowauditBpmnEditorElement = defineCustomElement(FlowauditBpmnElement, { shadowRoot: false })

export function registerFlowauditBpmnEditor(name: string = ELEMENT_NAME): void {
  if (typeof customElements !== 'undefined' && !customElements.get(name)) customElements.define(name, FlowauditBpmnEditorElement)
}

registerFlowauditBpmnEditor()

export * from './elementContract'
