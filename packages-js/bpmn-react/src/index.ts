/**
 * @auditcore/bpmn-react – native React UI of the FlowAudit BPMN editor (MIT):
 * no Vue runtime, no web components. The logic comes from the framework-free
 * core `@auditcore/bpmn-flowaudit/ui`, shared with `@auditcore/bpmn-vue`.
 */

import '@auditcore/bpmn-flowaudit/ui.css'

export { FlowauditEditor } from './FlowauditEditor'
export type { FlowauditEditorHandle, FlowauditEditorProps } from './editorProps'
export { FlowauditBpmnEditor, type FlowauditBpmnEditorHandle, type FlowauditBpmnEditorProps } from './element/FlowauditBpmnEditor'
export { FlowauditWorkbench } from './FlowauditWorkbench'
export { CollectionTree } from './collection/CollectionTree'
export { GroupOverview } from './collection/GroupOverview'
export { DiagramInfoColumn } from './collection/DiagramInfoColumn'
export { PropertiesPanel } from './panels/PropertiesPanel'
export { LegalBasisEditor } from './panels/legal/LegalBasisEditor'
export { IssueList } from './views/IssueList'
export { FaIcon } from './base/FaIcon'
export { BaseDialog } from './base/BaseDialog'
export { EditorContextProvider, useEditorContext, useEditorState, useSelectionState, useValidationView, type EditorContext } from './context'
export { createI18n, I18nProvider, useI18n, type I18n } from './i18n'
export { useStoreState, useElementId } from './hooks'
export { useEditorSession, type EditorRuntime } from './useEditorSession'
export { useCollection, useCollectionBinding, type CollectionBinding } from './useCollection'
export { defaultEditorFactory } from './editorFactory'
export { ATTRIBUTE_PROPS, EVENT_PROPS } from './element/contract'
export { MESSAGES_DE, MESSAGES_EN, LISTS, TABS, RestStorage, RestLegalSearch, RestCatalogue, RestProfiles, RestValidation, RestEsi, restPorts } from '@auditcore/bpmn-flowaudit/ui'
export type { CompareSource, CreateEditorOptions, EditorFactory, EditorLike, EditorPorts, FieldDescriptor, ListDescriptor, Locale, RestOptions, TabDefinition, ToolbarAction } from '@auditcore/bpmn-flowaudit/ui'
