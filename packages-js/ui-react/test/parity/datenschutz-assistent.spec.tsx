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
})
