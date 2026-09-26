// Gemeinsame Paritätsfälle der Belegerkennung (ui-core/test/parity/cases-extraction.ts)
// gegen die Vue-Fassung; die React-Fassung prüft dieselben Fälle und vergleicht das DOM.
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, it } from 'vitest'
import { extractionCases } from '../../ui-core/test/parity/cases-extraction'
import { checkExpectation } from '../../ui-core/test/parity/expect'
import FaExtraction from '../src/extraction/FaExtraction.vue'

afterEach(() => {
  document.body.innerHTML = ''
})

describe('Paritätsfälle Belegerkennung (Vue)', () => {
  for (const entry of extractionCases) {
    it(entry.name, async () => {
      const wrapper = mount(FaExtraction, { props: { ...entry.props() }, attachTo: document.body })
      await flushPromises()
      checkExpectation(wrapper.element as HTMLElement, entry.expect)
      wrapper.unmount()
    })
  }
})
