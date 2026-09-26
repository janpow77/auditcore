import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, it } from 'vitest'
import ScreeningReview from '../src/screening/ScreeningReview.vue'
import { screeningCases } from '../../ui-core/test/parity/cases-screening'
import { checkExpectation } from '../../ui-core/test/parity/expect'

afterEach(() => {
  document.body.innerHTML = ''
})

/** Gemeinsame Paritätsfälle (ui-core/test/parity/cases-screening.ts) mit der Vue-Fassung. */
describe('ScreeningReview – gemeinsame Paritätsfälle', () => {
  for (const entry of screeningCases) {
    it(entry.name, async () => {
      const wrapper = mount(ScreeningReview, { props: entry.props(), attachTo: document.body })
      await flushPromises()
      checkExpectation(wrapper.element as HTMLElement, entry.expect)
      wrapper.unmount()
    })
  }
})
