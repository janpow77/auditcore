import { describe, expect, it, vi } from 'vitest'
import { boardToJson, KanbanError, RestBoardPort } from '../src'
import { board, card } from './fixtures'

function reply(status: number, body: unknown): Response {
  return new Response(body === null ? null : JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

function setup(...responses: Response[]) {
  const fetch = vi.fn(async () => responses.shift() ?? reply(500, {}))
  const port = new RestBoardPort({ baseUrl: '/api/kanban/', userId: 'owner', fetch, headers: { 'X-CSRF': 't' } })
  return { fetch, port }
}

const call = (fetch: ReturnType<typeof vi.fn>, index: number) => fetch.mock.calls[index] as unknown as [string, RequestInit]

describe('RestBoardPort', () => {
  it('lädt Boards und schickt Verschiebungen mit erwarteter Version', async () => {
    const moved = { ...card('a', 'erledigt', 'k'), updated_at: 'jetzt' }
    const { fetch, port } = setup(reply(200, { board: boardToJson(board()), role: 'owner' }), reply(200, { version: 2, card: moved, changed_cards: [], warnings: [], events: [] }))
    const loaded = await port.load('b1')
    expect(loaded.cards).toHaveLength(3)
    const result = await port.moveCard('b1', 'a', 'erledigt', { after_id: 'x' })
    expect(call(fetch, 1)[0]).toBe('/api/kanban/boards/b1/cards/a/move')
    expect(JSON.parse(String(call(fetch, 1)[1].body))).toEqual({ column_id: 'erledigt', after_id: 'x', expected_version: 1 })
    expect(call(fetch, 1)[1].headers).toMatchObject({ 'X-CSRF': 't', 'Content-Type': 'application/json' })
    expect(result.board.version).toBe(2)
    expect(result.board.cards.find((entry) => entry.id === 'a')?.column_id).toBe('erledigt')
  })

  it('führt neue und neu verteilte Karten ein und entfernt gelöschte', async () => {
    const { port } = setup(
      reply(200, { board: boardToJson(board()) }),
      reply(201, { version: 2, card: card('neu', 'offen', 's'), changed_cards: [{ ...card('a', 'offen', 'F') }], warnings: ['WIP_LIMIT_REACHED'], events: [] }),
      reply(200, { version: 3, card: null, changed_cards: [], warnings: [], events: [] }),
    )
    await port.load('b1')
    const created = await port.createCard('b1', { title: 'Neu' })
    expect(created.warnings).toEqual(['WIP_LIMIT_REACHED'])
    expect(created.board.cards.map((entry) => `${entry.id}:${entry.rank}`)).toContain('a:F')
    const removed = await port.deleteCard('b1', 'neu')
    expect(removed.board.cards.some((entry) => entry.id === 'neu')).toBe(false)
    expect(removed.board.version).toBe(3)
  })

  it('übersetzt Fehlerkörper in KanbanError und lädt nach dem Teilen neu', async () => {
    const { fetch, port } = setup(
      reply(409, { error: { code: 'VERSION_CONFLICT', message: 'Board wurde geändert' } }),
      reply(502, null),
      reply(200, { version: 5, card: null, changed_cards: [], warnings: [], events: [] }),
      reply(200, { board: boardToJson(board({ version: 5 })) }),
    )
    await expect(port.updateBoard('b1', { title: 'x' })).rejects.toMatchObject({ code: 'VERSION_CONFLICT', status: 409 })
    await expect(port.load('b1')).rejects.toBeInstanceOf(KanbanError)
    const shared = await port.share('b1', 'neu', 'edit')
    expect(call(fetch, 2)[0]).toBe('/api/kanban/boards/b1/shares/neu')
    expect(call(fetch, 2)[1].method).toBe('PUT')
    expect(shared.board.version).toBe(5)
  })

  it('listet Boards, legt an, löscht und liest Ereignisse', async () => {
    const { fetch, port } = setup(
      reply(200, { boards: [{ id: 'b1', title: 'A', icon: '📋', pinned: false, updated_at: '', owner_id: 'owner', role: 'owner', stats: { total: 0, done: 0, progress: 0 } }] }),
      reply(201, { board: boardToJson(board({ id: 'b2' })) }),
      reply(204, null),
      reply(200, { events: [{ seq: 1, board_id: 'b1', version: 1, kind: 'board.created', actor: 'owner', at: '', card_id: null, data: {} }] }),
    )
    expect((await port.listBoards())[0]?.role).toBe('owner')
    expect((await port.createBoard('B', '📋', 'sprint')).id).toBe('b2')
    expect(JSON.parse(String(call(fetch, 1)[1].body))).toEqual({ title: 'B', icon: '📋', template: 'sprint' })
    await port.deleteBoard('b2')
    expect((await port.events('b1', 0))[0]?.kind).toBe('board.created')
    expect(call(fetch, 3)[0]).toBe('/api/kanban/boards/b1/events?since=0')
  })
})
