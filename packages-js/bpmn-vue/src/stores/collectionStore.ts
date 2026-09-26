/**
 * Collection store: folders, tags and diagrams of a `DiagramCollection`,
 * persisted through the storage port (framework-free
 * `createCollectionCore`; filter and selected folder stay Vue state so they
 * can be bound directly).
 */

import { computed, reactive, ref, shallowRef, triggerRef } from 'vue'
import { collectionIssues, collectionOverview, collectionTree, createCollectionCore, isFiltering, type CollectionFilter } from '@auditcore/bpmn-flowaudit/ui'
import type { StoragePort } from '@auditcore/bpmn-flowaudit'
import { useStore } from '../composables/useStore'

export type { CollectionFilter } from '@auditcore/bpmn-flowaudit/ui'
export type CollectionStore = ReturnType<typeof createCollectionStore>

export function createCollectionStore(storage: StoragePort) {
  const core = createCollectionCore(storage)
  const state = useStore(core.store)
  const collection = shallowRef(core.store.get().collection)
  core.store.subscribe(() => {
    collection.value = core.store.get().collection
    triggerRef(collection)
  })
  const filter = reactive<CollectionFilter>({ search: '', status: '', tag: '' })
  const selectedFolder = ref<string | null>(null)

  return {
    ...core,
    core,
    collection,
    filter,
    selectedFolder,
    loading: computed(() => state.value.loading),
    error: computed(() => state.value.error),
    tree: computed(() => collectionTree(collection.value, filter)),
    overview: computed(() => collectionOverview(collection.value, selectedFolder.value)),
    issues: computed(() => collectionIssues(collection.value)),
    isFiltering: computed(() => isFiltering(filter)),
    setFilter: (patch: Partial<CollectionFilter>) => Object.assign(filter, patch),
    selectFolder: (id: string | null) => (selectedFolder.value = id),
  }
}
