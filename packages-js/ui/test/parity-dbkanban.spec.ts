import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, it } from 'vitest'
import FaDbKanban from '../src/dbkanban/FaDbKanban.vue'
import { dbKanbanCases } from '../../ui-core/test/parity/cases-dbkanban'
import { checkExpectation } from '../../ui-core/test/parity/expect'

afterEach(() => {
  document.body.innerHTML = ''
})

/** Gemeinsame Paritätsfälle (ui-core/test/parity/cases-dbkanban.ts) mit der Vue-Fassung. */
describe('FaDbKanban – gemeinsame Paritätsfälle', () => {
  for (const entry of dbKanbanCases) {
    it(entry.name, async () => {
      const wrapper = mount(FaDbKanban, { props: entry.props(), attachTo: document.body })
      await flushPromises()
      checkExpectation(wrapper.element as HTMLElement, entry.expect)
      wrapper.unmount()
    })
  }
})
