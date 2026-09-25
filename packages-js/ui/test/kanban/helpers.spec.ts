import { describe, expect, it } from 'vitest'
import { badgePrefix, badgeStyle, cardAge, initials, preview, relativeTime, textOn } from '../../src/kanban/cardView'
import { boardShortcut, isTyping } from '../../src/kanban/cardKeys'
import { applyPreview, locate, neighbourColumn, placementFor } from '../../src/kanban/movePreview'
import { sortBoards } from '../../src/kanban/useBoardList'
import type { ColumnView } from '../../src/kanban/useKanbanBoard'
import { board, card } from './fixtures'

const NOW = Date.parse('2026-09-25T12:00:00Z')

function views(): ColumnView[] {
  const value = board()
  return value.columns.map((column) => ({ column, cards: value.cards.filter((entry) => entry.column_id === column.id), total: 0, wip: undefined }))
}

describe('Darstellungshilfen', () => {
  it('färbt Badges nach Präfix', () => {
    expect(badgePrefix('VP-19')).toBe('VP')
    expect(badgePrefix('jkb_26')).toBe('JKB')
    expect(badgeStyle('SYS-01').background).toBe('#7c3aed')
    expect(badgeStyle('XY-1').background).toBe('#4b5563')
  })

  it('kürzt Beschreibungen nach Zeichen, nicht nach UTF-16-Einheiten', () => {
    expect(preview('a'.repeat(81))).toHaveLength(81)
    expect(preview('kurz')).toBe('kurz')
    expect(preview('😀'.repeat(81))).toBe(`${'😀'.repeat(80)}…`)
  })

  it('berechnet Alter und relative Zeit in Stufen', () => {
    expect(cardAge('2026-09-25T11:30:00Z', NOW)).toEqual({ key: 'ageNew', count: 0 })
    expect(cardAge('2026-09-25T02:00:00Z', NOW)).toEqual({ key: 'ageHours', count: 10 })
    expect(cardAge('2026-09-20T12:00:00Z', NOW)).toEqual({ key: 'ageDays', count: 5 })
    expect(cardAge('2026-09-04T12:00:00Z', NOW)).toEqual({ key: 'ageWeeks', count: 3 })
    expect(cardAge('2026-06-01T12:00:00Z', NOW)).toEqual({ key: 'ageMonths', count: 3 })
    expect(cardAge('kaputt', NOW)).toBeNull()
    expect(relativeTime('2026-09-25T11:59:30Z', NOW)?.key).toBe('justNow')
    expect(relativeTime('2026-09-25T11:15:00Z', NOW)).toEqual({ key: 'minutesAgo', count: 45 })
    expect(relativeTime('2026-09-11T12:00:00Z', NOW)).toEqual({ key: 'weeksAgo', count: 2 })
  })

  it('wählt lesbare Schrift und Initialen', () => {
    expect(textOn('#1e293b')).toBe('light')
    expect(textOn('#eab308')).toBe('dark')
    expect(textOn('rot')).toBe('dark')
    expect(initials('Anna Maria Becker')).toBe('AB')
    expect(initials('lena')).toBe('LE')
  })

  it('sortiert Boards: angeheftet zuerst, dann neueste', () => {
    const base = { icon: '', owner_id: 'o', role: 'owner', stats: { total: 0, done: 0, progress: 0 } }
    const sorted = sortBoards([
      { ...base, id: 'alt', title: 'A', pinned: false, updated_at: '2026-01-01' },
      { ...base, id: 'neu', title: 'B', pinned: false, updated_at: '2026-09-01' },
      { ...base, id: 'pin', title: 'C', pinned: true, updated_at: '2025-01-01' },
    ])
    expect(sorted.map((entry) => entry.id)).toEqual(['pin', 'neu', 'alt'])
  })
})

describe('Verschiebevorschau', () => {
  it('setzt die Karte an die Vorschauposition und findet sie wieder', () => {
    const moved = applyPreview(views(), { cardId: 'a', columnId: 'fertig', index: 0 })
    expect(moved.map((view) => view.cards.map((entry) => entry.id))).toEqual([['b'], ['c'], ['a']])
    expect(locate(moved, 'a')).toEqual({ columnId: 'fertig', index: 0 })
    expect(applyPreview(views(), null)).toHaveLength(3)
  })

  it('platziert relativ zu sichtbaren Nachbarn', () => {
    const visible = [card('x', 'offen', 'V'), card('y', 'offen', 'k')]
    expect(placementFor(visible, 0)).toEqual({ before_id: 'x' })
    expect(placementFor(visible, 2)).toEqual({ after_id: 'y' })
    expect(placementFor([], 0)).toEqual({})
  })

  it('überspringt nicht erlaubte Spalten', () => {
    expect(neighbourColumn(views(), 'offen', 1, (id) => id !== 'arbeit')).toBe('fertig')
    expect(neighbourColumn(views(), 'offen', -1, () => true)).toBeNull()
  })
})

describe('Tastenkürzel', () => {
  it('erkennt Kürzel nur außerhalb von Eingabefeldern', () => {
    const input = document.createElement('input')
    expect(isTyping(input)).toBe(true)
    expect(boardShortcut(new KeyboardEvent('keydown', { key: 'n' }))).toBe('new-card')
    expect(boardShortcut(new KeyboardEvent('keydown', { key: 'F' }))).toBe('fullscreen')
    expect(boardShortcut(new KeyboardEvent('keydown', { key: 'n', ctrlKey: true }))).toBeNull()
    const typed = new KeyboardEvent('keydown', { key: 'n' })
    Object.defineProperty(typed, 'target', { value: input })
    expect(boardShortcut(typed)).toBeNull()
  })
})
