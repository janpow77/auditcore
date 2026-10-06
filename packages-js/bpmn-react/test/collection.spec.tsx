import { act, cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { InMemoryStorage } from '@auditcore/bpmn-flowaudit'
import { createCollectionCore, DIAGRAM_MIME, type CollectionCore } from '@auditcore/bpmn-flowaudit/ui'
import { fillCollection } from '../../bpmn-flowaudit/test/parity/cases-collection'
import { CollectionTree } from '../src/collection/CollectionTree'
import { GroupOverview } from '../src/collection/GroupOverview'
import { FlowauditWorkbench } from '../src/FlowauditWorkbench'
import { useCollectionBinding } from '../src/useCollection'
import { fixture, flush, until } from './helpers'

afterEach(cleanup)

async function filled() {
  const storage = new InMemoryStorage()
  const core = createCollectionCore(storage)
  const folderId = await fillCollection(core)
  return { storage, core, folderId }
}

function Tree({ core, onSelect, onOpen }: { core: CollectionCore; onSelect?: (id: string | null) => void; onOpen?: (id: string) => void }) {
  return <CollectionTree store={useCollectionBinding(core)} selectedDiagram={null} openDiagram={null} onSelectDiagram={onSelect} onOpenDiagram={onOpen} />
}

const label = (text: string) => screen.getAllByRole('button').find((item) => item.classList.contains('fa-tree__label') && item.textContent?.includes(text)) as HTMLElement

describe('collection controller', () => {
  it('persists through the storage port, filters, moves and tags', async () => {
    const { storage, core, folderId } = await filled()
    expect((await storage.loadCollection())?.diagrams).toHaveLength(2)
    expect(core.entry('bewilligung')?.folderId).toBe(folderId)
    await core.moveDiagram('anreicherung', folderId, 0)
    expect(core.store.get().collection.inFolder(folderId).map((d) => d.id)).toEqual(['anreicherung', 'bewilligung'])
    expect(core.entry('anreicherung')?.tags).toEqual(['kern'])
    await core.removeDiagram('anreicherung')
    await expect(storage.loadDiagram('anreicherung')).rejects.toThrow()
  })

  it('reports errors instead of throwing', async () => {
    const { core } = await filled()
    const xml = await core.openDiagram('bewilligung')
    expect((await core.approveDiagram('bewilligung', xml, '2.0', {}))?.sha256).toMatch(/^[0-9a-f]{64}$/)
    expect(await core.approveDiagram('bewilligung', `${xml} `, '2.0', {})).toBeUndefined()
    expect(core.store.get().error).toContain('bereits freigegeben')
  })
})

function Overview({ core }: { core: CollectionCore }) {
  const store = useCollectionBinding(core)
  return (
    <GroupOverview
      overview={store.overview}
      issues={store.issues}
      title="Oberste Ebene"
      cards={store.cards}
      onDescribeFolder={(id, text) => void store.describeFolder(id, text)}
      onDescribeDiagram={(id, text) => void store.describeDiagram(id, text)}
    />
  )
}

describe('GroupOverview (React)', () => {
  it('offers host folder actions in a small menu per folder card', async () => {
    const core = createCollectionCore(new InMemoryStorage())
    const folderId = await fillCollection(core)
    const onFolderAction = vi.fn()
    function WithActions() {
      const store = useCollectionBinding(core)
      return <GroupOverview overview={store.overview} issues={[]} title="Oberste Ebene" cards={store.cards} folderActions={[{ id: 'matrix', label: 'Kontrollmatrix erzeugen' }]} onFolderAction={onFolderAction} />
    }
    const { container } = render(<WithActions />)
    const menus = container.querySelectorAll('.fa-folder-card .fa-toolbar-menu')
    expect(menus).toHaveLength(1)
    fireEvent.click(menus[0]!.querySelector('button')!)
    fireEvent.click(container.querySelector('[role="menuitem"]')!)
    expect(onFolderAction).toHaveBeenCalledWith('matrix', folderId, ['bewilligung'])
  })

  it('shows folder cards, edits descriptions inline and keeps the hints collapsed', async () => {
    const storage = new InMemoryStorage()
    const core = createCollectionCore(storage)
    const folderId = await fillCollection(core)
    const { container } = render(<Overview core={core} />)
    expect(Array.from(container.querySelectorAll('.fa-folder-card h3')).map((node) => node.textContent)).toEqual(['Antragsverfahren', 'Ohne Ordner'])
    expect(container.querySelector('.fa-overview__ka-cell')).toBeNull()
    expect(container.querySelector('details.fa-overview__hints')!.hasAttribute('open')).toBe(false)
    fireEvent.click(container.querySelector('.fa-folder-card .fa-describe')!)
    const field = container.querySelector('textarea')!
    fireEvent.change(field, { target: { value: 'Bewilligungsverfahren' } })
    fireEvent.keyDown(field, { key: 'Enter' })
    await until(async () => (await storage.loadCollection())?.folders[0]?.description === 'Bewilligungsverfahren')
    await flush()
    expect(core.store.get().collection.folders.get(folderId)?.description).toBe('Bewilligungsverfahren')
    expect(container.querySelector('.fa-folder-card .fa-describe')!.textContent).toBe('Bewilligungsverfahren')
  })
})

describe('CollectionTree (React)', () => {
  it('shows an ARIA tree, filters and creates folders through the prompt', async () => {
    const { core } = await filled()
    render(<Tree core={core} />)
    const tree = screen.getByRole('tree')
    expect(tree.textContent).toContain('Antragsverfahren')
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'anreich' } })
    expect(within(tree).queryByText('Bewilligung')).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: 'Neuer Ordner' }))
    fireEvent.change(within(screen.getByRole('dialog')).getByRole('textbox'), { target: { value: 'Prüfverfahren' } })
    fireEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Übernehmen' }))
    await until(() => [...core.store.get().collection.folders.values()].some((f) => f.name === 'Prüfverfahren'))
  })

  it('selects and opens diagrams and moves them by drag and drop', async () => {
    const { core, folderId } = await filled()
    const onSelect = vi.fn()
    const onOpen = vi.fn()
    render(<Tree core={core} onSelect={onSelect} onOpen={onOpen} />)
    fireEvent.click(label('Anreicherung'))
    fireEvent.doubleClick(label('Anreicherung'))
    expect(onSelect).toHaveBeenLastCalledWith('anreicherung')
    expect(onOpen).toHaveBeenCalledWith('anreicherung')
    const data = new Map([[DIAGRAM_MIME, 'anreicherung']])
    const dataTransfer = { getData: (key: string) => data.get(key) ?? '', setData: () => undefined }
    await act(async () => {
      fireEvent.drop(label('Antragsverfahren').closest('.fa-tree__row') as HTMLElement, { dataTransfer })
    })
    await until(() => core.entry('anreicherung')?.folderId === folderId)
  })
})

