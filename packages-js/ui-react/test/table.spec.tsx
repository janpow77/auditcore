import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { TableColumn } from '@auditcore/common'
import { FlowauditTable } from '../src'

afterEach(cleanup)

const rows = [
  { id: 'a', name: 'Übergang', betrag: 10 },
  { id: 'b', name: 'Antrag', betrag: null },
  { id: 'c', name: 'Zahlung', betrag: 2 },
]
const columns: TableColumn[] = [
  { key: 'name', label: 'Name', sortable: true },
  { key: 'betrag', label: 'Betrag', sortable: true, align: 'end', format: (v) => (v === null ? '–' : `${String(v)} €`) },
]

describe('FlowauditTable (nativ)', () => {
  it('rendert formatierte Zellen, sortiert per Klick und setzt aria-sort', () => {
    const onSortChange = vi.fn()
    const { container } = render(<FlowauditTable columns={columns} rows={rows} caption="Belege" onSortChange={onSortChange} />)
    expect(screen.getByRole('table', { name: 'Belege' })).toBeTruthy()
    expect(container.querySelectorAll('tbody tr')[1]?.textContent).toContain('–')
    fireEvent.click(screen.getByRole('button', { name: 'Nach Betrag sortieren' }))
    expect(container.querySelectorAll('th')[1]?.getAttribute('aria-sort')).toBe('ascending')
    expect(onSortChange).toHaveBeenCalledWith({ key: 'betrag', direction: 'asc' })
    expect(container.querySelectorAll('tbody tr')[0]?.textContent).toContain('Zahlung')
  })

  it('zeigt einen Leertext und meldet Zeilenklicks per Tastatur, gesteuerte Sortierung', () => {
    const { container, unmount } = render(<FlowauditTable columns={columns} rows={[]} />)
    expect(container.textContent).toContain('Keine Einträge')
    unmount()
    const onRowClick = vi.fn()
    const view = render(<FlowauditTable columns={columns} rows={rows} clickable locale="en" sort={{ key: 'name', direction: 'desc' }} onRowClick={onRowClick} />)
    fireEvent.keyDown(view.container.querySelectorAll('tbody tr')[0] as HTMLElement, { key: 'Enter' })
    expect(onRowClick).toHaveBeenCalledWith(rows[2])
    expect(screen.getAllByRole('button')[0]?.getAttribute('aria-label')).toBe('Sort by Name')
    fireEvent.click(screen.getByRole('button', { name: 'Sort by Name' }))
    expect(view.container.querySelectorAll('th')[0]?.getAttribute('aria-sort')).toBe('descending')
  })

  it('rendert eigene Zellen', () => {
    render(<FlowauditTable columns={columns} rows={rows} renderCell={(column, row) => (column.key === 'name' ? <strong>{String(row.name)}</strong> : undefined)} />)
    expect(screen.getByText('Antrag').tagName).toBe('STRONG')
  })
})
