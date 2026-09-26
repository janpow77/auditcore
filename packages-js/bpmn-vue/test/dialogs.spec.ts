import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { issue, type DiagramInfo, type ExportChoice, type Suggestion } from '@auditcore/bpmn-flowaudit'
import DiagramInfoDialog from '../src/components/dialogs/DiagramInfoDialog.vue'
import EnrichmentDialog from '../src/components/dialogs/EnrichmentDialog.vue'
import ExportDialog from '../src/components/dialogs/ExportDialog.vue'
import XmlDialog from '../src/components/dialogs/XmlDialog.vue'
import BaseDialog from '../src/components/base/BaseDialog.vue'
import IssueList from '../src/components/views/IssueList.vue'
import KeyFilterBar from '../src/components/views/KeyFilterBar.vue'
import StatusBar from '../src/components/canvas/StatusBar.vue'
import { mountInContext } from './context'

const INFO: DiagramInfo = { title: 'Bewilligung', status: 'entwurf', version: '1.0', funds: ['efre'] }
const button = (wrapper: ReturnType<typeof mount>, text: string) => wrapper.findAll('button').find((item) => item.text().includes(text))!

describe('BaseDialog', () => {
  it('closes with Escape and via the close button', async () => {
    const wrapper = mount(BaseDialog, { props: { open: true, title: 'Titel' }, slots: { default: '<input />' }, attachTo: document.body })
    expect(wrapper.find('[role="dialog"]').attributes('aria-labelledby')).toBeTruthy()
    await wrapper.find('[role="dialog"]').trigger('keydown', { key: 'Escape' })
    await wrapper.find('.fa-icon-btn').trigger('click')
    expect(wrapper.emitted<[boolean]>('update:open')!.at(-1)![0]).toBe(false)
    wrapper.unmount()
  })
})

describe('DiagramInfoDialog', () => {
  it('edits a draft and applies it (funds as toggle chips)', async () => {
    const wrapper = mountInContext(DiagramInfoDialog, { open: true, info: INFO, profiles: [{ id: 'p', version: '1', title: 'Profil' }], fallbackTitle: 'Datei' })
    expect(wrapper.find('.fa-info-preview').text()).toContain('Bewilligung')
    const title = wrapper.find('.fa-info-section input')
    await title.setValue('Bewilligung und Auszahlung')
    await wrapper.find('.fa-chip[aria-pressed="true"]').trigger('click')
    await button(wrapper, 'Übernehmen').trigger('click')
    const dialog = wrapper.findComponent(DiagramInfoDialog)
    const [applied] = dialog.emitted<[DiagramInfo]>('apply')![0]!
    expect(applied).toMatchObject({ title: 'Bewilligung und Auszahlung', funds: [] })
    expect(INFO.title).toBe('Bewilligung')
    wrapper.unmount()
  })

  it('offers approval and a new version and shows the recorded hash', async () => {
    const approvals = [{ version: '1.0', sha256: 'a'.repeat(64) }]
    const wrapper = mountInContext(DiagramInfoDialog, { open: true, info: INFO, profiles: [], approvals, fallbackTitle: 'Datei' })
    expect(wrapper.text()).toContain('a'.repeat(64))
    await button(wrapper, 'Stand freigeben').trigger('click')
    await button(wrapper, 'Neue Version').trigger('click')
    const dialog = wrapper.findComponent(DiagramInfoDialog)
    expect(dialog.emitted('approve')).toHaveLength(1)
    expect(dialog.emitted('new-version')).toHaveLength(1)
    wrapper.unmount()
  })

  it('is read-only except for the status section', () => {
    const wrapper = mountInContext(DiagramInfoDialog, { open: true, info: INFO, profiles: [], fallbackTitle: 'Datei' }, { readonly: true })
    expect(button(wrapper, 'Übernehmen').attributes('disabled')).toBeDefined()
    wrapper.unmount()
  })
})

