// Gemeinsame Paritätsfälle (ui-core/test/parity/cases-attributes.ts) gegen
// die Vue-Fassung; die React-Fassung prüft dieselben Fälle und vergleicht
// zusätzlich das DOM.
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, it } from 'vitest'
import { attributesCases } from '../../ui-core/test/parity/cases-attributes'
import { checkExpectation } from '../../ui-core/test/parity/expect'
import AttributeSampling from '../src/attributes/AttributeSampling.vue'

afterEach(() => {
  document.body.innerHTML = ''
})

describe('Paritätsfälle AttributeSampling (Vue)', () => {
  for (const entry of attributesCases) {
    it(entry.name, async () => {
      const wrapper = mount(AttributeSampling, { props: { ...entry.props() }, attachTo: document.body })
      await flushPromises()
      checkExpectation(wrapper.element as HTMLElement, entry.expect)
      wrapper.unmount()
    })
  }
})
