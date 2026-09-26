import { describe, expect, it, vi } from 'vitest'
import {
  EMPTY_FILTER,
  KanbanError,
  createBoardController,
  createBoardListController,
  createColumnEditor,
  createMoveController,
  createShareSearch,
  filterCriteria,
  previewColumns,
  selectBoardList,
  selectBoardView,
  selectColumnEditor,
  shareName,
  type BoardPort,
  type MoveTranslate,
} from '../src'
import { NOW, kanbanBoard, kanbanPort, USERS } from './parity/cases'

const t: MoveTranslate = (key, params) => `${key}:${JSON.stringify(params ?? {})}`
const flush = () => new Promise((resolve) => setTimeout(resolve, 0))

function setup(port: BoardPort = kanbanPort()) {
  const onChange = vi.fn()
  const onError = vi.fn()
  const board = createBoardController({ port: () => port, boardId: () => 'b1', onChange, onError })
  const view = () => selectBoardView(board.store.get(), { userId: port.userId, criteria: filterCriteria(EMPTY_FILTER), today: '2026-09-25' })
  const focusCard = vi.fn()
  const mover = createMoveController({ board, columns: () => view().columns, canMove: () => view().can.move, t: () => t, focusCard })
  return { board, view, mover, onChange, onError, focusCard }
}

const ids = (columns: ReturnType<typeof previewColumns>, column: string) => columns.find((entry) => entry.column.id === column)?.cards.map((card) => card.id)

describe('createBoardController', () => {
  it('lädt, leitet die Ansicht ab und wendet Änderungen optimistisch an', async () => {
    const { board, view, onChange } = setup()
    await board.load()
    expect(view().columns.map((entry) => entry.cards.length)).toEqual([2, 1, 1])
    expect(view().stats).toMatchObject({ done: 1, total: 4 })
    const pending = board.actions.move('b', 'fertig', {})
    expect(ids(view().columns, 'fertig')).toEqual(['d', 'b'])
    expect((await pending)?.board.version).toBe(2)
    expect(onChange).toHaveBeenCalledTimes(1)
  })

  it('rollt bei Ablehnung zurück und meldet den Fehler', async () => {
    const port = kanbanPort()
    port.moveCard = () => Promise.reject(new KanbanError('INVALID_REQUEST', 'abgelehnt'))
    const { board, view, onError } = setup(port)
    await board.load()
    expect(await board.actions.move('b', 'fertig', {})).toBeNull()
    expect(ids(view().columns, 'offen')).toEqual(['a', 'b'])
    expect(onError.mock.calls[0]?.[0].message).toBe('abgelehnt')
  })

  it('lädt nach einem Versionskonflikt neu und behält die Meldung', async () => {
    const port = kanbanPort()
    const load = vi.spyOn(port, 'load')
    port.updateCard = () => Promise.reject(new KanbanError('VERSION_CONFLICT', 'geändert'))
    const { board } = setup(port)
    await board.load()
    await board.actions.editCard('a', { title: 'x' })
    await flush()
    expect(load).toHaveBeenCalledTimes(2)
    expect(board.store.get().error?.code).toBe('VERSION_CONFLICT')
  })
})

describe('createMoveController', () => {
  it('nimmt auf, überspringt volle Spalten, legt ab und sagt an', async () => {
    const { board, view, mover, focusCard } = setup()
    await board.load()
    mover.grab(view().columns[0]!.cards[0]!)
    expect(mover.store.get().announcement).toContain('grabbed')
    mover.step(1, 0)
    expect(mover.store.get().preview?.columnId).toBe('fertig')
    expect(ids(previewColumns(view().columns, mover.store.get()), 'fertig')).toEqual(['a', 'd'])
    await mover.drop()
    expect(ids(view().columns, 'fertig')).toEqual(['a', 'd'])
    expect(mover.store.get().announcement).toMatch(/^dropped:/)
    expect(focusCard).toHaveBeenCalledWith('a')
  })

  it('bricht ab, verweigert unzulässige Ziele und verschiebt mit Strg+Pfeil', async () => {
    const { board, view, mover } = setup()
    await board.load()
    const first = view().columns[0]!.cards[0]!
    mover.grab(first)
    mover.cancel()
    expect(mover.store.get()).toMatchObject({ grabbed: null, preview: null })
    expect(mover.store.get().announcement).toMatch(/^cancelled:/)
    expect(await mover.commit('a', { cardId: 'a', columnId: 'arbeit', index: 0 })).toBe(false)
    expect(mover.store.get().announcement).toMatch(/^moveDenied:/)
    await mover.nudge(first, 0, 1)
    expect(ids(view().columns, 'offen')).toEqual(['b', 'a'])
  })
})

describe('Boardliste, Spalteneditor, Personensuche', () => {
  it('sortiert, heftet an und löscht', async () => {
    const other = kanbanBoard({ id: 'b2', title: 'Zweites', pinned: true, updated_at: '2026-01-01T00:00:00Z' })
    const port = kanbanPort('owner')
    await port.createBoard?.('x', '📋')
    const list = createBoardListController(() => port)
    await list.load()
    expect(selectBoardList(list.store.get()).own.length).toBeGreaterThan(0)
    const first = list.store.get().boards.find((entry) => entry.id === 'b1')!
    await list.togglePin(first)
    expect(selectBoardList(list.store.get()).own[0]?.id).toBe('b1')
    await list.remove(first)
    expect(list.store.get().boards.some((entry) => entry.id === 'b1')).toBe(false)
    expect(list.canCreate()).toBe(true)
    expect(other.pinned).toBe(true)
    expect(NOW).toBeGreaterThan(0)
  })

  it('bearbeitet Spalten und prüft sie', () => {
    const editor = createColumnEditor(4)
    editor.reset(kanbanBoard().columns)
    editor.add('Nachprüfung')
    const view = () => selectColumnEditor(editor.store.get(), 4)
    expect(view()).toMatchObject({ canAdd: false, dirty: true })
    editor.move(3, -1)
    editor.remove(0)
    expect(view().removed.map((column) => column.id)).toEqual(['offen'])
    editor.update(0, { label: ' ' })
    expect(editor.validated()).toBeNull()
    expect(editor.store.get().problem).not.toBe('')
  })

  it('verwirft späte Suchantworten und blendet Freigegebene aus', async () => {
    const search = createShareSearch()
    let resolveSlow: (users: typeof USERS[number][]) => void = () => undefined
    const slow = () => new Promise<typeof USERS[number][]>((resolve) => { resolveSlow = resolve })
    const first = search.query('Anna', slow, [])
    await search.query('e', async () => [...USERS], [{ user_id: 'leser', permission: 'read', shared_by: 'owner', created_at: null }])
    resolveSlow([USERS[0]!])
    await first
    expect(search.store.get().results.map((user) => user.id)).toEqual(['owner', 'neu'])
    expect(shareName('leser', search.store.get().known, [])).toBe('Lena Schmidt')
    expect(shareName('unbekannt', search.store.get().known, [])).toBe('unbekannt')
  })
})
