// Gemeinsame Paritätsfälle (ui-core/test/parity/cases-extrapolation.ts) gegen
// die Vue-Fassung; die React-Fassung prüft dieselben Fälle und vergleicht
// zusätzlich das DOM.
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, it } from 'vitest'
import { extrapolationCases } from '../../ui-core/test/parity/cases-extrapolation'
import { checkExpectation } from '../../ui-core/test/parity/expect'
import ExtrapolationPanel from '../src/extrapolation/ExtrapolationPanel.vue'

afterEach(() => {
  document.body.innerHTML = ''
})

describe('Paritätsfälle Hochrechnung (Vue)', () => {
  for (const entry of extrapolationCases) {
    it(entry.name, async () => {
      const wrapper = mount(ExtrapolationPanel, { props: { ...entry.props() }, attachTo: document.body })
      await flushPromises()
      checkExpectation(wrapper.element as HTMLElement, entry.expect)
      wrapper.unmount()
    })
  }
})
