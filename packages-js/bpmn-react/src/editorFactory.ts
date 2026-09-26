/**
 * Default editor factory of the React UI: the core `BpmnEditor` with the
 * FlowAudit layer (`createEditorFactory` of the framework-free UI core).
 */

import { BpmnEditor } from '@auditcore/bpmn-editor'
import { createEditorFactory, type EditorFactory } from '@auditcore/bpmn-flowaudit/ui'

export const defaultEditorFactory: EditorFactory = createEditorFactory(BpmnEditor as never)
