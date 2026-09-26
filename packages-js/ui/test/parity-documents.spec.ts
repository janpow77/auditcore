import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, it } from 'vitest'
import FaComparisons from '../src/documents/FaComparisons.vue'
import { comparisonsCases } from '../../ui-core/test/parity/cases-documents'
import { checkExpectation } from '../../ui-core/test/parity/expect'

afterEach(() => {
  document.body.innerHTML = ''
})

/** Gemeinsame Paritätsfälle (ui-core/test/parity/cases-documents.ts) mit der Vue-Fassung. */
describe('FaComparisons – gemeinsame Paritätsfälle', () => {
  for (const entry of comparisonsCases) {
    it(entry.name, async () => {
      const wrapper = mount(FaComparisons, { props: entry.props(), attachTo: document.body })
      await flushPromises()
      checkExpectation(wrapper.element as HTMLElement, entry.expect)
      wrapper.unmount()
    })
  }
})
