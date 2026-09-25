import { afterEach, describe, expect, it } from 'vitest'
import { mount, type VueWrapper } from '@vue/test-utils'
import { InMemoryStorage } from '@flowaudit/bpmn-flowaudit'
import CollectionTree from '../src/components/collection/CollectionTree.vue'
import FlowauditWorkbench from '../src/components/FlowauditWorkbench.vue'
import { DIAGRAM_MIME, readDrag, setDrag } from '../src/components/collection/dragData'
import { createCollectionStore } from '../src/stores/collectionStore'
import { fixture, until } from './helpers'

let wrapper: VueWrapper | undefined
afterEach(() => {
  wrapper?.unmount()
  wrapper = undefined
})

async function filledStore() {
  const storage = new InMemoryStorage()
  const store = createCollectionStore(storage)
  await store.load()
  const folder = await store.createFolder('Antragsverfahren')
  await store.createDiagram('Bewilligung', folder!.id, fixture('schema-1.1.bpmn'))
  await store.createDiagram('Anreicherung', null, fixture('enrichment.bpmn'))
  return { storage, store, folderId: folder!.id }
}

describe('collection store', () => {
  it('creates folders and diagrams, persists through the storage port and filters', async () => {
    const { storage, store, folderId } = await filledStore()
    expect((await storage.loadCollection())?.diagrams).toHaveLength(2)
    expect(store.entry('bewilligung')?.folderId).toBe(folderId)
    store.filter.search = 'anreich'
    expect(store.tree.value.diagrams.map((d) => d.id)).toEqual(['anreicherung'])
    expect(store.tree.value.subfolders).toEqual([])
    store.filter.search = ''
    store.filter.status = 'freigegeben'
    expect(store.tree.value.subfolders[0].diagrams.map((d) => d.id)).toEqual(['bewilligung'])
  })

  it('moves, renames, tags and removes diagrams', async () => {
    const { storage, store, folderId } = await filledStore()
    await store.moveDiagram('anreicherung', folderId, 0)
    expect(store.collection.value.inFolder(folderId).map((d) => d.id)).toEqual(['anreicherung', 'bewilligung'])
    await store.renameDiagram('anreicherung', 'Anreicherung (Muster)')
    await store.createTag('Kern')
    await store.setTags('anreicherung', ['kern'])
    expect(store.entry('anreicherung')).toMatchObject({ name: 'Anreicherung (Muster)', tags: ['kern'] })
    await store.removeDiagram('anreicherung')
    await expect(storage.loadDiagram('anreicherung')).rejects.toThrow()
  })

  it('records approvals with hash and reports errors instead of throwing', async () => {
    const { store } = await filledStore()
    const xml = await store.openDiagram('bewilligung')
    const approval = await store.approveDiagram('bewilligung', xml, '2.0', { approvedBy: 'Referatsleitung' })
    expect(approval?.sha256).toMatch(/^[0-9a-f]{64}$/)
    expect(await store.approveDiagram('bewilligung', `${xml} `, '2.0', {})).toBeUndefined()
    expect(store.error.value).toContain('bereits freigegeben')
  })

  it('computes the group overview of the selected folder', async () => {
    const { store, folderId } = await filledStore()
    store.selectedFolder.value = folderId
    expect(store.overview.value.count).toBe(1)
    expect(store.overview.value.activities).toBeGreaterThan(0)
  })
})

describe('drag data', () => {
  it('writes and reads diagram and folder payloads', () => {
    const data = new Map<string, string>()
    const event = { dataTransfer: { setData: (k: string, v: string) => data.set(k, v), getData: (k: string) => data.get(k) ?? '', effectAllowed: '' } } as unknown as DragEvent
    setDrag(event, 'diagram', 'd1')
    expect(data.get(DIAGRAM_MIME)).toBe('d1')
    expect(readDrag(event)).toEqual({ kind: 'diagram', id: 'd1' })
  })
})

describe('CollectionTree', () => {
  it('shows folders and diagrams as an ARIA tree and creates folders through the prompt', async () => {
    const { store } = await filledStore()
    wrapper = mount(CollectionTree, { props: { store, selectedDiagram: null, openDiagram: null } })
    expect(wrapper.find('[role="tree"]').text()).toContain('Antragsverfahren')
    expect(wrapper.find('[role="tree"]').text()).toContain('Anreicherung')
    await wrapper.find('.fa-collection__head .fa-icon-btn').trigger('click')
    await wrapper.find('[role="dialog"] input').setValue('Prüfverfahren')
    await wrapper.find('[role="dialog"] .fa-btn--primary').trigger('click')
    await until(() => wrapper!.text().includes('Prüfverfahren'))
    expect([...store.collection.value.folders.values()].map((f) => f.name)).toContain('Prüfverfahren')
  })

  it('selects and opens diagrams', async () => {
    const { store } = await filledStore()
    wrapper = mount(CollectionTree, { props: { store, selectedDiagram: null, openDiagram: null } })
    const label = wrapper.findAll('.fa-tree__label').find((item) => item.text().includes('Anreicherung'))!
    await label.trigger('click')
    await label.trigger('dblclick')
    expect(wrapper.emitted<[string]>('select-diagram')!.at(-1)![0]).toBe('anreicherung')
    expect(wrapper.emitted<[string]>('open-diagram')![0][0]).toBe('anreicherung')
  })
})

describe('FlowauditWorkbench', () => {
  it('lists the collection, opens a diagram in the editor and saves it back', async () => {
    const { storage } = await filledStore()
    wrapper = mount(FlowauditWorkbench, { props: { storage }, attachTo: document.body })
    await until(() => wrapper!.text().includes('Anreicherung'))
    expect(wrapper.find('.fa-overview').exists()).toBe(true)
    const label = wrapper.findAll('.fa-tree__label').find((item) => item.text().includes('Anreicherung'))!
    await label.trigger('dblclick')
    await until(() => wrapper!.find('.fa-editor .djs-container').exists())
    expect(wrapper.emitted<[string]>('open')![0][0]).toBe('anreicherung')
    await wrapper.find('.fa-editor').trigger('keydown', { key: 's', ctrlKey: true })
    await until(async () => (await storage.loadDiagram('anreicherung')) !== fixture('enrichment.bpmn'))
    expect(await storage.loadDiagram('anreicherung')).toContain('bpmn:definitions')
  })
})
