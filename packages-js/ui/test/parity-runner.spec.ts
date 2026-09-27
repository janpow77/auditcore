// Gemeinsame Paritätsfälle (ui-core/test/parity/cases-runner.ts) gegen
// die Vue-Fassung; die React-Fassung prüft dieselben Fälle und vergleicht
// zusätzlich das DOM.
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, it } from 'vitest'
import { runnerCases } from '../../ui-core/test/parity/cases-runner'
import { checkExpectation } from '../../ui-core/test/parity/expect'
import RunnerConsole from '../src/runner/RunnerConsole.vue'

afterEach(() => {
  document.body.innerHTML = ''
})

describe('Paritätsfälle RunnerConsole (Vue)', () => {
  for (const entry of runnerCases) {
    it(entry.name, async () => {
      const wrapper = mount(RunnerConsole, { props: { ...entry.props() }, attachTo: document.body })
      await flushPromises()
      checkExpectation(wrapper.element as HTMLElement, entry.expect)
      wrapper.unmount()
    })
  }
})
