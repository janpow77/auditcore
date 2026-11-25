import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import type { ChecklistItemView } from '@auditcore/ui-core'
import { fresh } from '../../../ui-core/test/dataprotection/fake-assistant-port'
import AssistantChecklist from '../../src/dataprotection/components/AssistantChecklist.vue'
import AssistantChecklistDetail from '../../src/dataprotection/components/AssistantChecklistDetail.vue'

const items = fresh.pruefpunkte as ChecklistItemView[]
const copy = (list: ChecklistItemView[]): ChecklistItemView[] => JSON.parse(JSON.stringify(list)) as ChecklistItemView[]
const itemCount = (root: Element): number => root.querySelectorAll('.fa-checklist__node--item').length

describe('Prüfpunkte-Baum: Entwurf und aufgeklappte Bereiche (Vue)', () => {
  it('behält die ungespeicherte Eingabe bei inhaltsgleichem neuem Objekt und übernimmt geänderten Serverinhalt', async () => {
    const item = items[0] as ChecklistItemView
    const wrapper = mount(AssistantChecklistDetail, { props: { item, busy: false } })
    const area = wrapper.get('textarea')
    await area.setValue('Entwurf')
    await wrapper.setProps({ item: JSON.parse(JSON.stringify(item)) as ChecklistItemView })
    expect((area.element as HTMLTextAreaElement).value).toBe('Entwurf')
    await wrapper.setProps({ item: { ...item, justification: 'vom Server' } })
    expect((area.element as HTMLTextAreaElement).value).toBe('vom Server')
  })

  it('klappt erst später kommende Bereiche auf und lässt bedienten Knoten ihren Zustand', async () => {
    const wrapper = mount(AssistantChecklist, { props: { items: [], busy: false } })
    expect(wrapper.findAll('.fa-checklist__node--area').length).toBe(0)
    await wrapper.setProps({ items: copy(items) })
    await flushPromises()
    expect(itemCount(wrapper.element)).toBe(30)
    await wrapper.get('[data-node="bereich:A"] > .fa-checklist__row').trigger('click')
    expect(itemCount(wrapper.element)).toBe(26)
    const extra = { ...(items[0] as ChecklistItemView), id: 'CHK-99', bereich: 'G' }
    await wrapper.setProps({ items: [...copy(items), extra] })
    await flushPromises()
    expect(itemCount(wrapper.element)).toBe(27)
    expect(wrapper.find('[data-node="bereich:G"] [data-item="CHK-99"]').exists()).toBe(true)
  })
})
