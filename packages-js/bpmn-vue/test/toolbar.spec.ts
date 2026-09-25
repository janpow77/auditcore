import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { hasIcon } from '@flowaudit/bpmn-flowaudit'
import EditorToolbar from '../src/components/toolbar/EditorToolbar.vue'
import { EDIT_ACTIONS, FILE_ACTIONS, VIEW_ACTIONS } from '../src/components/toolbar/toolbarActions'
import ToolPalette from '../src/components/palette/ToolPalette.vue'
import { CORE_ENTRY_ICONS, readPaletteEntries } from '../src/components/palette/paletteEntries'
import FaIcon from '../src/components/base/FaIcon.vue'
import ColorSwatches from '../src/components/base/ColorSwatches.vue'
import { handleShortcut } from '../src/composables/useShortcuts'
import { TABS } from '../src/panels/tabs'

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
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted<[string, Event]>('trigger')![0][0]).toBe('create.task')
  })
})

describe('ColorSwatches', () => {
  it('emits the chosen colour or null for reset', async () => {
    const wrapper = mount(ColorSwatches, { props: { colors: [{ id: 'w', fill: '#fff', stroke: '#000', label: 'Weiß', meaning: 'neutral' }] } })
    const buttons = wrapper.findAll('button')
    await buttons[0].trigger('click')
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
