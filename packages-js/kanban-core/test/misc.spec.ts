import { describe, expect, it } from 'vitest'
import {
  boardFromJson,
  boardToJson,
  capabilities,
  columnForStatus,
  findTemplate,
  groupByValue,
  isFilterActive,
  KanbanError,
  movableTargets,
  normalizeDue,
  slugify,
  todayIso,
  uniqueColumnId,
  wipStates,
} from '../src'
import { board, card } from './fixtures'

describe('Serialisierung', () => {
  it('liest geschriebene Boards verlustfrei zurück', () => {
    const value = board({ cards: [card('z', 'offen', 'k'), card('y', 'offen', 'V')] })
    const json = JSON.parse(JSON.stringify(boardToJson(value)))
    expect(json.cards.map((entry: { id: string }) => entry.id)).toEqual(['y', 'z'])
    expect(boardFromJson(json)).toEqual({ ...value, cards: [value.cards[1], value.cards[0]] })
  })

  it('meldet fehlerhafte Dokumente mit Pfad', () => {
    expect(() => boardFromJson({ ...boardToJson(board()), columns: [] })).toThrowError(/mindestens eine Spalte/)
    expect(() => boardFromJson({ ...boardToJson(board()), wip_mode: 'x' })).toThrowError(KanbanError)
    expect(() => boardFromJson({ ...boardToJson(board()), schema_version: 'v0' })).toThrowError(/Formatversion/)
  })
})

describe('Hilfen', () => {
  it('bildet Spalten-IDs aus Beschriftungen', () => {
    expect(slugify('Prüfung – Größe')).toBe('pruefung_groesse')
    expect(uniqueColumnId('Neue Spalte', ['neue_spalte', 'neue_spalte_2'])).toBe('neue_spalte_3')
    expect(uniqueColumnId('!!!', [])).toBe('spalte')
  })

  it('normalisiert Fristen wie Python isoformat', () => {
    expect(normalizeDue('2026-09-30T10:00:00.500Z')).toBe('2026-09-30T10:00:00.500000+00:00')
    expect(normalizeDue('2026-09-30 08:15+0200')).toBe('2026-09-30T08:15:00+02:00')
    expect(() => normalizeDue('2026-02-30')).toThrowError(/Deadline/)
    expect(normalizeDue(null)).toBeNull()
  })

  it('ordnet externe Status Spalten zu und kennt erlaubte Ziele', () => {
    const cockpit = { ...board(), ...findTemplate('cockpit-auftraege')!, cards: [card('x', 'eingang', 'V'), card('y', 'laeuft', 'V')] }
    expect(columnForStatus(cockpit, 'unterbrochen')?.id).toBe('rueckfrage')
    expect(movableTargets(cockpit, cockpit.cards[0]!)).toEqual(['geplant'])
    expect(movableTargets(cockpit, cockpit.cards[1]!)).toEqual([])
  })

  it('liefert Rechte je Rolle, WIP-Zustände und Gruppen', () => {
    expect(capabilities(board(), 'reader')).toMatchObject({ read: true, move_card: false })
    expect(capabilities(board(), 'owner').configure).toBe(true)
    expect(wipStates(board()).find((state) => state.column_id === 'in_arbeit')).toMatchObject({ count: 1, limit: 2, full: false })
    expect(groupByValue(['a', 'b', 'x'], (v) => v, ['a', 'b'])).toEqual([['', ['x']], ['a', ['a']], ['b', ['b']]])
    expect(isFilterActive({ query: '  ' })).toBe(false)
    expect(isFilterActive({ priorities: ['hoch'] })).toBe(true)
    expect(todayIso(new Date(2026, 8, 5))).toBe('2026-09-05')
  })
})
