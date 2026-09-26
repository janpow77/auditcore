/**
 * React binding of the collection controller (`createCollectionCore` of the
 * framework-free UI core): state via `useSyncExternalStore`, filtered tree,
 * group overview and collection issues derived per revision. Filter and
 * selected folder live in the core store (`setFilter`, `selectFolder`).
 */

import { useEffect, useMemo, useState } from 'react'
import { collectionIssues, collectionOverview, collectionTree, createCollectionCore, type CollectionCore, type CollectionState } from '@auditcore/bpmn-flowaudit/ui'
import type { StoragePort } from '@auditcore/bpmn-flowaudit'
import { useStoreState } from './hooks'

/** What the collection components (`CollectionTree`, `DiagramInfoColumn`) receive as `store`. */
export type CollectionBinding = CollectionCore & {
  state: CollectionState
  tree: ReturnType<typeof collectionTree>
  overview: ReturnType<typeof collectionOverview>
  issues: ReturnType<typeof collectionIssues>
}

/** Binds an existing controller (e.g. created and filled outside React). */
export function useCollectionBinding(core: CollectionCore): CollectionBinding {
  const state = useStoreState(core.store)
  const { collection, revision, filter, selectedFolder } = state
  // `revision` announces in-place changes of the collection object.
  const tree = useMemo(() => (void revision, collectionTree(collection, filter)), [collection, revision, filter])
  const overview = useMemo(() => (void revision, collectionOverview(collection, selectedFolder)), [collection, revision, selectedFolder])
  const issues = useMemo(() => (void revision, collectionIssues(collection)), [collection, revision])
  return useMemo(() => ({ ...core, state, tree, overview, issues }), [core, state, tree, overview, issues])
}

/** Creates a controller for the storage port, loads it once and binds it. */
export function useCollection(storage: StoragePort): CollectionBinding {
  const [core] = useState(() => createCollectionCore(storage))
  useEffect(() => {
    void core.load()
  }, [core])
  return useCollectionBinding(core)
}
