// Gemeinsame Paritätsfälle (ui-core/test/parity/cases-reporting.ts) gegen die
// Vue-Fassung; die React-Fassung prüft dieselben Fälle und vergleicht das DOM.
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, it } from 'vitest'
import { reportingCases } from '../../ui-core/test/parity/cases-reporting'
import { checkExpectation } from '../../ui-core/test/parity/expect'
import ReportExportPanel from '../src/reporting/ReportExportPanel.vue'

afterEach(() => {
  document.body.innerHTML = ''
})

describe('Paritätsfälle Tabellenexport (Vue)', () => {
  for (const entry of reportingCases) {
    it(entry.name, async () => {
      const wrapper = mount(ReportExportPanel, { props: { ...entry.props() }, attachTo: document.body })
      await flushPromises()
      checkExpectation(wrapper.element as HTMLElement, entry.expect)
      wrapper.unmount()
    })
  }
})
