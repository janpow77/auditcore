import { afterEach, describe, expect, it } from 'vitest'
import { defineFlowauditElements } from '../../src/elements'
import { board, flush, port } from './fixtures'

afterEach(() => {
  document.body.innerHTML = ''
})

describe('<flowaudit-kanban-board>', () => {
  it('rendert mit Port-Eigenschaft im Light DOM und sendet card-open', async () => {
    defineFlowauditElements({ only: ['flowaudit-kanban-board'] })
    const element = document.createElement('flowaudit-kanban-board') as HTMLElement & Record<string, unknown>
    element.port = port()
    element.boardId = 'b1'
    element.today = '2026-09-25'
    document.body.append(element)
    await flush()
    await flush()
    expect(element.shadowRoot).toBeNull()
    expect(element.querySelectorAll('[data-column-id]')).toHaveLength(3)
    const opened: unknown[] = []
    element.addEventListener('card-open', (event) => opened.push((event as CustomEvent<unknown[]>).detail[0]))
    element.querySelector<HTMLElement>('[data-card-id="a"]')?.click()
    expect(opened).toEqual([expect.objectContaining({ id: 'a' })])
  })

  it('bearbeitet ein Board ohne Port lokal und meldet board-change', async () => {
    defineFlowauditElements({ only: ['flowaudit-kanban-board', 'flowaudit-kanban-boards'] })
    const element = document.createElement('flowaudit-kanban-board') as HTMLElement & Record<string, unknown>
    element.board = board()
    element.userId = 'owner'
    const changes: unknown[] = []
    element.addEventListener('board-change', (event) => changes.push((event as CustomEvent<unknown[]>).detail[0]))
    document.body.append(element)
    await flush()
    await flush()
    element.querySelector<HTMLElement>('[data-card-id="a"] .fa-kanban-card__check')?.click()
    await flush()
    expect(changes).toEqual([expect.objectContaining({ version: 2 })])
  })
})
