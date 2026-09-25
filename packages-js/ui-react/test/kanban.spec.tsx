import { act } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest'
import { MemoryBoardPort, SCHEMA_VERSION, type Board } from '@flowaudit/kanban-core'
import { FlowauditKanbanBoard, FlowauditKanbanBoards, defineFlowauditElements } from '../src'

;(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true

const board: Board = {
  schema_version: SCHEMA_VERSION, id: 'b1', title: 'Prüfung 2026', icon: '📋', owner_id: 'owner', version: 1, pinned: false, archived: false, created_at: '', updated_at: '',
  columns: [{ id: 'offen', label: 'Offen', color: '#7c3aed', wip_limit: null, done: false, status_aliases: [] }, { id: 'fertig', label: 'Erledigt', color: '#10b981', wip_limit: null, done: false, status_aliases: [] }],
  cards: [{ id: 'a', column_id: 'offen', rank: 'V', title: 'Belegliste', description: '', priority: 'mittel', tags: [], assignees: [], due: null, color: null, image: null, badge: null, checklist: [], links: [], attachments: [], created_at: '', updated_at: '', extra: {} }],
  labels: [], shares: [], transitions: { mode: 'free', allowed: [], locked_columns: [], fixed_order_columns: [] }, wip_mode: 'block', extra: {},
}

let root: Root | null = null
let host: HTMLElement
const flush = () => new Promise((resolve) => setTimeout(resolve, 5))

beforeAll(() => defineFlowauditElements())
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

describe('React-Hüllen für Kanban', () => {
  it('bearbeitet ein übergebenes Board und meldet Änderungen', async () => {
    const onChange = vi.fn()
    render(<FlowauditKanbanBoard board={board} userId="owner" today="2026-09-25" onBoardChange={onChange} />)
    await act(flush)
    await act(flush)
    const element = host.querySelector('flowaudit-kanban-board') as HTMLElement
    expect(element.querySelectorAll('[data-card-id]')).toHaveLength(1)
    element.querySelector<HTMLElement>('.fa-kanban-card__check')?.click()
    await act(flush)
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ version: 2 }), expect.any(CustomEvent))
    expect(element.querySelector('[data-column-id="fertig"] [data-card-id="a"]')).not.toBeNull()
  })

  it('zeigt die Boardliste eines Ports und meldet die Auswahl', async () => {
    const onSelect = vi.fn()
    const port = new MemoryBoardPort({ userId: 'owner', boards: [board] })
    render(<FlowauditKanbanBoards port={port} onBoardSelect={onSelect} />)
    await act(flush)
    await act(flush)
    const open = host.querySelector<HTMLElement>('.fa-kanban-boards__open')
    expect(open?.textContent).toContain('Prüfung 2026')
    open?.click()
    expect(onSelect).toHaveBeenCalledWith('b1', expect.any(CustomEvent))
  })
})
