/**
 * Collection controller: folders, tags and diagrams of a `DiagramCollection`,
 * persisted through the storage port (no database in the library). The
 * collection object is changed in place; `revision` announces each change.
 */

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
} from '../index'
import { createStore, type Store } from './store'

export interface CollectionFilter {
  search: string
  status: string
  tag: string
}

export interface CollectionState {
  collection: DiagramCollection
  revision: number
  filter: CollectionFilter
  selectedFolder: string | null
  loading: boolean
  error: string | null
}

export type CollectionCore = ReturnType<typeof createCollectionCore>

async function modelOf(xml: string) {
  return modelFromDefinitions((await loadDefinitions(xml)).definitions)
}

function filteredTree(collection: DiagramCollection, visible: Set<string>, filtering: boolean, node: FolderNode = collection.tree()): FolderNode {
  const subfolders = node.subfolders.map((child) => filteredTree(collection, visible, filtering, child)).filter((child) => child.diagrams.length || child.subfolders.length || !filtering)
  return { folder: node.folder, subfolders, diagrams: node.diagrams.filter((entry) => visible.has(entry.id)) }
}

/** Filtered folder tree of the collection (empty folders hidden while filtering). */
export function collectionTree(collection: DiagramCollection, filter: CollectionFilter): FolderNode {
  const hits = collection.search(filter.search, { status: filter.status || undefined, tag: filter.tag || undefined })
  return filteredTree(collection, new Set(hits.map((entry) => entry.id)), isFiltering(filter))
}

export const isFiltering = (filter: CollectionFilter): boolean => Boolean(filter.search || filter.status || filter.tag)
export const collectionOverview = (collection: DiagramCollection, folderId: string | null) => groupOverview(collection, { folderId })
export const collectionIssues = (collection: DiagramCollection) => checkCollection(collection)

type Guard = <T>(action: () => Promise<T>) => Promise<T | undefined>

/** Persisting changes to folders, diagrams, tags and approvals. */
function collectionActions(store: Store<CollectionState>, storage: StoragePort, persist: () => Promise<void>, guarded: Guard) {
  const current = () => store.get().collection
  const takenIds = () => new Set([...current().diagrams.keys(), ...current().folders.keys(), ...current().tags.keys()])
  const mutate = (change: (c: DiagramCollection) => void) => guarded(async () => (change(current()), await persist()))

  const createFolder = (name: string, parentId: string | null = null) =>
    guarded(async () => {
      const folder = current().createFolder(idFromName(name, takenIds()), name, parentId)
      await persist()
      return folder
    })

  const createDiagram = (name: string, folderId: string | null = null, xml = EMPTY_DIAGRAM) =>
    guarded(async () => {
      const id = idFromName(name, takenIds())
      await storage.saveDiagram(id, xml)
      current().addDiagram(id, { name, folderId, model: await modelOf(xml) })
      current().rename(id, name)
      await persist()
      return id
    })

  const saveDiagram = (id: string, xml: string) =>
    guarded(async () => {
      await storage.saveDiagram(id, xml)
      current().update(id, await modelOf(xml))
      await persist()
    })

  const removeDiagram = (id: string) =>
    guarded(async () => {
      await storage.deleteDiagram(id)
      current().remove(id)
      await persist()
    })

  const approveDiagram = (id: string, xml: string, version: string, meta: { approvedBy?: string; approvedOn?: string; cutoffDate?: string }) =>
    guarded(async () => {
      const approval = await approve(current(), id, xml, version, meta)
      await storage.saveApproval?.(id, version, xml)
      await persist()
      return approval
    })

  return {
    createFolder,
    createDiagram,
    saveDiagram,
    removeDiagram,
    approveDiagram,
    renameFolder: (id: string, name: string) => mutate((c) => c.renameFolder(id, name)),
    removeFolder: (id: string) => mutate((c) => c.removeFolder(id)),
    moveFolder: (id: string, parentId: string | null, position?: number) => mutate((c) => c.moveFolder(id, parentId, position)),
    moveDiagram: (id: string, folderId: string | null, position?: number) => mutate((c) => c.move(id, folderId, position)),
    renameDiagram: (id: string, name: string) => mutate((c) => c.rename(id, name)),
    setTags: (id: string, tags: string[]) => mutate((c) => c.setTags(id, tags)),
    createTag: (name: string, color?: string) => mutate((c) => c.createTag(idFromName(name, takenIds()), name, color)),
  }
}

export function createCollectionCore(storage: StoragePort) {
  const store = createStore<CollectionState>({ collection: new DiagramCollection(), revision: 0, filter: { search: '', status: '', tag: '' }, selectedFolder: null, loading: false, error: null })
  const touch = () => store.set((state) => ({ revision: state.revision + 1 }))

  async function persist(): Promise<void> {
    await storage.saveCollection(store.get().collection.toData())
    touch()
  }

  async function guarded<T>(action: () => Promise<T>): Promise<T | undefined> {
    store.set({ error: null })
    try {
      return await action()
    } catch (caught) {
      store.set({ error: (caught as Error).message })
      return undefined
    }
  }

  async function load(): Promise<void> {
    store.set({ loading: true })
    await guarded(async () => {
      const data = await storage.loadCollection()
      store.set((state) => ({ collection: data ? DiagramCollection.fromData(data) : new DiagramCollection(), revision: state.revision + 1 }))
    })
    store.set({ loading: false })
  }

  return {
    store,
    load,
    ...collectionActions(store, storage, persist, guarded),
    openDiagram: (id: string) => storage.loadDiagram(id),
    setFilter: (patch: Partial<CollectionFilter>) => store.set((state) => ({ filter: { ...state.filter, ...patch } })),
    selectFolder: (id: string | null) => store.set({ selectedFolder: id }),
    entry: (id: string): DiagramEntry | undefined => store.get().collection.diagrams.get(id),
  }
}
