import { act, cleanup, fireEvent, render, screen } from '@testing-library/react'
import { useState } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { RecordTable } from '@flowaudit/kanban-core'
import { recordPort, recordTable } from '../../ui-core/test/dbkanban/fixtures'
import { FlowauditDbKanban } from '../src'

const flush = () => act(() => new Promise<void>((resolve) => setTimeout(resolve, 0)))

afterEach(() => {
  cleanup()
  document.body.innerHTML = ''
})

function transfer(): DataTransfer {
  const data = new Map<string, string>()
  return { setData: (type: string, value: string) => data.set(type, value), getData: (type: string) => data.get(type) ?? '', effectAllowed: 'all' } as unknown as DataTransfer
}

const ids = (container: HTMLElement, column: string) => Array.from(container.querySelectorAll(`[data-column="${column}"] .fa-db-kanban-card`)).map((card) => card.getAttribute('data-card-id'))

describe('FlowauditDbKanban (nativ)', () => {
  it('verschiebt per Ziehen und Ablegen und meldet die Verschiebung', async () => {
    const port = recordPort()
    const onRecordMove = vi.fn()
    const { container } = render(<FlowauditDbKanban port={port} onRecordMove={onRecordMove} />)
    await flush()
    const dataTransfer = transfer()
    fireEvent.dragStart(container.querySelector('[data-card-id="r1"]') as Element, { dataTransfer })
    fireEvent.dragOver(container.querySelector('[data-column="erledigt"]') as Element, { dataTransfer })
    expect(container.querySelector('[data-column="erledigt"]')?.classList).toContain('fa-db-kanban-column--over')
    fireEvent.drop(container.querySelector('[data-column="erledigt"]') as Element, { dataTransfer })
    await flush()
    expect(port.updateCell).toHaveBeenCalledWith('r1', 'status', 'erledigt')
    expect(onRecordMove).toHaveBeenCalledWith({ rowId: 'r1', propertyId: 'status', value: 'erledigt' })
    expect(ids(container, 'erledigt')).toEqual(['r1', 'r2'])
    expect(screen.getByRole('status').textContent).toBe('„Vorhaben A“ nach „erledigt“ verschoben.')
  })

  it('verschiebt mit Strg+Pfeil und behält den Fokus', async () => {
    const port = recordPort()
    const { container } = render(<FlowauditDbKanban port={port} />)
    await flush()
    fireEvent.keyDown(container.querySelector('[data-card-id="r4"]') as Element, { key: 'ArrowRight', ctrlKey: true })
    await flush()
    await flush()
    expect(port.updateCell).toHaveBeenCalledWith('r4', 'status', 'erledigt')
    expect(document.activeElement?.getAttribute('data-card-id')).toBe('r4')
    fireEvent.keyDown(container.querySelector('[data-card-id="r4"]') as Element, { key: 'ArrowRight' })
    expect(port.updateCell).toHaveBeenCalledOnce()
  })

  it('arbeitet gesteuert auf einer Tabelle (groupBy, onTableChange)', async () => {
    const changes: RecordTable[] = []
    function Host() {
      const [table, setTable] = useState(recordTable)
      const [groupBy, setGroupBy] = useState('fonds')
      return <FlowauditDbKanban table={table} groupBy={groupBy} onGroupByChange={setGroupBy} onTableChange={(next) => { changes.push(next); setTable(next) }} />
    }
    const { container } = render(<Host />)
    await flush()
    expect(Array.from(container.querySelectorAll('.fa-db-kanban-column__name')).map((node) => node.textContent)).toEqual(['Ohne Wert', 'EFRE', 'ESF+', 'JTF'])
    fireEvent.keyDown(container.querySelector('[data-card-id="r2"]') as Element, { key: 'ArrowRight', ctrlKey: true })
    await flush()
    await flush()
    expect(changes[0]?.rows.find((row) => row.id === 'r2')?.cells.fonds).toBe('JTF')
    expect(ids(container, 'JTF')).toEqual(['r2'])
    fireEvent.change(container.querySelector('select') as HTMLSelectElement, { target: { value: 'status' } })
    await flush()
    expect(container.querySelectorAll('.fa-db-kanban-column')).toHaveLength(4)
    expect(container.querySelector('.fa-db-kanban-column__name')?.textContent).toBe('Ohne Wert')
  })

  it('nimmt eine Verschiebung bei Fehler zurück und meldet ihn', async () => {
    const port = recordPort({ updateCell: vi.fn(async () => Promise.reject(new TypeError('Failed to fetch'))) })
    const onError = vi.fn()
    const { container } = render(<FlowauditDbKanban port={port} onError={onError} />)
    await flush()
    fireEvent.keyDown(container.querySelector('[data-card-id="r1"]') as Element, { key: 'ArrowRight', ctrlKey: true })
    await flush()
    expect(screen.getByRole('alert').textContent).toBe('Keine Verbindung zur Datenquelle (Failed to fetch).')
    expect(ids(container, 'offen')).toEqual(['r1', 'r6'])
    expect(onError).toHaveBeenCalledOnce()
  })

  it('legt Einträge an und sperrt im Nur-Lese-Modus', async () => {
    const port = recordPort()
    const onRecordAdd = vi.fn()
    const { container, rerender } = render(<FlowauditDbKanban port={port} onRecordAdd={onRecordAdd} />)
    await flush()
    fireEvent.click(screen.getByRole('button', { name: 'Eintrag in „Ohne Wert“ hinzufügen' }))
    await flush()
    expect(port.addRow).toHaveBeenCalledWith({ status: null })
    expect(onRecordAdd).toHaveBeenCalledWith(expect.objectContaining({ id: 'neu-1' }))
    rerender(<FlowauditDbKanban port={port} editable={false} />)
    expect(container.querySelectorAll('[draggable="true"]')).toHaveLength(0)
    expect(container.textContent).toContain('Nur Lesezugriff')
  })
})
