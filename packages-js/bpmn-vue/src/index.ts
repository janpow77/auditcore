/**
 * @flowaudit/bpmn-vue – Vue 3 UI for the FlowAudit BPMN editor (MIT). The
 * logic lives in the framework-free core `@flowaudit/bpmn-flowaudit/ui`,
 * shared with `@flowaudit/bpmn-react`.
 */

import '@flowaudit/bpmn-flowaudit/ui.css'

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

export { createEditorStore, bindEditorCore, type EditorStore } from './stores/editorStore'
export { createSelectionStore, bindSelectionCore, type SelectionStore } from './stores/selectionStore'
export { createValidationStore, bindValidationCore, type ValidationStore } from './stores/validationStore'
export { createCollectionStore, type CollectionStore } from './stores/collectionStore'
export { provideEditorContext, useEditorContext, type EditorContext, type EditorPorts } from './stores/context'
export { createI18n, provideI18n, useI18n, type I18n, type Locale } from './i18n/useI18n'
export { useStore } from './composables/useStore'
export { defaultEditorFactory, type EditorFactory, type EditorLike, type CreateEditorOptions } from './editor/defaultFactory'
export { MESSAGES_DE, MESSAGES_EN, LISTS, TABS, RestStorage, RestLegalSearch, RestCatalogue, RestProfiles, RestValidation, RestEsi, restPorts } from '@flowaudit/bpmn-flowaudit/ui'
export type { FieldDescriptor, ListDescriptor, TabDefinition, CompareSource, ToolbarAction, RestOptions } from '@flowaudit/bpmn-flowaudit/ui'
