// Gemeinsame Paritätsfälle (ui-core/test/parity/cases-identifiers.ts) gegen die
// Vue-Fassung; die React-Fassung prüft dieselben Fälle und vergleicht das DOM.
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, it } from 'vitest'
import { identifierCases } from '../../ui-core/test/parity/cases-identifiers'
import { checkExpectation } from '../../ui-core/test/parity/expect'
import IdentifierCheck from '../src/identifiers/IdentifierCheck.vue'

afterEach(() => {
  document.body.innerHTML = ''
})

describe('Paritätsfälle Kennung prüfen (Vue)', () => {
  for (const entry of identifierCases) {
    it(entry.name, async () => {
      const wrapper = mount(IdentifierCheck, { props: { ...entry.props() }, attachTo: document.body })
      await flushPromises()
      checkExpectation(wrapper.element as HTMLElement, entry.expect)
      wrapper.unmount()
    })
  }
})