describe('FlowauditWorkbench (React)', () => {
  it('lists the collection, opens a diagram in the editor and saves it back', async () => {
    const storage = new InMemoryStorage()
    await fillCollection(createCollectionCore(storage))
    const onOpen = vi.fn()
    const { container } = render(<FlowauditWorkbench storage={storage} onOpen={onOpen} />)
    await until(() => container.textContent?.includes('Anreicherung') ?? false)
    expect(container.querySelector('.fa-overview')).not.toBeNull()
    fireEvent.doubleClick(label('Anreicherung'))
    await until(() => container.querySelector('.fa-editor .djs-container') !== null)
    expect(onOpen).toHaveBeenCalledWith('anreicherung')
    const saveDiagram = vi.spyOn(storage, 'saveDiagram')
    fireEvent.keyDown(container.querySelector('.fa-editor') as HTMLElement, { key: 's', ctrlKey: true })
    await until(() => saveDiagram.mock.calls.length > 0)
    expect(saveDiagram.mock.calls[0]?.[0]).toBe('anreicherung')
    expect(await storage.loadDiagram('anreicherung')).toContain('bpmn:definitions')
    await flush()
  })

  it('uses the fixtures of the Vue tests', () => {
    expect(fixture('schema-1.1.bpmn')).toContain('bpmn:definitions')
  })
})
