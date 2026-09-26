// Gemeinsame Paritätsfälle (ui-core/test/parity/cases-batchchecks.ts) gegen
// die Vue-Fassung; die React-Fassung prüft dieselben Fälle und vergleicht
// zusätzlich das DOM.
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, it } from 'vitest'
import { batchchecksCases } from '../../ui-core/test/parity/cases-batchchecks'
import { checkExpectation } from '../../ui-core/test/parity/expect'
import BatchChecks from '../src/batchchecks/BatchChecks.vue'

afterEach(() => {
  document.body.innerHTML = ''
})

describe('Paritätsfälle BatchChecks (Vue)', () => {
  for (const entry of batchchecksCases) {
    it(entry.name, async () => {
      const wrapper = mount(BatchChecks, { props: { ...entry.props() }, attachTo: document.body })
      await flushPromises()
      checkExpectation(wrapper.element as HTMLElement, entry.expect)
      wrapper.unmount()
    })
  }
})
