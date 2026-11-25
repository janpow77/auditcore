import { FaDatenschutzAssistent } from '@auditcore/ui'
import { fireEvent as domEvent } from '@testing-library/dom'
import { act, fireEvent } from '@testing-library/react'
import { flushPromises } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import { activityId, fakeAssistantPort } from '../../../ui-core/test/dataprotection/fake-assistant-port'
import { assistantCases } from '../../../ui-core/test/parity/cases-datenschutz-assistent'
import { normalizeDom } from '../../../ui-core/test/parity/dom'
import { FlowauditDatenschutzAssistent } from '../../src/dataprotection/FlowauditDatenschutzAssistent'
import { expectParity, renderBoth, tick } from './setup'

describe('Parität Datenschutz-Assistent Vue ↔ React', () => {
  for (const entry of assistantCases) {
    it(entry.name, async () => {
      const rendered = await renderBoth(FaDatenschutzAssistent, { ...entry.props() }, <FlowauditDatenschutzAssistent {...entry.props()} />)
      expectParity(rendered, entry.expect)
    })
  }

  it('Antwort wählen und Reiter wechseln führt zu gleichem DOM', async () => {
    const rendered = await renderBoth(
      FaDatenschutzAssistent,
      { port: fakeAssistantPort(), activityId },
      <FlowauditDatenschutzAssistent port={fakeAssistantPort()} activityId={activityId} />,
    )
    for (const [root, fire] of [[rendered.vue, domEvent], [rendered.react, fireEvent]] as const) {
      fire.click(root.querySelector('input[type="radio"][value="unklar"]') as HTMLElement)
      await flushPromises()
      await tick()
      fire.click(Array.from(root.querySelectorAll('[role="tab"]')).find((node) => node.textContent === 'Status und Sperren') as HTMLElement)
      await flushPromises()
      await tick()
    }
    expect(normalizeDom(rendered.react)).toBe(normalizeDom(rendered.vue))
    expect(rendered.vue.textContent).toContain('Es gibt bewusst keinen Gesamtstatus')
    await act(async () => undefined)
  })

  it('Prüfpunkte als Baum: aufklappen, Status ändern und speichern führt zu gleichem DOM', async () => {
    const ports = [fakeAssistantPort(), fakeAssistantPort()] as const
    const rendered = await renderBoth(
      FaDatenschutzAssistent,
      { port: ports[0], activityId },
      <FlowauditDatenschutzAssistent port={ports[1]} activityId={activityId} />,
    )
    for (const [root, fire, port] of [[rendered.vue, domEvent, ports[0]], [rendered.react, fireEvent, ports[1]]] as const) {
      fire.click(Array.from(root.querySelectorAll('[role="tab"]')).find((node) => node.textContent === 'Prüfpunkte') as HTMLElement)
      await flushPromises()
      await tick()
      expect(root.querySelectorAll('.fa-checklist__node--area').length).toBe(6)
      expect(root.querySelectorAll('.fa-checklist__node--item').length).toBe(30)
      expect(root.querySelectorAll('.fa-checklist__detail').length).toBe(0)
      fire.click(root.querySelector('[data-node="bereich:B"] > .fa-checklist__row') as HTMLElement)
      fire.click(root.querySelector('[data-item="CHK-14"] > .fa-checklist__row') as HTMLElement)
      await tick()
      expect(root.querySelectorAll('.fa-checklist__node--item').length).toBe(25)
      const detail = root.querySelector('[data-item="CHK-14"] .fa-checklist__detail') as HTMLElement
      expect(detail.textContent).toContain('Betriebsnachweis, Konzept, Test')
      fire.change(detail.querySelector('select') as HTMLElement, { target: { value: 'zur_pruefung' } })
      await tick()
      // v-model hört bei Eingabefeldern auf „input“, React auf „change“.
      ;(fire === domEvent ? fire.input : fire.change)(detail.querySelector('input[type="date"]') as HTMLElement, { target: { value: '2026-11-30' } })
      await tick()
      fire.click(detail.querySelector('.fa-checklist__save') as HTMLElement)
      await flushPromises()
      await tick()
      expect(port.checklist).toHaveBeenCalledWith(activityId, 'CHK-14', { status: 'zur_pruefung', justification: '', evidence_ids: [], due: '2026-11-30' }, expect.anything())
    }
    expect(normalizeDom(rendered.react)).toBe(normalizeDom(rendered.vue))
    expect(rendered.vue.textContent).toContain('0 von 30 erledigt')
    expect(rendered.vue.textContent).toContain('Bereich A')
    await act(async () => undefined)
  })
})
