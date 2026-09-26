import { fireEvent as domEvent } from '@testing-library/dom'
import { act, fireEvent } from '@testing-library/react'
import { flushPromises } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import RiskFlags from '../../../ui/src/risk/RiskFlags.vue'
import { riskCases, riskEvaluation, riskProfile } from '../../../ui-core/test/parity/cases-risk'
import { formState, normalizeDom } from '../../../ui-core/test/parity/dom'
import { FlowauditRiskFlags } from '../../src/risk/FlowauditRiskFlags'
import { expectParity, renderBoth, tick, type Rendered } from './setup'

describe('Parität Risiko-Merkmale Vue ↔ React', () => {
  for (const entry of riskCases) {
    it(entry.name, async () => {
      const rendered = await renderBoth(RiskFlags, { ...entry.props() }, <FlowauditRiskFlags {...entry.props()} />)
      expectParity(rendered, entry.expect)
    })
  }
})

type Step = (root: HTMLElement) => Element | null | undefined

/** Dieselbe Interaktion auf beiden Fassungen, danach DOM und Formularzustand vergleichen. */
async function both(rendered: Rendered, find: Step, value?: string): Promise<void> {
  for (const [root, fire] of [[rendered.vue, domEvent], [rendered.react, fireEvent]] as const) {
    const target = find(root) as HTMLInputElement
    expect(target, 'Ziel der Interaktion fehlt').toBeTruthy()
    if (value === undefined) fire.click(target)
    else if (target.tagName === 'SELECT') fire.change(target, { target: { value } })
    else fire.input(target, { target: { value } })
    await flushPromises()
    await tick()
  }
  expect(normalizeDom(rendered.react)).toBe(normalizeDom(rendered.vue))
  expect(formState(rendered.react)).toEqual(formState(rendered.vue))
}

const row = (key: string): Step => (root) => Array.from(root.querySelectorAll('.fa-risk-table tbody tr')).find((tr) => tr.textContent?.trim().startsWith(key))
const code = (value: string): Step => (root) => Array.from(root.querySelectorAll('.fa-risk-summary__code')).find((node) => node.textContent === value)
const testId = (id: string): Step => (root) => root.querySelector(`[data-testid="${id}"]`)

describe('Parität Risiko-Merkmale nach Interaktion', () => {
  it('Datensatz wählen, Code wählen, Filter ändern, suchen, sortieren, abwählen', async () => {
    const props = { evaluation: riskEvaluation, profile: riskProfile }
    const rendered = await renderBoth(RiskFlags, props, <FlowauditRiskFlags {...props} />)
    await both(rendered, row('B-012'))
    await both(rendered, code('RF13'))
    await both(rendered, testId('risk-filter-state'), 'all')
    await both(rendered, testId('risk-filter-code'), '')
    await both(rendered, testId('risk-filter-query'), 'B-00')
    await both(rendered, (root) => root.querySelector('.fa-risk-table .fa-table__sort'))
    await both(rendered, row('B-003'))
    await both(rendered, row('B-003'))
    await act(async () => undefined)
  })
})
