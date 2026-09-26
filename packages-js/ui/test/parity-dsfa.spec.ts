import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, it } from 'vitest'
import FaDsfa from '../src/dataprotection/FaDsfa.vue'
import { dsfaCases } from '../../ui-core/test/parity/cases-dsfa'
import { checkExpectation } from '../../ui-core/test/parity/expect'

afterEach(() => {
  document.body.innerHTML = ''
})

/** Gemeinsame Paritätsfälle (ui-core/test/parity/cases-dsfa.ts) mit der Vue-Fassung. */
describe('FaDsfa – gemeinsame Paritätsfälle', () => {
  for (const entry of dsfaCases) {
    it(entry.name, async () => {
      const wrapper = mount(FaDsfa, { props: entry.props(), attachTo: document.body })
      await flushPromises()
      checkExpectation(wrapper.element as HTMLElement, entry.expect)
      wrapper.unmount()
    })
  }
})
