/**
 * Collection store: folders, tags and diagrams of a `DiagramCollection`,
 * persisted through the storage port (no database in the library).
 */

import { computed, reactive, ref, shallowRef, triggerRef } from 'vue'
import {
  approve,
  checkCollection,
  DiagramCollection,
  EMPTY_DIAGRAM,
  groupOverview,
  idFromName,
  loadDefinitions,
  modelFromDefinitions,
  type DiagramEntry,
  type FolderNode,
  type StoragePort,
} from '@flowaudit/bpmn-flowaudit'

export interface CollectionFilter {
  search: string
  status: string
  tag: string
}

export type CollectionStore = ReturnType<typeof createCollectionStore>

async function modelOf(xml: string) {
  return modelFromDefinitions((await loadDefinitions(xml)).definitions)
}

export function createCollectionStore(storage: StoragePort) {
  const collection = shallowRef(new DiagramCollection())
  const filter = reactive<CollectionFilter>({ search: '', status: '', tag: '' })
  const selectedFolder = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const touch = () => triggerRef(collection)

  async function persist(): Promise<void> {
    await storage.saveCollection(collection.value.toData())
    touch()
  }

  async function guarded<T>(action: () => Promise<T>): Promise<T | undefined> {
    error.value = null
    try {
      return await action()
    } catch (caught) {
      error.value = (caught as Error).message
      return undefined
    }
  }

  async function load(): Promise<void> {
    loading.value = true
    await guarded(async () => {
      const data = await storage.loadCollection()
      collection.value = data ? DiagramCollection.fromData(data) : new DiagramCollection()
    })
    loading.value = false
  }

  const takenIds = () => new Set([...collection.value.diagrams.keys(), ...collection.value.folders.keys(), ...collection.value.tags.keys()])

  const createFolder = (name: string, parentId: string | null = null) =>
    guarded(async () => {
      const folder = collection.value.createFolder(idFromName(name, takenIds()), name, parentId)
      await persist()
      return folder
    })

  const createDiagram = (name: string, folderId: string | null = null, xml = EMPTY_DIAGRAM) =>
    guarded(async () => {
      const id = idFromName(name, takenIds())
      await storage.saveDiagram(id, xml)
      collection.value.addDiagram(id, { name, folderId, model: await modelOf(xml) })
      collection.value.rename(id, name)
      await persist()
      return id
    })

  const saveDiagram = (id: string, xml: string) =>
    guarded(async () => {
      await storage.saveDiagram(id, xml)
      collection.value.update(id, await modelOf(xml))
      await persist()
    })

  const mutate = (change: (c: DiagramCollection) => void) =>
    guarded(async () => {
      change(collection.value)
      await persist()
    })

  const removeDiagram = (id: string) =>
    guarded(async () => {
      await storage.deleteDiagram(id)
      collection.value.remove(id)
      await persist()
    })

  const approveDiagram = (id: string, xml: string, version: string, meta: { approvedBy?: string; approvedOn?: string; cutoffDate?: string }) =>
    guarded(async () => {
      const approval = await approve(collection.value, id, xml, version, meta)
      await storage.saveApproval?.(id, version, xml)
      await persist()
      return approval
    })

  const visibleIds = computed(() => {
    void collection.value
    const hits = collection.value.search(filter.search, { status: filter.status || undefined, tag: filter.tag || undefined })
    return new Set(hits.map((entry) => entry.id))
  })

  function filteredTree(node: FolderNode = collection.value.tree()): FolderNode {
    const subfolders = node.subfolders.map((child) => filteredTree(child)).filter((child) => child.diagrams.length || child.subfolders.length || !isFiltering.value)
    return { folder: node.folder, subfolders, diagrams: node.diagrams.filter((entry) => visibleIds.value.has(entry.id)) }
  }

  const isFiltering = computed(() => Boolean(filter.search || filter.status || filter.tag))
  const tree = computed(() => filteredTree())
  const overview = computed(() => groupOverview(collection.value, { folderId: selectedFolder.value }))
  const issues = computed(() => checkCollection(collection.value))

  return {
    collection,
    filter,
    selectedFolder,
    loading,
    error,
    tree,
    overview,
    issues,
    isFiltering,
    load,
    createFolder,
    createDiagram,
    saveDiagram,
    removeDiagram,
    approveDiagram,
    openDiagram: (id: string) => storage.loadDiagram(id),
    entry: (id: string): DiagramEntry | undefined => collection.value.diagrams.get(id),
    renameFolder: (id: string, name: string) => mutate((c) => c.renameFolder(id, name)),
    removeFolder: (id: string) => mutate((c) => c.removeFolder(id)),
    moveFolder: (id: string, parentId: string | null, position?: number) => mutate((c) => c.moveFolder(id, parentId, position)),
    moveDiagram: (id: string, folderId: string | null, position?: number) => mutate((c) => c.move(id, folderId, position)),
    renameDiagram: (id: string, name: string) => mutate((c) => c.rename(id, name)),
    setTags: (id: string, tags: string[]) => mutate((c) => c.setTags(id, tags)),
    createTag: (name: string, color?: string) => mutate((c) => c.createTag(idFromName(name, takenIds()), name, color)),
  }
}
