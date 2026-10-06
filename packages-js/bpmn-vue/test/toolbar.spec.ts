import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { hasIcon } from '@auditcore/bpmn-flowaudit'
import EditorToolbar from '../src/components/toolbar/EditorToolbar.vue'
import { CORE_ENTRY_ICONS, EDIT_ACTIONS, FILE_ACTIONS, handleShortcut, PALETTE_VIEW_KEY, readPaletteEntries, TABS, VIEW_ACTIONS } from '@auditcore/bpmn-flowaudit/ui'
import { rolesFor } from '@auditcore/bpmn-flowaudit'
import ToolPalette from '../src/components/palette/ToolPalette.vue'
import FaIcon from '../src/components/base/FaIcon.vue'
import ColorSwatches from '../src/components/base/ColorSwatches.vue'

const toolbarProps = { name: 'Muster', dirty: true, saving: false, readonly: false, canUndo: true, canRedo: false, direction: 'waagerecht' as const, pageView: 'aus', active: {} }

describe('icons', () => {
  it('exist for every toolbar action, palette entry and tab', () => {
    const names = [...FILE_ACTIONS, ...EDIT_ACTIONS, ...VIEW_ACTIONS].map((entry) => entry.icon).concat(Object.values(CORE_ENTRY_ICONS), TABS.map((tab) => tab.icon))
    expect(names.filter((name) => !hasIcon(name))).toEqual([])
  })

  it('renders decorative icons hidden and labelled icons as images', () => {
    expect(mount(FaIcon, { props: { name: 'save' } }).attributes('aria-hidden')).toBe('true')
    const labelled = mount(FaIcon, { props: { name: 'save', label: 'Speichern' } })
    expect(labelled.attributes('role')).toBe('img')
    expect(labelled.attributes('aria-label')).toBe('Speichern')
  })
})

describe('EditorToolbar', () => {
  it('shows menu host actions in the check menu, not as buttons, and emits their id', async () => {
    const wrapper = mount(EditorToolbar, { props: { ...toolbarProps, hostActions: [{ id: 'kontrollmatrix', label: 'Kontrollmatrix (XLSX)', group: 'export' as const }, { id: 'abgleich', label: 'Abgleich starten' }] }, attachTo: document.body })
    const buttonsBefore = wrapper.findAll('.fa-toolbar > button').length
    expect(wrapper.text()).not.toContain('Abgleich starten')
    await wrapper.findAll('.fa-toolbar-menu > button').find((item) => item.text().includes('Prüfen'))!.trigger('click')
    expect(wrapper.text()).toContain('Weitere Aktionen')
    expect(wrapper.text()).not.toContain('Kontrollmatrix')
    await wrapper.findAll('[role="menuitem"]').find((item) => item.text() === 'Abgleich starten')!.trigger('click')
    expect(wrapper.emitted<[string]>('host-action')![0]).toEqual(['abgleich'])
    expect(wrapper.findAll('.fa-toolbar > button')).toHaveLength(buttonsBefore)
    wrapper.unmount()
  })

  it('emits actions, renames and disables undo/redo by state', async () => {
    const wrapper = mount(EditorToolbar, { props: toolbarProps })
    expect(wrapper.text()).toContain('ungespeichert')
    await wrapper.find('.fa-btn--primary').trigger('click')
    expect(wrapper.emitted('action')![0]).toEqual(['save'])
    await wrapper.find('.fa-toolbar__name').setValue('Neu')
    expect(wrapper.emitted('update:name')![0]).toEqual(['Neu'])
    const redo = wrapper.find('[aria-label="Wiederholen"]')
    expect(redo.attributes('disabled')).toBeDefined()
  })

  it('blocks writing actions when read-only and hides configured actions', () => {
    const wrapper = mount(EditorToolbar, { props: { ...toolbarProps, readonly: true, hidden: ['export'] } })
    expect(wrapper.find('.fa-btn--primary').attributes('disabled')).toBeDefined()
    expect(wrapper.find('[aria-label="Exportieren"]').exists()).toBe(false)
  })
})

