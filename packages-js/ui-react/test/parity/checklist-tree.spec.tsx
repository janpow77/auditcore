import { fireEvent as domEvent } from '@testing-library/dom'
import { act, cleanup, fireEvent, render } from '@testing-library/react'
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it } from 'vitest'
import type { ChecklistItemView } from '@auditcore/ui-core'
import { fresh } from '../../../ui-core/test/dataprotection/fake-assistant-port'
import { normalizeDom } from '../../../ui-core/test/parity/dom'
import VueChecklist from '../../../ui/src/dataprotection/components/AssistantChecklist.vue'
import VueDetail from '../../../ui/src/dataprotection/components/AssistantChecklistDetail.vue'
import { AssistantChecklist } from '../../src/dataprotection/assistant/AssistantChecklist'
import { AssistantChecklistDetail } from '../../src/dataprotection/assistant/AssistantChecklistDetail'
import { tick } from './setup'

const items = fresh.pruefpunkte as ChecklistItemView[]
const copy = (list: ChecklistItemView[]): ChecklistItemView[] => JSON.parse(JSON.stringify(list)) as ChecklistItemView[]
const noop = (): void => undefined
const count = (root: Element): number => root.querySelectorAll('.fa-checklist__node--item').length

afterEach(() => {
  cleanup()
  document.body.innerHTML = ''
})

describe('Parität Prüfpunkte-Baum: Entwurf und aufgeklappte Bereiche Vue ↔ React', () => {
  it('behält die ungespeicherte Eingabe bei inhaltsgleichem neuem Objekt und übernimmt geänderten Serverinhalt', async () => {
    const item = items[0] as ChecklistItemView
    const vue = mount(VueDetail, { props: { item, busy: false }, attachTo: document.body })
    const react = render(<AssistantChecklistDetail item={item} busy={false} onChange={noop} />)
    const areas = [vue.element.querySelector('textarea'), react.container.querySelector('textarea')] as HTMLTextAreaElement[]
    domEvent.input(areas[0] as HTMLTextAreaElement, { target: { value: 'Entwurf' } })
    fireEvent.change(areas[1] as HTMLTextAreaElement, { target: { value: 'Entwurf' } })
    await flushPromises()
    await tick()
    const same = copy([item])[0] as ChecklistItemView
    await vue.setProps({ item: same } as never)
    react.rerender(<AssistantChecklistDetail item={same} busy={false} onChange={noop} />)
    await tick()
    expect(areas.map((area) => area.value)).toEqual(['Entwurf', 'Entwurf'])
    const served = { ...item, justification: 'vom Server' }
    await vue.setProps({ item: served } as never)
    react.rerender(<AssistantChecklistDetail item={served} busy={false} onChange={noop} />)
    await tick()
    expect(areas.map((area) => area.value)).toEqual(['vom Server', 'vom Server'])
    expect(normalizeDom(react.container.firstElementChild as HTMLElement)).toBe(normalizeDom(vue.element as HTMLElement))
    await act(async () => undefined)
  })

  it('klappt erst später kommende Bereiche auf und lässt bedienten Knoten ihren Zustand', async () => {
    const vue = mount(VueChecklist, { props: { items: [], busy: false }, attachTo: document.body })
    const react = render(<AssistantChecklist items={[]} busy={false} onChange={noop} />)
    await tick()
    const roots = [vue.element as HTMLElement, react.container.firstElementChild as HTMLElement]
    const update = async (next: ChecklistItemView[]): Promise<void> => {
      await vue.setProps({ items: next } as never)
      await flushPromises()
      react.rerender(<AssistantChecklist items={next} busy={false} onChange={noop} />)
      await tick()
    }
    await update(copy(items))
    expect(roots.map(count)).toEqual([30, 30])
    domEvent.click(roots[0]?.querySelector('[data-node="bereich:A"] > .fa-checklist__row') as HTMLElement)
    fireEvent.click(roots[1]?.querySelector('[data-node="bereich:A"] > .fa-checklist__row') as HTMLElement)
    await tick()
    expect(roots.map(count)).toEqual([26, 26])
    await update([...copy(items), { ...(items[0] as ChecklistItemView), id: 'CHK-99', bereich: 'G' }])
    expect(roots.map(count)).toEqual([27, 27])
    // role="tabpanel" setzt in Vue der umgebende Reiter; verglichen wird der Baum.
    const trees = roots.map((root) => root.querySelector('.fa-checklist__tree') as HTMLElement)
    expect(normalizeDom(trees[1] as HTMLElement)).toBe(normalizeDom(trees[0] as HTMLElement))
  })
})
