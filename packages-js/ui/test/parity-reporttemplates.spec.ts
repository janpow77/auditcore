// Gemeinsame Paritätsfälle (ui-core/test/parity/cases-reporttemplates.ts) gegen
// die Vue-Fassung; die React-Fassung prüft dieselben Fälle und vergleicht
// zusätzlich das DOM.
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, it } from 'vitest'
import { reporttemplatesCases } from '../../ui-core/test/parity/cases-reporttemplates'
import { checkExpectation } from '../../ui-core/test/parity/expect'
import ReportTemplates from '../src/reporttemplates/ReportTemplates.vue'

afterEach(() => {
  document.body.innerHTML = ''
})

describe('Paritätsfälle ReportTemplates (Vue)', () => {
  for (const entry of reporttemplatesCases) {
    it(entry.name, async () => {
      const wrapper = mount(ReportTemplates, { props: { ...entry.props() }, attachTo: document.body })
      await flushPromises()
      checkExpectation(wrapper.element as HTMLElement, entry.expect)
      wrapper.unmount()
    })
  }
})
