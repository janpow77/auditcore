import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, it } from 'vitest'
import RiskFlags from '../src/risk/RiskFlags.vue'
import { riskCases } from '../../ui-core/test/parity/cases-risk'
import { checkExpectation } from '../../ui-core/test/parity/expect'

afterEach(() => {
  document.body.innerHTML = ''
})

/** Gemeinsame Paritätsfälle (ui-core/test/parity/cases-risk.ts) mit der Vue-Fassung. */
describe('RiskFlags – gemeinsame Paritätsfälle', () => {
  for (const entry of riskCases) {
    it(entry.name, async () => {
      const wrapper = mount(RiskFlags, { props: entry.props(), attachTo: document.body })
      await flushPromises()
      checkExpectation(wrapper.element as HTMLElement, entry.expect)
      wrapper.unmount()
    })
  }
})
