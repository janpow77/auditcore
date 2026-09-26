/**
 * Default editor factory of the Vue UI: the core `BpmnEditor` with the
 * FlowAudit layer (`createEditorFactory` of the framework-free UI core).
 */

import { BpmnEditor } from '@flowaudit/bpmn-editor'
import { createEditorFactory, type EditorFactory } from '@flowaudit/bpmn-flowaudit/ui'

export const defaultEditorFactory: EditorFactory = createEditorFactory(BpmnEditor as never)

export type { CreateEditorOptions, EditorFactory, EditorLike } from '@flowaudit/bpmn-flowaudit/ui'
