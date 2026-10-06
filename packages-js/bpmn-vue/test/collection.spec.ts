import { afterEach, describe, expect, it, vi } from 'vitest'
import { mount, type VueWrapper } from '@vue/test-utils'
import { InMemoryStorage } from '@auditcore/bpmn-flowaudit'
import CollectionTree from '../src/components/collection/CollectionTree.vue'
import GroupOverview from '../src/components/collection/GroupOverview.vue'
import FlowauditWorkbench from '../src/components/FlowauditWorkbench.vue'
import { DIAGRAM_MIME, readDrag, setDrag } from '@auditcore/bpmn-flowaudit/ui'
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
    expect(store.tree.value.subfolders[0]!.diagrams.map((d) => d.id)).toEqual(['bewilligung'])
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

describe('GroupOverview', () => {
  it('offers host folder actions in a small menu per folder card', async () => {
    const { store, folderId } = await filledStore()
    wrapper = mount(GroupOverview, { props: { overview: store.overview.value, issues: [], title: 'Oberste Ebene', cards: store.cards.value, folderActions: [{ id: 'matrix', label: 'Kontrollmatrix erzeugen' }] }, attachTo: document.body })
    const menus = wrapper.findAll('.fa-folder-card .fa-toolbar-menu')
    expect(menus).toHaveLength(1)
    await menus[0]!.find('button').trigger('click')
    await wrapper.find('[role="menuitem"]').trigger('click')
    expect(wrapper.emitted<[string, string, string[]]>('folder-action')![0]).toEqual(['matrix', folderId, ['bewilligung']])
    wrapper.unmount()
    wrapper = mount(GroupOverview, { props: { overview: store.overview.value, issues: [], title: 'Oberste Ebene', cards: store.cards.value } })
    expect(wrapper.find('.fa-folder-card .fa-toolbar-menu').exists()).toBe(false)
  })

  it('shows folder cards, edits descriptions inline and keeps the hints collapsed', async () => {
    const { storage, store, folderId } = await filledStore()
    wrapper = mount(GroupOverview, {
      props: { overview: store.overview.value, issues: store.issues.value, title: 'Oberste Ebene', cards: store.cards.value, 'onDescribeFolder': store.describeFolder, 'onDescribeDiagram': store.describeDiagram },
      attachTo: document.body,
    })
    expect(wrapper.findAll('.fa-folder-card').map((card) => card.find('h3').text())).toEqual(['Antragsverfahren', 'Ohne Ordner'])
    expect(wrapper.find('.fa-overview__ka-cell').exists()).toBe(false)
    expect(wrapper.find('details.fa-overview__hints').attributes('open')).toBeUndefined()
    expect(wrapper.find('summary').text()).toMatch(/^Prüfhinweise \(\d+\)$/)
    const folderText = wrapper.find('.fa-folder-card .fa-describe')
    expect(folderText.text()).toBe('Keine Beschreibung')
    await folderText.trigger('click')
    const field = wrapper.find('textarea')
    await field.setValue('Bewilligungsverfahren')
    await field.trigger('keydown', { key: 'Enter' })
    await until(async () => (await storage.loadCollection())?.folders[0]?.description === 'Bewilligungsverfahren')
    expect(store.collection.value.folders.get(folderId)?.description).toBe('Bewilligungsverfahren')
    await wrapper.findAll('.fa-describe')[1]!.trigger('click')
    await wrapper.find('textarea').setValue('verworfen')
    await wrapper.find('textarea').trigger('keydown', { key: 'Escape' })
    expect(wrapper.find('textarea').exists()).toBe(false)
    expect(store.entry('bewilligung')?.info?.description ?? '').not.toBe('verworfen')
    await wrapper.find('.fa-folder-card__open').trigger('click')
    expect(wrapper.emitted<[string]>('open')![0]![0]).toBe('bewilligung')
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
    expect(wrapper.emitted<[string]>('open-diagram')![0]![0]).toBe('anreicherung')
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
    expect(wrapper.emitted<[string]>('open')![0]![0]).toBe('anreicherung')
    const saveDiagram = vi.spyOn(storage, 'saveDiagram')
    await wrapper.find('.fa-editor').trigger('keydown', { key: 's', ctrlKey: true })
    await until(() => saveDiagram.mock.calls.length > 0)
    expect(saveDiagram.mock.calls[0]![0]).toBe('anreicherung')
    expect(await storage.loadDiagram('anreicherung')).toContain('bpmn:definitions')
  })
})
