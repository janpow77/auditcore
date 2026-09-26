// Gemeinsame Kanban-Paritätsfälle (kanban-core/test/parity) gegen die Vue-Fassung;
// die React-Fassung prüft dieselben Fälle und vergleicht zusätzlich das DOM.
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, it } from 'vitest'
import type { Component } from 'vue'
import { boardListCases, kanbanCases } from '../../kanban-core/test/parity/cases'
import type { ParityCase } from '../../kanban-core/test/parity/cases'
import { checkExpectation } from '../../ui-core/test/parity/expect'
import { KanbanBoard, KanbanBoardList } from '../src'

afterEach(() => {
  document.body.innerHTML = ''
})

function suite<P extends object>(title: string, component: Component, cases: ReadonlyArray<ParityCase<P>>): void {
  describe(title, () => {
    for (const entry of cases) {
      it(entry.name, async () => {
        const wrapper = mount(component, { props: { ...entry.props() }, attachTo: document.body })
        await flushPromises()
        await flushPromises()
        checkExpectation(wrapper.element as HTMLElement, entry.expect)
        wrapper.unmount()
      })
    }
  })
}

suite('Paritätsfälle Kanban-Board (Vue)', KanbanBoard, kanbanCases)
suite('Paritätsfälle Kanban-Boardliste (Vue)', KanbanBoardList, boardListCases)
