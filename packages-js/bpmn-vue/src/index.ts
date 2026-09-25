/**
 * @flowaudit/bpmn-vue – Vue 3 UI for the FlowAudit BPMN editor (MIT).
 */

import './styles/theme.css'

export { default as FlowauditEditor } from './components/FlowauditEditor.vue'
export { default as FlowauditWorkbench } from './components/FlowauditWorkbench.vue'
export { default as CollectionTree } from './components/collection/CollectionTree.vue'
export { default as GroupOverview } from './components/collection/GroupOverview.vue'
export { default as DiagramInfoColumn } from './components/collection/DiagramInfoColumn.vue'
export { default as PropertiesPanel } from './panels/PropertiesPanel.vue'
export { default as LegalBasisEditor } from './panels/legal/LegalBasisEditor.vue'
export { default as IssueList } from './components/views/IssueList.vue'
export { default as FaIcon } from './components/base/FaIcon.vue'
export { default as BaseDialog } from './components/base/BaseDialog.vue'

export { createEditorStore, type EditorStore } from './stores/editorStore'
export { createSelectionStore, type SelectionStore } from './stores/selectionStore'
export { createValidationStore, type ValidationStore } from './stores/validationStore'
export { createCollectionStore, type CollectionStore } from './stores/collectionStore'
export { provideEditorContext, useEditorContext, type EditorContext, type EditorPorts } from './stores/context'
export { createI18n, provideI18n, useI18n, type I18n, type Locale } from './i18n/useI18n'
export { MESSAGES_DE } from './i18n/messages.de'
export { MESSAGES_EN } from './i18n/messages.en'
export { defaultEditorFactory, type EditorFactory, type EditorLike, type CreateEditorOptions } from './editor/createEditor'
export { LISTS, type FieldDescriptor, type ListDescriptor } from './panels/descriptors'
export { TABS, type TabDefinition } from './panels/tabs'
export type { CompareSource } from './components/views/compareSource'
export type { ToolbarAction } from './components/toolbar/toolbarActions'
export { RestStorage, RestLegalSearch, RestCatalogue, RestProfiles, RestValidation, RestEsi, restPorts, type RestOptions } from './rest/restPorts'
