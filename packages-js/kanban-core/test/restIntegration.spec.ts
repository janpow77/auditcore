/**
 * Vertragsprüfung gegen den echten Python-Server (auditcore_kanban.rest.KanbanApi):
 *   python packages-js/ui/demo/kanban_api_server.py --port 18766 &
 *   KANBAN_API_URL=http://127.0.0.1:18766/api/kanban npm test -w packages-js/kanban-core
 * Ohne KANBAN_API_URL wird die Prüfung übersprungen (CI ohne Python-Server).
 */
import { describe, expect, it } from 'vitest'
import { cardsIn, KanbanError, RestBoardPort } from '../src'

const BASE = process.env.KANBAN_API_URL

function port(userId: string, optimisticLocking = true): RestBoardPort {
  return new RestBoardPort({ baseUrl: BASE ?? '', userId, optimisticLocking, headers: { 'X-Demo-User': userId } })
}

describe.skipIf(!BASE)('RestBoardPort gegen auditcore_kanban (Python)', () => {
  it('durchläuft den REST-Vertrag mit Rang, WIP, Rechten und Versionen', async () => {
    const anna = port('anna')
    const created = await anna.createBoard(`Integration ${Date.now()}`, '🔍', 'vorhabenpruefung')
    const id = created.id
    expect(created.columns.map((column) => column.id)).toContain('kontradiktorisch')
    await anna.load(id)
    for (const title of ['Stichprobe', 'Belegliste', 'Vergabe']) await anna.createCard(id, { title, column_id: 'auswahl' })
    let board = await anna.load(id)
    const [first, second, third] = cardsIn(board, 'auswahl')
    expect([first?.title, second?.title, third?.title]).toEqual(['Stichprobe', 'Belegliste', 'Vergabe'])
    const moved = await anna.moveCard(id, third!.id, 'auswahl', { before_id: first!.id })
    expect(cardsIn(moved.board, 'auswahl').map((card) => card.title)).toEqual(['Vergabe', 'Stichprobe', 'Belegliste'])

    board = await anna.load(id)
    const columns = board.columns.map((column) => (column.id === 'pruefung' ? { ...column, wip_limit: 1 } : column))
    await anna.configureColumns(id, columns)
    await anna.moveCard(id, first!.id, 'pruefung', {})
    await expect(anna.moveCard(id, second!.id, 'pruefung', {})).rejects.toMatchObject({ code: 'WIP_LIMIT_REACHED', status: 409 })

    const stale = port('anna')
    await stale.load(id)
    await anna.updateCard(id, second!.id, { priority: 'hoch', tags: ['EFRE'], due: '2026-10-01' })
    await expect(stale.updateCard(id, second!.id, { title: 'veraltet' })).rejects.toMatchObject({ code: 'VERSION_CONFLICT' })

    await anna.share(id, 'lena', 'read')
    const lena = port('lena')
    await lena.load(id)
    await expect(lena.createCard(id, { title: 'nein' })).rejects.toMatchObject({ code: 'FORBIDDEN', status: 403 })
    await expect(port('tobias').load(id)).rejects.toMatchObject({ code: 'NOT_VISIBLE', status: 404 })
    await expect(anna.share(id, 'unbekannt', 'read')).rejects.toBeInstanceOf(KanbanError)
    expect((await lena.listBoards()).find((entry) => entry.id === id)?.role).toBe('read')

    await anna.deleteCard(id, second!.id)
    const events = await anna.events(id, 0)
    expect(events.map((event) => event.kind)).toEqual(expect.arrayContaining(['card.created', 'card.moved', 'board.configured', 'share.created', 'card.deleted']))
    await anna.deleteBoard(id)
  })
})
