// Gemeinsame Paritätsfälle (ui-core/test/parity/cases-account.ts) gegen
// die Vue-Fassung; die React-Fassung prüft dieselben Fälle und vergleicht
// zusätzlich das DOM.
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, it } from 'vitest'
import { accountCases } from '../../ui-core/test/parity/cases-account'
import { checkExpectation } from '../../ui-core/test/parity/expect'
import AccountWorkspace from '../src/account/AccountWorkspace.vue'

afterEach(() => {
  document.body.innerHTML = ''
})

describe('Paritätsfälle AccountWorkspace (Vue)', () => {
  for (const entry of accountCases) {
    it(entry.name, async () => {
      const wrapper = mount(AccountWorkspace, { props: { ...entry.props() }, attachTo: document.body })
      await flushPromises()
      checkExpectation(wrapper.element as HTMLElement, entry.expect)
      wrapper.unmount()
    })
  }
})
