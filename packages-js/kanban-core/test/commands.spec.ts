import { describe, expect, it } from 'vitest'
import {
  boardStats,
  cardsIn,
  configureColumns,
  createBoard,
  createCard,
  deleteCard,
  findTemplate,
  KanbanError,
  moveCard,
  respreadColumn,
  revokeShare,
  shareBoard,
  TEMPLATES,
  updateBoard,
  updateCard,
} from '../src'
import { board, card, ctx } from './fixtures'

const ids = (value: ReturnType<typeof board>, column: string) => cardsIn(value, column).map((entry) => entry.id)

describe('Kartenbefehle', () => {
  it('legt Karten an und erhöht die Version', () => {
    const result = createCard(board(), ctx('editor'), { title: '  Neue Aufgabe ', column_id: 'offen', tags: ['VP'] })
    expect(result.card?.title).toBe('Neue Aufgabe')
    expect(ids(result.board, 'offen')).toEqual(['a', 'b', 'neu'])
    expect(result.board.version).toBe(2)
    expect(result.changes[0]?.kind).toBe('card.created')
  })

  it('verbietet Lesern das Anlegen und meldet Unbeteiligten NOT_VISIBLE', () => {
    expect(() => createCard(board(), ctx('reader'), { title: 'x' })).toThrowError(expect.objectContaining({ code: 'FORBIDDEN' }))
    expect(() => createCard(board(), ctx('fremd'), { title: 'x' })).toThrowError(expect.objectContaining({ code: 'NOT_VISIBLE' }))
  })

  it('verschiebt mit WIP-Grenze und liefert im Warnmodus eine Warnung', () => {
    const full = board({ cards: [...board().cards, card('d', 'in_arbeit', 'k')] })
    expect(() => moveCard(full, ctx(), 'a', 'in_arbeit')).toThrowError(expect.objectContaining({ code: 'WIP_LIMIT_REACHED', status: 409 }))
    const warned = moveCard({ ...full, wip_mode: 'warn' }, ctx(), 'a', 'in_arbeit')
    expect(warned.warnings).toEqual(['WIP_LIMIT_REACHED'])
  })

  it('ändert Felder und verschiebt bei neuer Spalte ans Ende', () => {
    const result = updateCard(board(), ctx(), 'a', { column_id: 'erledigt', priority: 'hoch', due: '2026-10-01T09:00Z' })
    expect(result.card).toMatchObject({ column_id: 'erledigt', priority: 'hoch', due: '2026-10-01T09:00:00+00:00' })
    expect(result.changes.map((change) => change.kind)).toEqual(['card.moved', 'card.updated'])
    expect(result.board.version).toBe(2)
  })

  it('löscht Karten und meldet unbekannte Karten', () => {
    expect(ids(deleteCard(board(), ctx(), 'a').board, 'offen')).toEqual(['b'])
    expect(() => deleteCard(board(), ctx(), 'zz')).toThrow(KanbanError)
  })

  it('verteilt eine Spalte neu, ohne die Reihenfolge zu ändern', () => {
    const result = respreadColumn(board(), ctx(), 'offen')
    expect(ids(result.board, 'offen')).toEqual(['a', 'b'])
    expect(() => respreadColumn(board(), ctx(), 'nix')).toThrowError(expect.objectContaining({ code: 'UNKNOWN_COLUMN' }))
  })
})

describe('Board-Befehle', () => {
  it('legt Boards aus Vorlagen an', () => {
    const template = findTemplate('cockpit-auftraege')
    const created = createBoard(ctx('u1'), 'neu', 'Aufträge', '🤖', template).board
    expect(created.owner_id).toBe('u1')
    expect(created.columns.map((column) => column.id)).toEqual(['eingang', 'geplant', 'laeuft', 'rueckfrage', 'fertig'])
    expect(created.transitions.locked_columns).toEqual(['laeuft'])
    expect(TEMPLATES).toHaveLength(8)
    expect(createBoard(ctx(), 'x').board.columns).toHaveLength(3)
  })

  it('benennt um (auch Bearbeiter) und heftet an (nur Eigentümer)', () => {
    expect(updateBoard(board(), ctx('editor'), { title: 'Neu' }).board.title).toBe('Neu')
    expect(() => updateBoard(board(), ctx('editor'), { pinned: true })).toThrowError(expect.objectContaining({ code: 'FORBIDDEN' }))
    expect(updateBoard(board(), ctx(), { pinned: true }).board.pinned).toBe(true)
  })

  it('verschiebt Karten entfernter Spalten in die erste Spalte', () => {
    const result = configureColumns(board(), ctx(), [board().columns[0]!, board().columns[2]!])
    expect(ids(result.board, 'offen')).toEqual(['a', 'b', 'c'])
    expect(result.changes[0]?.data).toEqual({ removed: ['in_arbeit'], moved_cards: ['c'] })
  })

  it('teilt als Upsert, verbietet Selbstfreigabe und erlaubt Empfängern den Austritt', () => {
    const shared = shareBoard(board(), ctx(), 'neu', 'read').board
    expect(shareBoard(shared, ctx(), 'neu', 'edit').board.shares.find((s) => s.user_id === 'neu')?.permission).toBe('edit')
    expect(() => shareBoard(board(), ctx(), 'owner', 'read')).toThrowError(expect.objectContaining({ code: 'SELF_SHARE' }))
    expect(() => shareBoard(board(), ctx(), 'x', 'write')).toThrowError(expect.objectContaining({ code: 'INVALID_PERMISSION' }))
    expect(revokeShare(board(), ctx('reader'), 'reader').board.shares).toHaveLength(1)
    expect(() => revokeShare(board(), ctx('reader'), 'editor')).toThrowError(expect.objectContaining({ code: 'FORBIDDEN' }))
  })

  it('berechnet den Fortschritt über die Erledigt-Spalte', () => {
    const done = moveCard(board(), ctx(), 'a', 'erledigt').board
    expect(boardStats(done)).toMatchObject({ total: 3, done: 1, done_column: 'erledigt', progress: 33 })
  })
})
