import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { TYPES, EXTENSION_FIELDS, ProfileLegalSearch, type LegalBasis } from '@flowaudit/bpmn-flowaudit'
import FieldForm from '../src/panels/FieldForm.vue'
import ListEditor from '../src/panels/ListEditor.vue'
import LegalBasisEditor from '../src/panels/legal/LegalBasisEditor.vue'
import LegalSearch from '../src/panels/legal/LegalSearch.vue'
import { CONTROL_LIST, LISTS, type FieldDescriptor } from '../src/panels/descriptors'
import { listsFor, TABS, tabsFor } from '../src/panels/tabs'
import { until } from './helpers'

const noOptions = () => []

describe('field descriptors', () => {
  it('describe only attributes that exist in the FlowAudit schema', () => {
    for (const list of Object.values(LISTS)) {
      const xml = EXTENSION_FIELDS.find((field) => field.key === list.key)?.xml
      const spec = Object.values(TYPES).find((type) => type.xml === xml)
      expect(spec, list.key).toBeDefined()
      const keys = new Set(spec!.fields.map((field) => field.key))
      for (const field of list.fields) expect(keys.has(field.key), `${list.key}.${field.key}`).toBe(true)
    }
  })

  it('summarise entries and create empty ones', () => {
    expect(CONTROL_LIST.summary({ id: 'K1', label: 'Vier-Augen-Prüfung' })).toContain('Vier-Augen-Prüfung')
    expect(CONTROL_LIST.create()).toBeTypeOf('object')
  })
})

describe('tabs', () => {
  it('offers tabs per element type', () => {
    const ids = (type: string) => tabsFor(type).map((tab) => tab.id)
    expect(ids('bpmn:Task')).toEqual(expect.arrayContaining(['general', 'role', 'legal', 'control', 'findings', 'color']))
    expect(ids('bpmn:Lane')).toContain('role')
    expect(ids('bpmn:Lane')).not.toContain('control')
    expect(ids('bpmn:SequenceFlow')).toEqual(['general', 'notes', 'color'])
    expect(tabsFor(null)).toEqual([])
  })

  it('edits evidence only at data objects and deadlines only at activities', () => {
    const evidence = TABS.find((tab) => tab.id === 'evidence')!
    expect(listsFor(evidence, 'bpmn:DataObjectReference')).toEqual(['evidence'])
    expect(listsFor(evidence, 'bpmn:Task')).toEqual(['deadlines'])
  })
})

describe('FieldForm', () => {
  const fields: FieldDescriptor[] = [
    { key: 'label', label: 'field.label', kind: 'text' },
    { key: 'keyControl', label: 'field.keyControl', kind: 'checkbox' },
    { key: 'controls', label: 'field.controls', kind: 'tokens' },
    { key: 'frequency', label: 'field.frequency', kind: 'select' },
  ]

  it('emits the updated object, trims text and drops empty values', async () => {
    const wrapper = mount(FieldForm, { props: { value: { label: 'alt', frequency: 'monatlich' }, fields, optionsFor: () => [{ value: 'monatlich', label: 'monatlich' }] } })
    const input = wrapper.find('input.fa-input')
    const last = () => wrapper.emitted<[Record<string, unknown>]>('update')!.at(-1)![0]
    await input.setValue('  neu  ')
    expect(last()).toEqual({ label: 'neu', frequency: 'monatlich' })
    await wrapper.find('input[type="checkbox"]').setValue(true)
    expect(last()).toMatchObject({ keyControl: true })
    await wrapper.findAll('input.fa-input')[1].setValue('K1, K2 K3')
    expect(last()).toMatchObject({ controls: ['K1', 'K2', 'K3'] })
    await wrapper.find('select').setValue('')
    expect(last()).not.toHaveProperty('frequency')
  })

  it('keeps unknown select values visible and respects disabled', () => {
    const wrapper = mount(FieldForm, { props: { value: { frequency: 'alle 7 Jahre' }, fields, optionsFor: noOptions, disabled: true } })
    expect(wrapper.find('select').text()).toContain('alle 7 Jahre')
    expect(wrapper.findAll('input').every((input) => input.attributes('disabled') !== undefined)).toBe(true)
  })
})

