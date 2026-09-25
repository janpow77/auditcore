import { afterEach, describe, expect, it } from 'vitest'
import { mount, type VueWrapper } from '@vue/test-utils'
import { nextTick } from 'vue'
import FlowauditEditor from '../src/components/FlowauditEditor.vue'
import { fixture, until } from './helpers'

type EditorVm = { select(id: string): void; getXml(): Promise<string>; validation: { count: { value: { fehler: number; warnung: number; hinweis: number } } } }

let wrapper: VueWrapper | undefined

afterEach(() => {
  wrapper?.unmount()
  wrapper = undefined
})

async function mountEditor(props: Record<string, unknown> = {}): Promise<VueWrapper> {
  wrapper = mount(FlowauditEditor, { props: { xml: fixture('schema-1.1.bpmn'), name: 'Muster', lockApproved: false, ...props }, attachTo: document.body })
  await until(() => wrapper!.find('.djs-container').exists() && wrapper!.text().includes('Bewilligung'))
  return wrapper
}

const vm = (w: VueWrapper) => w.vm as unknown as EditorVm

describe('FlowauditEditor', () => {
  it('imports a 1.1 diagram with the core editor and renders toolbar, palette and status bar', async () => {
    const w = await mountEditor()
    expect(w.find('[role="toolbar"]').exists()).toBe(true)
    expect(w.html()).toContain('fa-palette')
    expect(w.find('.fa-statusbar').exists()).toBe(true)
  })

  it('shows the properties of the selected element and writes changes back into the XML', async () => {
    const w = await mountEditor()
    vm(w).select('Task_Bewilligen')
    await until(() => w.find('[role="tablist"]').exists())
    const tabs = w.findAll('[role="tab"]').map((tab) => tab.attributes('id'))
    expect(tabs).toEqual(expect.arrayContaining(['fa-tab-general', 'fa-tab-legal', 'fa-tab-control', 'fa-tab-findings']))
    const name = w.find('.fa-tab-general input')
    await name.setValue('Zuwendung bewilligen')
    await name.trigger('change')
    await until(() => w.emitted('update:xml') !== undefined)
    const xml = w.emitted<[string]>('update:xml')!.at(-1)![0]
    expect(xml).toContain('name="Zuwendung bewilligen"')
    expect(xml).toContain('flowaudit:diagrammInfo')
  })

  it('switches tabs with the arrow keys (WAI-ARIA tabs)', async () => {
    const w = await mountEditor()
    vm(w).select('Task_Bewilligen')
    await until(() => w.find('#fa-tab-general').exists())
    await w.find('#fa-tab-general').trigger('keydown', { key: 'ArrowDown' })
    expect(w.find('[role="tab"][aria-selected="true"]').attributes('id')).not.toBe('fa-tab-general')
  })

  it('validates locally after import and lists issues with a jump to the element', async () => {
    const w = await mountEditor()
    const count = vm(w).validation.count.value
    expect(count.fehler + count.warnung + count.hinweis).toBeGreaterThan(0)
    await w.find('.fa-statusbar button').trigger('click')
    await until(() => w.find('.fa-issues').exists())
    expect(w.find('.fa-issues').text()).toMatch(/BPMN-/)
  })

  it('emits save with XML and diagram info on Ctrl+S', async () => {
    const w = await mountEditor()
    await w.find('.fa-editor').trigger('keydown', { key: 's', ctrlKey: true })
    await until(() => w.emitted('save') !== undefined)
    const [payload] = w.emitted<[{ xml: string; info: { title?: string } | null }]>('save')![0]!
    expect(payload.xml).toContain('bpmn:definitions')
    expect(payload.info).not.toBeNull()
  })

  it('does not save and disables inputs when read-only', async () => {
    const w = await mountEditor({ readonly: true })
    await w.find('.fa-editor').trigger('keydown', { key: 's', ctrlKey: true })
    await nextTick()
    expect(w.emitted('save')).toBeUndefined()
    vm(w).select('Task_Bewilligen')
    await until(() => w.find('.fa-tab-general').exists())
    expect(w.find('.fa-tab-general input').attributes('disabled')).toBeDefined()
  })

  it('locks approved diagrams unless lockApproved is disabled', async () => {
    const w = await mountEditor({ lockApproved: true })
    await w.find('.fa-editor').trigger('keydown', { key: 's', ctrlKey: true })
    await nextTick()
    expect(w.emitted('save')).toBeUndefined()
  })

  it('opens the shortcut help with „?“ and the element search with Ctrl+F', async () => {
    const w = await mountEditor()
    await w.find('.fa-editor').trigger('keydown', { key: '?' })
    await until(() => w.find('[role="dialog"]').exists())
    expect(w.find('[role="dialog"]').text()).toContain('Rückgängig')
    await w.find('[role="dialog"] .fa-icon-btn').trigger('click')
    await w.find('.fa-editor').trigger('keydown', { key: 'f', ctrlKey: true })
    await until(() => w.find('[role="dialog"] input').exists())
  })

  it('reports import errors instead of throwing', async () => {
    wrapper = mount(FlowauditEditor, { props: { xml: '<kein-bpmn/>', name: 'X' }, attachTo: document.body })
    await until(() => wrapper!.emitted('error') !== undefined)
    expect(wrapper.emitted<[string]>('error')![0]![0]).toBeTruthy()
  })
})
