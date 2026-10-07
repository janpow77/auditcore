import { afterEach, describe, expect, it } from 'vitest'
import { mount, type VueWrapper } from '@vue/test-utils'
import { InMemoryStorage } from '@auditcore/bpmn-flowaudit'
import { OVERVIEW_VIEW_KEY, PROPERTIES_PANEL } from '@auditcore/bpmn-flowaudit/ui'
import PanelResizer from '../src/components/base/PanelResizer.vue'
import GroupOverview from '../src/components/collection/GroupOverview.vue'
import { createCollectionStore } from '../src/stores/collectionStore'
import { fixture } from './helpers'

let wrapper: VueWrapper | undefined
afterEach(() => {
  wrapper?.unmount()
  wrapper = undefined
  localStorage.clear()
})

describe('PanelResizer', () => {
  const props = { width: 420, open: true, bounds: PROPERTIES_PANEL, edge: 'right' as const, name: 'Eigenschaften' }

  it('resizes with arrows, Home/End and double click; drag uses the pointer', async () => {
    wrapper = mount(PanelResizer, { props })
    const handle = wrapper.get('[role="separator"]')
    await handle.trigger('keydown', { key: 'ArrowLeft' })
    await handle.trigger('keydown', { key: 'End' })
    await handle.trigger('dblclick')
    await handle.trigger('pointerdown', { button: 0, clientX: 1000, pointerId: 1 })
    await handle.trigger('pointermove', { clientX: 900, pointerId: 1 })
    await handle.trigger('pointerup', { pointerId: 1 })
    expect(wrapper.emitted('update:width')?.map(([width]) => width)).toEqual([444, PROPERTIES_PANEL.max, PROPERTIES_PANEL.initial, 520])
  })

  it('collapses with the button and shows a rail to expand', async () => {
    wrapper = mount(PanelResizer, { props })
    await wrapper.get('.fa-resizer__toggle').trigger('click')
    expect(wrapper.emitted('update:open')?.[0]).toEqual([false])
    await wrapper.setProps({ open: false })
    expect(wrapper.find('[role="separator"]').exists()).toBe(false)
    await wrapper.get('.fa-panel-rail__button').trigger('click')
    expect(wrapper.emitted('update:open')?.[1]).toEqual([true])
  })
})

describe('GroupOverview layouts', () => {
  async function overview(thumbnails: boolean) {
    const store = createCollectionStore(new InMemoryStorage())
    await store.load()
    const folder = await store.createFolder('Systemprüfungen')
    for (const name of ['S01 – Informationssicherheit', 'S02 – Zahlungsantrag', 'S03 – Auswahl der Vorhaben', 'S04 – Verwendungsnachweis']) {
      await store.createDiagram(name, folder!.id, fixture('enrichment.bpmn'))
    }
    const source = { get: async () => 'data:image/svg+xml,%3Csvg%2F%3E', invalidate: () => undefined, clear: () => undefined }
    return mount(GroupOverview, { props: { overview: store.overview.value, issues: [], title: 'Oberste Ebene', cards: store.cards.value, thumbnails: thumbnails ? source : null } })
  }

  it('gives a folder with many diagrams the whole row and switches to the list, kept per browser', async () => {
    wrapper = await overview(false)
    expect(wrapper.find('.fa-folder-card--wide').exists()).toBe(true)
    await wrapper.get('.fa-overview__head .fa-toolbar-menu button').trigger('click')
    const options = wrapper.findAll('[role="menuitemradio"]')
    expect(options.map((option) => option.text())).toEqual(['Kacheln', 'Liste'])
    await options[1]!.trigger('click')
    expect(wrapper.findAll('.fa-diagram-list__row')).toHaveLength(5)
    expect(localStorage.getItem(OVERVIEW_VIEW_KEY)).toBe('list')
  })

  it('offers thumbnails only with a source', async () => {
    wrapper = await overview(true)
    await wrapper.get('.fa-overview__head .fa-toolbar-menu button').trigger('click')
    expect(wrapper.findAll('[role="menuitemradio"]').map((option) => option.text())).toContain('Vorschaubilder')
  })
})