describe('ListEditor', () => {
  it('adds, opens, edits and removes entries', async () => {
    const wrapper = mount(ListEditor, { props: { descriptor: LISTS.controls, items: [{ id: 'K1', label: 'Sichtprüfung' }], optionsFor: noOptions } })
    expect(wrapper.text()).toContain('Sichtprüfung')
    await wrapper.find('.fa-btn').trigger('click')
    expect(wrapper.emitted<[unknown[]]>('update')![0][0]).toHaveLength(2)
    await wrapper.find('.fa-list-editor__toggle').trigger('click')
    expect(wrapper.find('.fa-field-form').exists()).toBe(true)
    await wrapper.find('.fa-list-editor__row .fa-icon-btn').trigger('click')
    expect(wrapper.emitted<[unknown[]]>('update')![1][0]).toEqual([])
  })
})

describe('legal bases', () => {
  it('takes a typed citation over in structured form', async () => {
    const wrapper = mount(LegalSearch)
    await wrapper.find('input').setValue('Art. 74 Abs. 1 VO (EU) 2021/1060')
    await wrapper.find('[role="option"]').trigger('click')
    const [chosen] = wrapper.emitted<[LegalBasis]>('choose')![0]
    expect(chosen).toMatchObject({ article: '74', paragraph: '1' })
    expect(chosen.act).toContain('2021/1060')
  })

  it('asks the search port for suggestions (debounced)', async () => {
    const port = { search: vi.fn(async () => [{ act: 'Verordnung (EU) 2021/1060', article: '69', title: 'Verantwortlichkeiten', origin: 'Profil' }]) }
    const wrapper = mount(LegalSearch, { props: { port, profileId: 'p' } })
    await wrapper.find('input').setValue('Verantwort')
    await until(() => wrapper.text().includes('Verantwortlichkeiten'))
    expect(port.search).toHaveBeenCalledWith('Verantwort', expect.objectContaining({ profile: 'p' }))
    const option = wrapper.findAll('[role="option"]').find((item) => item.text().includes('Verantwortlichkeiten'))!
    await option.trigger('click')
    expect(wrapper.emitted<[LegalBasis]>('choose')![0][0]).toEqual({ act: 'Verordnung (EU) 2021/1060', article: '69' })
  })

  it('keeps legacy free text and splits it into structured entries on request', async () => {
    const items: LegalBasis[] = [{ text: 'Art. 74 VO (EU) 2021/1060; interne Weisung' }]
    const wrapper = mount(LegalBasisEditor, { props: { items } })
    expect(wrapper.text()).toContain('Altbestand')
    await wrapper.find('.fa-list-editor__toggle').trigger('click')
    await wrapper.find('.fa-list-editor__form .fa-btn').trigger('click')
    const [updated] = wrapper.emitted<[LegalBasis[]]>('update')![0]
    expect(updated[0]).toMatchObject({ article: '74' })
    expect(updated.at(-1)).toEqual({ text: 'interne Weisung' })
  })

  it('ignores duplicates and removes entries', async () => {
    const items: LegalBasis[] = [{ act: 'Verordnung (EU) 2021/1060', article: '74' }]
    const wrapper = mount(LegalBasisEditor, { props: { items, port: new ProfileLegalSearch(null) } })
    await wrapper.find('input').setValue('Art. 74 VO (EU) 2021/1060')
    await wrapper.find('[role="option"]').trigger('click')
    expect(wrapper.emitted('update')).toBeUndefined()
    await wrapper.find('.fa-list-editor__row .fa-icon-btn').trigger('click')
    expect(wrapper.emitted<[LegalBasis[]]>('update')![0][0]).toEqual([])
  })
})
