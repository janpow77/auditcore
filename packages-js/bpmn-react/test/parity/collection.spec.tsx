import { act } from '@testing-library/react'
import { flushPromises } from '@vue/test-utils'
import { describe, it } from 'vitest'
import { InMemoryStorage } from '@flowaudit/bpmn-flowaudit'
import { createCollectionCore, type CollectionCore } from '@flowaudit/bpmn-flowaudit/ui'
import VueCollectionTree from '../../../bpmn-vue/src/components/collection/CollectionTree.vue'
import VueDiagramInfoColumn from '../../../bpmn-vue/src/components/collection/DiagramInfoColumn.vue'
import VueGroupOverview from '../../../bpmn-vue/src/components/collection/GroupOverview.vue'
import { createCollectionStore } from '../../../bpmn-vue/src/stores/collectionStore'
import { bundledProfiles } from '@flowaudit/bpmn-flowaudit/profiles'
import { fillCollection, INFO_EXPECT, OVERVIEW_EXPECT, TREE_CASES } from '../../../bpmn-flowaudit/test/parity/cases-collection'
import { CollectionTree } from '../../src/collection/CollectionTree'
import { DiagramInfoColumn } from '../../src/collection/DiagramInfoColumn'
import { GroupOverview } from '../../src/collection/GroupOverview'
import { useCollectionBinding } from '../../src/useCollection'
import { flush } from '../helpers'
import { expectParity, renderBoth } from './setup'

async function both() {
  const vue = createCollectionStore(new InMemoryStorage())
  const react = createCollectionCore(new InMemoryStorage())
  const folderId = await fillCollection(vue)
  await fillCollection(react)
  return { vue, react, folderId }
}

function Tree({ core, selected = 'bewilligung' }: { core: CollectionCore; selected?: string | null }) {
  return <CollectionTree store={useCollectionBinding(core)} selectedDiagram={selected} openDiagram={null} />
}

function Info({ core }: { core: CollectionCore }) {
  const store = useCollectionBinding(core)
  const entry = store.entry('bewilligung')
  return entry ? <DiagramInfoColumn store={store} entry={entry} /> : null
}

function Overview({ core }: { core: CollectionCore }) {
  const store = useCollectionBinding(core)
  return <GroupOverview overview={store.overview} profile={bundledProfiles()[0] ?? null} issues={store.issues} title="Oberste Ebene" />
}

describe('collection parity (Vue ↔ React)', () => {
  for (const testCase of TREE_CASES) {
    it(`CollectionTree: ${testCase.name}`, async () => {
      const { vue, react, folderId } = await both()
      vue.setFilter(testCase.filter)
      react.setFilter(testCase.filter)
      if (testCase.selectFolder) {
        vue.selectFolder(folderId)
        react.selectFolder(folderId)
      }
      const rendered = await renderBoth(VueCollectionTree, { store: vue, selectedDiagram: 'bewilligung', openDiagram: null }, <Tree core={react} />)
      expectParity(rendered, testCase.expect)
    })
  }

  it('CollectionTree: same DOM after changing filter and folder on both sides', async () => {
    const { vue, react, folderId } = await both()
    const rendered = await renderBoth(VueCollectionTree, { store: vue, selectedDiagram: null, openDiagram: null }, <Tree core={react} selected={null} />)
    vue.setFilter({ search: 'bewill' })
    vue.selectFolder(folderId)
    act(() => {
      react.setFilter({ search: 'bewill' })
      react.selectFolder(folderId)
    })
    await flushPromises()
    await flush()
    expectParity(rendered, { texts: ['Bewilligung'], counts: { '.fa-tree__name': 1 } })
  })

  it('GroupOverview', async () => {
    const { vue, react } = await both()
    const rendered = await renderBoth(VueGroupOverview, { overview: vue.overview.value, profile: bundledProfiles()[0] ?? null, issues: vue.issues.value, title: 'Oberste Ebene' }, <Overview core={react} />)
    expectParity(rendered, OVERVIEW_EXPECT)
  })

  it('DiagramInfoColumn', async () => {
    const { vue, react } = await both()
    const rendered = await renderBoth(VueDiagramInfoColumn, { store: vue, entry: vue.entry('bewilligung') }, <Info core={react} />)
    expectParity(rendered, INFO_EXPECT)
  })
})
