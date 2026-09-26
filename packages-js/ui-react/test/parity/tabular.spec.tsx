import { fireEvent as domEvent } from '@testing-library/dom'
import { fireEvent } from '@testing-library/react'
import { flushPromises } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import TableImport from '../../../ui/src/tabular/TableImport.vue'
import { formState, normalizeDom } from '../../../ui-core/test/parity/dom'
import { TABULAR_CSV, tabularCases } from '../../../ui-core/test/parity/cases-tabular'
import { TableImport as ReactTableImport } from '../../src/tabular/TableImport'
import { both } from './interact'
import { expectParity, renderBoth, tick, type Rendered } from './setup'

describe('Parität Datei-Import Vue ↔ React', () => {
  for (const entry of tabularCases) {
    it(entry.name, async () => {
      const rendered = await renderBoth(TableImport, { ...entry.props() }, <ReactTableImport {...entry.props()} />)
      expectParity(rendered, entry.expect)
    })
  }
})

async function upload(rendered: Rendered, file: File): Promise<void> {
  for (const [root, events] of [[rendered.vue, domEvent], [rendered.react, fireEvent]] as const) {
    const input = root.querySelector('input[type="file"]') as HTMLInputElement
    Object.defineProperty(input, 'files', { value: [file], configurable: true })
    events.change(input)
    for (let i = 0; i < 3; i += 1) {
      await flushPromises()
      await tick()
    }
  }
  expect(normalizeDom(rendered.react)).toBe(normalizeDom(rendered.vue))
  expect(formState(rendered.react)).toEqual(formState(rendered.vue))
}

describe('Parität Datei-Import nach Interaktion', () => {
  it('Datei laden, Spalten wählen, Dezimalpunkt, Kopfzeile', async () => {
    const rendered = await renderBoth(TableImport, { mode: 'items' }, <ReactTableImport mode="items" />)
    await upload(rendered, new File([TABULAR_CSV], 'belege.csv', { type: 'text/csv' }))
    expect(rendered.react.querySelector('.fa-import__note')?.textContent).toContain('belege.csv')
    const select = (index: number) => (root: HTMLElement) => root.querySelectorAll('select')[index]
    await both(rendered, select(0), { kind: 'change', value: '1' })
    await both(rendered, select(1), { kind: 'change', value: '0' })
    await both(rendered, select(2), { kind: 'change', value: '2' })
    await both(rendered, select(3), { kind: 'change', value: '.' })
    await both(rendered, (root) => root.querySelector('input[type="checkbox"]'), { kind: 'click' })
    expect(rendered.react.querySelectorAll('select')).toHaveLength(4)
  })
})
