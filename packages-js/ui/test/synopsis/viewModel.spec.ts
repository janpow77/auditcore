import { describe, expect, it } from 'vitest'
import {
  DEFAULT_SYNOPSIS_FILTER,
  applyRowOverrides,
  buildSynopsisView,
  changeIds,
  filterRows,
  positionText,
  stepChange,
} from '../../src/synopsis/viewModel'
import { segmentsText } from '../../src/synopsis/wordDiff'
import { article, checklist, standard, t } from './fixtures'

describe('View-Model der Synopse', () => {
  it('beschriftet Standardvergleiche mit Zählwerten, Hinweisen und Dokumentart', () => {
    const view = buildSynopsisView(standard.result, t, { title: standard.title })
    expect(view.title).toBe('Förderrichtlinie Mittelstand – Fassung 2025 und 2026')
    expect(view.oldLabel).toBe('Bisherige Fassung')
    expect(view.countsText).toBe('3 geändert · 2 entfallen · 3 neu · 0 verschoben · 6 zugeordnet')
    expect(view.detectedText).toContain('Fließtext')
    expect(view.notices[0]).toContain('keine Prüfungsentscheidung')
    expect(view.isArticleLaw).toBe(false)
    const first = view.rows[0]
    expect(first?.statusLabel).toBe('Geändert')
    expect(first?.new.some((segment) => segment.kind === 'added' && segment.text === 'Unternehmen in Hessen.')).toBe(true)
  })

  it('übernimmt Beschriftungen und Befehle der Gesetzessynopse', () => {
    const view = buildSynopsisView(article.result, t)
    expect(view.isArticleLaw).toBe(true)
    expect([view.oldLabel, view.newLabel, view.reasonLabel]).toEqual(['Geltende Fassung', 'Fassung nach dem Entwurf', 'Änderungsbefehl'])
    expect(view.openCommands.length).toBeGreaterThan(0)
    expect(view.consolidated.length).toBeGreaterThan(0)
    expect(view.notices).toContain('Arbeitshilfe ohne amtlichen Charakter; jede Zuordnung ist fachlich zu prüfen.')
    const replaced = view.rows.find((row) => row.location === '§ 3 Absatz 3')
    expect(replaced?.reason).toContain('durch die Angabe')
    // Ohne ndiff vom Server: Wortdifferenz wird nachgerechnet.
    expect(replaced?.old).toContainEqual({ text: 'drei', kind: 'removed' })
    expect(replaced?.new).toContainEqual({ text: 'sechs', kind: 'added' })
  })

  it('zeigt Antworten, Bemerkungen und Hinweise mit eigener Differenz', () => {
    const view = buildSynopsisView(checklist.result, t)
    const answer = view.rows[1]?.fields.find((field) => field.field === 'answer')
    expect(answer?.label).toBe('Antwort')
    expect(answer?.old).toContainEqual({ text: 'ja', kind: 'removed' })
    expect(answer?.new).toContainEqual({ text: 'nein', kind: 'added' })
  })

  it('verzichtet ohne Hervorhebung auf Markierungen', () => {
    const view = buildSynopsisView(standard.result, t, { highlight: false })
    expect(view.rows[0]?.old.every((segment) => segment.kind === 'same')).toBe(true)
    expect(view.rows[0]?.inline.map((segment) => segment.kind)).toEqual(['removed', 'same', 'added'])
  })

  it('filtert nach Art, Suchbegriff und Auswahl', () => {
    const rows = buildSynopsisView(standard.result, t).rows
    expect(filterRows(rows, DEFAULT_SYNOPSIS_FILTER).every((row) => row.status !== 'unchanged')).toBe(true)
    expect(filterRows(rows, { ...DEFAULT_SYNOPSIS_FILTER, statuses: ['unchanged'] })).toHaveLength(3)
    expect(filterRows(rows, { ...DEFAULT_SYNOPSIS_FILTER, query: 'PAUSCHALSATZ' }).map((row) => row.location)).toEqual([
      '§ 2 Förderfähige Ausgaben, Absatz 2',
    ])
    const overridden = applyRowOverrides(standard.result.rows, new Map([[rows[0]?.id ?? '', { selected: false }]]))
    const selectedOnly = filterRows(buildSynopsisView({ ...standard.result, rows: overridden }, t).rows, { ...DEFAULT_SYNOPSIS_FILTER, onlySelected: true })
    expect(selectedOnly.some((row) => row.id === rows[0]?.id)).toBe(false)
  })

  it('navigiert zwischen Änderungen und beschreibt die Position', () => {
    const ids = ['a', 'b', 'c']
    expect(stepChange(ids, null, 1)).toBe('a')
    expect(stepChange(ids, null, -1)).toBe('c')
    expect(stepChange(ids, 'b', 1)).toBe('c')
    expect(stepChange(ids, 'c', 1)).toBe('c')
    expect(stepChange(ids, 'a', -1)).toBe('a')
    expect(stepChange([], null, 1)).toBeNull()
    expect(positionText(ids, 'b', t)).toBe('Änderung 2 von 3')
    expect(positionText(ids, null, t)).toBe('3 Änderungen in dieser Ansicht')
    const rows = buildSynopsisView(standard.result, t).rows
    expect(changeIds(filterRows(rows, { ...DEFAULT_SYNOPSIS_FILTER, statuses: ['changed', 'unchanged'] }))).toHaveLength(3)
    expect(segmentsText(rows[0]?.old ?? [])).toBe(standard.result.rows[0]?.old_text)
  })
})
