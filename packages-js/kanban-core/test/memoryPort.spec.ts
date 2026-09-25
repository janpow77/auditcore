import { describe, expect, it } from 'vitest'
import { MemoryBoardPort } from '../src'
import { board } from './fixtures'

describe('MemoryBoardPort', () => {
  const users = [{ id: 'owner', name: 'Anna Becker' }, { id: 'editor', name: 'Markus Weber', email: 'mw@example.invalid' }, { id: 'neu', name: 'Tobias Keller' }]

  it('wendet Befehle an, protokolliert Ereignisse und isoliert Kopien', async () => {
    const port = new MemoryBoardPort({ userId: 'owner', boards: [board()], users, clock: () => '2026-09-25T12:00:00Z' })
    const loaded = await port.load('b1')
    loaded.cards.length = 0
    const moved = await port.moveCard('b1', 'a', 'erledigt', {})
    expect(moved.board.cards).toHaveLength(3)
    expect((await port.events('b1')).map((event) => event.kind)).toEqual(['card.moved'])
    expect((await port.events('b1', 99))).toEqual([])
  })

  it('prüft Nutzer beim Teilen, sucht Personen und listet sichtbare Boards', async () => {
    const port = new MemoryBoardPort({ userId: 'owner', boards: [board()], users })
    await expect(port.share('b1', 'unbekannt', 'read')).rejects.toMatchObject({ code: 'USER_NOT_FOUND' })
    await port.share('b1', 'neu', 'read')
    expect((await port.searchUsers('mw@'))[0]?.id).toBe('editor')
    port.switchUser('neu')
    const listed = await port.listBoards()
    expect(listed).toEqual([expect.objectContaining({ id: 'b1', role: 'read' })])
    await expect(port.deleteBoard('b1')).rejects.toMatchObject({ code: 'FORBIDDEN' })
    await expect(port.load('fehlt')).rejects.toMatchObject({ code: 'BOARD_NOT_FOUND' })
  })

  it('legt Boards aus Vorlagen an', async () => {
    const port = new MemoryBoardPort({ userId: 'owner', users, newId: () => 'neu-board' })
    const created = await port.createBoard('Sprint 12', '🏃', 'sprint')
    expect(created.columns.map((column) => column.id)).toContain('review')
    await expect(port.createBoard('Doppelt', '📋')).rejects.toMatchObject({ code: 'BOARD_EXISTS' })
    await port.deleteBoard('neu-board')
    expect(await port.listBoards()).toEqual([])
  })
})