describe('palette', () => {
  it('maps core entries to own icons and drops separators', () => {
    const items = readPaletteEntries({ 'hand-tool': { group: 'tools', title: 'Hand' }, 'tool-separator': { separator: true }, 'create.task': { group: 'activity', title: 'Aufgabe' } })
    expect(items).toEqual([
      { id: 'hand-tool', title: 'Hand', group: 'tools', icon: 'hand', html: undefined },
      { id: 'create.task', title: 'Aufgabe', group: 'activity', icon: 'bpmn-task', html: undefined },
    ])
  })

  it('triggers entries by click', async () => {
    const wrapper = mount(ToolPalette, { props: { items: readPaletteEntries({ 'create.task': { group: 'activity', title: 'Aufgabe' } }) } })
    await wrapper.find('.fa-palette__item').trigger('click')
    expect(wrapper.emitted<[string, Event]>('trigger')![0]![0]).toBe('create.task')
  })

  it('switches between icons, tiles and list in one menu and keeps the choice', async () => {
    localStorage.removeItem(PALETTE_VIEW_KEY)
    const items = readPaletteEntries({ 'create.task': { group: 'activity', title: 'Aufgabe anlegen' }, 'flowaudit-pool-rfs': { group: 'flowaudit-roles', title: 'Pool anlegen: RFS' } }, rolesFor(null, '2021-2027'))
    const wrapper = mount(ToolPalette, { props: { items }, attachTo: document.body })
    expect(wrapper.findAll('.fa-palette__head button')).toHaveLength(1)
    expect(wrapper.find('.fa-palette__caption').exists()).toBe(false)
    await wrapper.find('.fa-palette__head button').trigger('click')
    await wrapper.findAll('[role="menuitemradio"]')[2]!.trigger('click')
    expect(localStorage.getItem(PALETTE_VIEW_KEY)).toBe('list')
    expect(wrapper.text()).toContain('Stelle mit Rechnungsführungsfunktion (Art. 76 CPR)')
    expect(wrapper.text()).toContain('Aufgabe')
    await wrapper.findAll('.fa-palette__item').at(-1)!.trigger('dragstart')
    expect(wrapper.emitted<[string, Event]>('trigger')!.at(-1)![0]).toBe('flowaudit-pool-rfs')
    const again = mount(ToolPalette, { props: { items } })
    expect(again.find('.fa-palette--list').exists()).toBe(true)
    localStorage.setItem(PALETTE_VIEW_KEY, 'tiles')
    expect(mount(ToolPalette, { props: { items } }).find('.fa-palette__caption').text()).toBe('Aufgabe')
    localStorage.removeItem(PALETTE_VIEW_KEY)
    wrapper.unmount()
  })
})

describe('ColorSwatches', () => {
  it('emits the chosen colour or null for reset', async () => {
    const wrapper = mount(ColorSwatches, { props: { colors: [{ id: 'w', fill: '#fff', stroke: '#000', label: 'Weiß', meaning: 'neutral' }] } })
    const buttons = wrapper.findAll('button')
    await buttons[0]!.trigger('click')
    await buttons.at(-1)!.trigger('click')
    const emitted = wrapper.emitted<[unknown]>('choose')!.map((entry) => entry[0])
    expect(emitted).toContainEqual({ id: 'w', fill: '#fff', stroke: '#000', label: 'Weiß', meaning: 'neutral' })
    expect(emitted).toContain(null)
  })
})

describe('shortcuts', () => {
  const handlers = () => ({ save: vi.fn(), search: vi.fn(), help: vi.fn() })

  it('handles Ctrl+S, Ctrl+F and „?“ outside of inputs', () => {
    const h = handlers()
    expect(handleShortcut(new KeyboardEvent('keydown', { key: 's', ctrlKey: true }), h)).toBe(true)
    expect(handleShortcut(new KeyboardEvent('keydown', { key: 'F', metaKey: true }), h)).toBe(true)
    expect(handleShortcut(new KeyboardEvent('keydown', { key: '?' }), h)).toBe(true)
    expect(handleShortcut(new KeyboardEvent('keydown', { key: 'x' }), h)).toBe(false)
    expect([h.save, h.search, h.help].map((fn) => fn.mock.calls.length)).toEqual([1, 1, 1])
  })

  it('ignores „?“ while typing', () => {
    const h = handlers()
    const input = document.createElement('input')
    const event = new KeyboardEvent('keydown', { key: '?', bubbles: true })
    Object.defineProperty(event, 'target', { value: input })
    expect(handleShortcut(event, h)).toBe(false)
  })
})
