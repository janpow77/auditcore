import { act, createRef } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest'
import type { TableColumn, TableRow } from '@flowaudit/common'
import { createElementComponent, defineFlowauditElements, eventPayload } from '../src/elements'

// Allgemeiner Mechanismus der (veralteten) Hüllen, geprüft an <flowaudit-table>.
const FlowauditTable = createElementComponent<{ columns: readonly TableColumn[]; rows: readonly TableRow[]; clickable?: boolean }, { onRowClick: string; onSortChange: string }>(
  'flowaudit-table',
  { properties: ['columns', 'rows', 'clickable'], events: { onRowClick: 'row-click', onSortChange: 'sort-change' } },
)

// React 18: act() braucht diese Kennzeichnung außerhalb von Testbibliotheken.
;(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true

let root: Root | null = null
let host: HTMLElement

beforeAll(() => {
  defineFlowauditElements()
})

afterEach(() => {
  act(() => root?.unmount())
  root = null
  document.body.innerHTML = ''
})

function render(node: React.ReactNode): void {
  host = document.createElement('div')
  document.body.append(host)
  root = createRoot(host)
  act(() => root?.render(node))
}

const flush = () => new Promise((resolve) => setTimeout(resolve, 0))

describe('React-Hüllen', () => {
  it('setzt Objekte als Eigenschaften und leitet Ereignisse weiter', async () => {
    const onRowClick = vi.fn()
    const ref = createRef<HTMLElement | null>()
    render(
      <FlowauditTable
        ref={ref}
        className="tabelle"
        columns={[{ key: 'name', label: 'Name' }]}
        rows={[{ id: 1, name: 'Vorhaben A' }]}
        clickable
        onRowClick={onRowClick}
      />,
    )
    await act(flush)
    const element = host.querySelector('flowaudit-table') as HTMLElement & Record<string, unknown>
    expect(ref.current).toBe(element)
    expect(element.className).toBe('tabelle')
    expect(Array.isArray(element.rows)).toBe(true)
    expect(element.querySelector('td')?.textContent).toBe('Vorhaben A')
    element.querySelector('tbody tr')?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    expect(onRowClick).toHaveBeenCalledWith({ id: 1, name: 'Vorhaben A' }, expect.any(CustomEvent))
  })

  it('aktualisiert Eigenschaften bei neuem Render und entfernt Listener beim Aushängen', async () => {
    const onRowClick = vi.fn()
    const columns = [{ key: 'name', label: 'Name' }]
    render(<FlowauditTable columns={columns} rows={[{ id: 1, name: 'A' }]} clickable onRowClick={onRowClick} />)
    await act(flush)
    act(() => root?.render(<FlowauditTable columns={columns} rows={[{ id: 2, name: 'B' }]} clickable onRowClick={onRowClick} />))
    await act(flush)
    const element = host.querySelector('flowaudit-table') as HTMLElement
    expect(element.querySelector('td')?.textContent).toBe('B')
    const row = element.querySelector('tbody tr')
    act(() => root?.unmount())
    root = null
    row?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    expect(onRowClick).not.toHaveBeenCalled()
  })

  it('liest das erste emit-Argument und erzeugt Hüllen für beliebige Elemente', () => {
    expect(eventPayload(new CustomEvent('x', { detail: ['a', 'b'] }))).toBe('a')
    expect(eventPayload(new CustomEvent('x', { detail: 5 }))).toBe(5)
    const Probe = createElementComponent<{ value: number }, { onChange: string }>('flowaudit-probe', {
      properties: ['value'],
      events: { onChange: 'change' },
    })
    expect(Probe.displayName).toBe('flowaudit-probe')
  })
})
