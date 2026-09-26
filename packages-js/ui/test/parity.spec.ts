// Gemeinsame Paritätsfälle (ui-core/test/parity) gegen die Vue-Fassung; die
// React-Fassung prüft dieselben Fälle und vergleicht zusätzlich das DOM.
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, it } from 'vitest'
import type { Component } from 'vue'
import { synopsisCases, tableCases, type ParityCase } from '../../ui-core/test/parity/cases'
import { buttonCases, textFieldCases } from '../../ui-core/test/parity/cases-base'
import { vvtCases } from '../../ui-core/test/parity/cases-vvt'
import { checkExpectation } from '../../ui-core/test/parity/expect'
import { FaButton, FaSynopsis, FaTable, FaTextField, FaVvt } from '../src'

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

suite('Paritätsfälle Synopse (Vue)', FaSynopsis, synopsisCases)
suite('Paritätsfälle Tabelle (Vue)', FaTable, tableCases)
suite('Paritätsfälle VVT (Vue)', FaVvt, vvtCases)
suite('Paritätsfälle Schaltfläche (Vue)', FaButton, buttonCases)
suite('Paritätsfälle Eingabefeld (Vue)', FaTextField, textFieldCases)