describe('ExportDialog', () => {
  const data = { colors: [{ fill: '#fff', stroke: '#000', label: 'Standard', meaning: 'Standard', count: 1 }], markers: [], legalBases: [] }

  it('preselects attachments from the data and emits the choice', async () => {
    const wrapper = mount(ExportDialog, { props: { open: true, defaultTitle: 'Bewilligung', data } })
    await wrapper.findAll('button').find((item) => item.text().includes('PDF'))!.trigger('click')
    const [choice] = wrapper.emitted<[ExportChoice]>('export')![0]!
    expect(choice).toMatchObject({ format: 'pdf', title: 'Bewilligung', showLegend: true, showMarkerLegend: false, neutral: false })
  })

  it('suggests the neutral export for confidential diagrams', async () => {
    const wrapper = mount(ExportDialog, { props: { open: true, defaultTitle: 'X', data, confidentiality: 'vs_nfd' } })
    await wrapper.findAll('button').find((item) => item.text().includes('SVG'))!.trigger('click')
    expect(wrapper.emitted<[ExportChoice]>('export')![0]![0]!.neutral).toBe(true)
  })
})

describe('EnrichmentDialog', () => {
  const suggestions: Suggestion[] = [
    { id: 's1', elementId: 'T1', kind: 'legalBasis', value: { act: 'Verordnung (EU) 2021/1060', article: '74' }, excerpt: 'Art. 74 CPR', origin: 'documentation' },
    { id: 's2', elementId: 'T1', kind: 'rolePrefix', value: 'ZGS', excerpt: 'ZGS: Antrag prüfen', origin: 'name' },
  ]

  it('accepts all suggestions by default and lets the user reject single ones', async () => {
    const wrapper = mount(EnrichmentDialog, { props: { open: true, suggestions, names: { T1: 'Antrag prüfen' } } })
    expect(wrapper.text()).toContain('Antrag prüfen')
    await wrapper.find('.fa-enrich__item input').setValue(false)
    await wrapper.find('.fa-btn--primary').trigger('click')
    const [accepted, removePrefixes] = wrapper.emitted<[Suggestion[], boolean]>('apply')![0]!
    expect(accepted.map((s) => s.id)).toEqual(['s2'])
    expect(removePrefixes).toBe(true)
  })
})

describe('XmlDialog', () => {
  it('applies edited XML unless read-only', async () => {
    const wrapper = mount(XmlDialog, { props: { open: true, xml: '<a/>' } })
    await wrapper.find('textarea').setValue('<b/>')
    await wrapper.find('.fa-btn--primary').trigger('click')
    expect(wrapper.emitted<[string]>('apply')![0]![0]).toBe('<b/>')
    const readonly = mount(XmlDialog, { props: { open: true, xml: '<a/>', readonly: true } })
    expect(readonly.find('textarea').attributes('readonly')).toBeDefined()
  })
})

describe('views', () => {
  const issues = [issue('BPMN-S010', 'Process_1', { name: 'Antrag' }), issue('BPMN-F001', 'Task_1', { name: 'Prüfen' })]

  it('IssueList filters by severity and jumps to elements', async () => {
    const wrapper = mount(IssueList, { props: { issues } })
    expect(wrapper.findAll('.fa-issue')).toHaveLength(2)
    await wrapper.findAll('.fa-chip')[1]!.trigger('click')
    expect(wrapper.findAll('.fa-issue')).toHaveLength(1)
    await wrapper.find('.fa-issue .fa-btn').trigger('click')
    expect(wrapper.emitted<[string]>('jump')![0]![0]).toBe('Process_1')
  })

  it('KeyFilterBar emits kind, value and clear', async () => {
    const wrapper = mount(KeyFilterBar, { props: { keys: { ka: { '2': ['T1'] } }, kind: 'ka', value: '', hits: 0 } })
    await wrapper.find('select').setValue('bk')
    await wrapper.find('input').setValue('2')
    await wrapper.find('.fa-btn').trigger('click')
    expect(wrapper.emitted('update:kind')![0]).toEqual(['bk'])
    expect(wrapper.emitted('update:value')![0]).toEqual(['2'])
    expect(wrapper.emitted('clear')).toHaveLength(1)
  })

  it('StatusBar shows zoom, counts and profile', async () => {
    const wrapper = mount(StatusBar, { props: { scale: 1.25, count: { fehler: 1, warnung: 2, hinweis: 0 }, profile: 'p@1' } })
    expect(wrapper.text()).toContain('125')
    expect(wrapper.text()).toContain('p@1')
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('issues')).toHaveLength(1)
  })
})
