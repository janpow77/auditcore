// Gemeinsame Paritätsfälle (ui-core/test/parity/cases-tabular.ts) gegen die
// Vue-Fassung; die React-Fassung prüft dieselben Fälle und vergleicht
// zusätzlich das DOM.
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, it } from 'vitest'
import { tabularCases } from '../../ui-core/test/parity/cases-tabular'
import { checkExpectation } from '../../ui-core/test/parity/expect'
import TableImport from '../src/tabular/TableImport.vue'

afterEach(() => {
  document.body.innerHTML = ''
})

describe('Paritätsfälle Datei-Import (Vue)', () => {
  for (const entry of tabularCases) {
    it(entry.name, async () => {
      const wrapper = mount(TableImport, { props: { ...entry.props() }, attachTo: document.body })
      await flushPromises()
      checkExpectation(wrapper.element as HTMLElement, entry.expect)
      wrapper.unmount()
    })
  }
})
