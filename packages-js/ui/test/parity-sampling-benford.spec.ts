// Gemeinsame Paritätsfälle (ui-core/test/parity/cases-sampling.ts,
// cases-benford.ts) gegen die Vue-Fassung; die React-Fassung prüft dieselben
// Fälle und vergleicht zusätzlich das DOM.
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, it } from 'vitest'
import type { Component } from 'vue'
import type { ParityCase } from '../../ui-core/test/parity/cases'
import { benfordCases } from '../../ui-core/test/parity/cases-benford'
import { samplingCases } from '../../ui-core/test/parity/cases-sampling'
import { checkExpectation } from '../../ui-core/test/parity/expect'
import BenfordPanel from '../src/benford/BenfordPanel.vue'
import SamplingPanel from '../src/sampling/SamplingPanel.vue'

afterEach(() => {
  document.body.innerHTML = ''
})

function suite<P extends object>(title: string, component: Component, cases: ReadonlyArray<ParityCase<P>>): void {
  describe(title, () => {
    for (const entry of cases) {
      it(entry.name, async () => {
        const wrapper = mount(component, { props: { ...entry.props() }, attachTo: document.body })
        await flushPromises()
        checkExpectation(wrapper.element as HTMLElement, entry.expect)
        wrapper.unmount()
      })
    }
  })
}

suite('Paritätsfälle Stichprobe (Vue)', SamplingPanel, samplingCases)
suite('Paritätsfälle Benford (Vue)', BenfordPanel, benfordCases)
