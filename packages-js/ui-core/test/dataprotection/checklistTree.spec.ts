import { describe, expect, it } from 'vitest'
import { translator } from '../../src/i18n'
import { dataprotectionMessages } from '../../src/dataprotection/messages'
import { checklistBranchIds, checklistChange, checklistEdit, checklistMeta, checklistProgress, checklistTone, checklistTree, parseEvidenceIds, toggleChecklistNode } from '../../src/dataprotection/checklistTree'
import type { ChecklistItemView, ChecklistStatus } from '../../src/dataprotection/assistantTypes'
import { fresh } from './fake-assistant-port'

function withStatus(changes: Record<string, ChecklistStatus>): ChecklistItemView[] {
  return fresh.pruefpunkte.map((item) => ({ ...item, status: changes[item.id] ?? item.status }))
}

describe('Prüfpunkte als Baum', () => {
  it('gruppiert CHK-01 bis CHK-30 nach Bereich in Katalogreihenfolge', () => {
    const tree = checklistTree(fresh.pruefpunkte)
    expect(tree.map((node) => node.label)).toEqual(['A', 'B', 'C', 'D', 'E', 'F'])
    expect(tree[0]?.children.map((node) => node.id)).toEqual(['CHK-01', 'CHK-02', 'CHK-03', 'CHK-04'])
    expect(checklistProgress(tree)).toEqual({ total: 30, settled: 0, attention: 0 })
    expect(checklistBranchIds(tree)).toEqual(['bereich:A', 'bereich:B', 'bereich:C', 'bereich:D', 'bereich:E', 'bereich:F'])
  })

  it('leitet Ton und Fortschritt eines Bereichs aus seinen Prüfpunkten ab', () => {
    const tree = checklistTree(withStatus({ 'CHK-01': 'nachgewiesen', 'CHK-02': 'nicht_anwendbar', 'CHK-03': 'nachgewiesen', 'CHK-04': 'nachgewiesen', 'CHK-05': 'in_bearbeitung', 'CHK-10': 'klaerungsbedarf' }))
    expect(tree.map((node) => node.tone)).toEqual(['settled', 'progress', 'attention', 'open', 'open', 'open'])
    expect(tree[0]?.progress).toEqual({ total: 4, settled: 4, attention: 0 })
    expect(checklistProgress(tree)).toEqual({ total: 30, settled: 4, attention: 1 })
    expect(checklistTone('erneut_zu_pruefen')).toBe('attention')
  })

  it('schaltet Knoten um, ohne den bisherigen Satz zu ändern', () => {
    const before = new Set(['bereich:A'])
    expect([...toggleChecklistNode(before, 'CHK-01')]).toEqual(['bereich:A', 'CHK-01'])
    expect([...toggleChecklistNode(before, 'bereich:A')]).toEqual([])
    expect([...before]).toEqual(['bereich:A'])
  })

  it('beschriftet Zuständigkeit und Nachweisarten und lässt leere Angaben weg', () => {
    const t = translator(dataprotectionMessages, 'de')
    const item = fresh.pruefpunkte.find((entry) => entry.id === 'CHK-14') as ChecklistItemView
    expect(checklistMeta(t, item, (value) => value)).toEqual([
      { key: 'role', label: 'Zuständig', value: 'IT-Betrieb' },
      { key: 'kinds', label: 'Erforderliche Nachweisarten', value: 'Betriebsnachweis, Konzept, Test' },
    ])
    const changed = { ...item, owner: 'p1', updated_by: 'p2', updated_at: '2026-10-12' }
    expect(checklistMeta(t, changed, (value) => `am ${value}`).map((row) => row.value)).toEqual(['IT-Betrieb', 'Betriebsnachweis, Konzept, Test', 'p1', 'p2 · am 2026-10-12'])
    expect(parseEvidenceIds(' n1, ,n2 ')).toEqual(['n1', 'n2'])
  })

  it('sendet Bearbeitung und Frist nur, wenn sie geändert wurden', () => {
    const item = fresh.pruefpunkte.find((entry) => entry.id === 'CHK-14') as ChecklistItemView
    const edit = checklistEdit(item)
    expect(checklistChange(item, { ...edit, status: 'zur_pruefung', evidence: 'n1' })).toEqual({ status: 'zur_pruefung', justification: '', evidence_ids: ['n1'] })
    expect(checklistChange(item, { ...edit, owner: ' p1 ', due: '2026-11-30' })).toEqual({ status: 'offen', justification: '', evidence_ids: [], owner: 'p1', due: '2026-11-30' })
    expect(checklistChange({ ...item, owner: 'p1' }, { ...edit, owner: '' }).owner).toBe('')
  })
})
