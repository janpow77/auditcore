import { afterEach, describe, expect, it, vi } from 'vitest'
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react'
import { InMemoryStorage } from '@auditcore/bpmn-flowaudit'
import { createCollectionCore, OVERVIEW_VIEW_KEY, PROPERTIES_PANEL } from '@auditcore/bpmn-flowaudit/ui'
import { PanelResizer } from '../src/base/PanelResizer'
import { GroupOverview } from '../src/collection/GroupOverview'
import { I18nProvider } from '../src/i18n'
import { useCollectionBinding } from '../src/useCollection'
import { fixture } from './helpers'

afterEach(() => {
  cleanup()
  localStorage.clear()
})

describe('PanelResizer', () => {
  it('resizes with arrows, Home/End, double click and the pointer; collapses to a rail', () => {
    const onWidthChange = vi.fn()
    const onOpenChange = vi.fn()
    const props = { width: 420, bounds: PROPERTIES_PANEL, edge: 'right' as const, name: 'Eigenschaften', onWidthChange, onOpenChange }
    const { rerender } = render(<I18nProvider locale="de"><PanelResizer {...props} open /></I18nProvider>)
    const handle = screen.getByRole('separator')
    fireEvent.keyDown(handle, { key: 'ArrowLeft' })
    fireEvent.keyDown(handle, { key: 'End' })
    fireEvent.doubleClick(handle)
    fireEvent.pointerDown(handle, { button: 0, clientX: 1000, pointerId: 1 })
    fireEvent.pointerMove(handle, { clientX: 900, pointerId: 1 })
    fireEvent.pointerUp(handle, { pointerId: 1 })
    expect(onWidthChange.mock.calls.map(([width]) => width)).toEqual([444, PROPERTIES_PANEL.max, PROPERTIES_PANEL.initial, 520])
    fireEvent.click(screen.getByRole('button', { name: '„Eigenschaften“ ausblenden' }))
    expect(onOpenChange).toHaveBeenLastCalledWith(false)
    rerender(<I18nProvider locale="de"><PanelResizer {...props} open={false} /></I18nProvider>)
    expect(screen.queryByRole('separator')).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: '„Eigenschaften“ einblenden' }))
    expect(onOpenChange).toHaveBeenLastCalledWith(true)
  })
})

describe('GroupOverview layouts', () => {
  it('gives a folder with many diagrams the whole row and switches to the list, kept per browser', async () => {
    const core = createCollectionCore(new InMemoryStorage())
    await core.load()
    const folder = await core.createFolder('Systemprüfungen')
    for (const name of ['S01', 'S02', 'S03', 'S04']) await core.createDiagram(name, folder!.id, fixture('enrichment.bpmn'))
    function Overview() {
      const store = useCollectionBinding(core)
      return <GroupOverview overview={store.overview} issues={[]} title="Oberste Ebene" cards={store.cards} />
    }
    const { container } = render(<I18nProvider locale="de"><Overview /></I18nProvider>)
    expect(container.querySelector('.fa-folder-card--wide')).not.toBeNull()
    fireEvent.click(screen.getByRole('button', { name: 'Ansicht der Übersicht' }))
    expect(screen.getAllByRole('menuitemradio').map((option) => option.textContent)).toEqual(['Kacheln', 'Liste'])
    act(() => void fireEvent.click(screen.getByRole('menuitemradio', { name: 'Liste' })))
    expect(container.querySelectorAll('.fa-diagram-list__row')).toHaveLength(5)
    expect(localStorage.getItem(OVERVIEW_VIEW_KEY)).toBe('list')
  })
})
