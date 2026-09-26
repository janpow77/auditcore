import { describe, expect, it } from 'vitest'
import { parseImport } from '../../src/documents/importing'
import { filterSummaries, formatDateTime, summaryOf, summaryView } from '../../src/documents/list'
import { created, summaries, t } from './fake-port'

describe('Liste und Import', () => {
  it('zeigt Art, Dateien und Zählwerte der echten Zusammenfassung', () => {
    const law = summaries.find((item) => item.comparison_type === 'article_law')
    expect(law).toBeDefined()
    const view = summaryView(law as (typeof summaries)[number], t, 'de')
    expect(view.kindLabel).toBe('Gesetzessynopse')
    expect(view.files).toBe('al_stamm.docx → al_befehle.docx')
    expect(view.counts).toBe('3 geändert · 1 entfallen · 1 neu · 0 verschoben')
    expect(view.changes).toBe(5)
    expect(summaryView({ ...summaries[0]!, comparison_type: 'eigen' }, t, 'de').kindLabel).toBe('eigen')
  })

  it('sucht in Titel und Dateinamen und sortiert neueste zuerst', () => {
    const reversed = [...summaries].reverse()
    expect(filterSummaries(reversed, '').map((item) => item.id)).toEqual(summaries.map((item) => item.id))
    expect(filterSummaries(summaries, 'PRÜFCHECK').map((item) => item.title)).toEqual(['Prüfcheckliste – Fassungen 1 und 2'])
    expect(filterSummaries(summaries, 'al_befehle')).toHaveLength(1)
    expect(filterSummaries(summaries, 'nichts')).toEqual([])
  })

  it('bildet die Zusammenfassung aus einem gespeicherten Vergleich wie der Server', () => {
    expect(summaryOf(created)).toEqual(summaries.find((item) => item.id === created.id))
    expect(formatDateTime('kein Datum', 'de')).toBe('kein Datum')
  })

  it('liest JSON-Ausgabe, gespeicherten Vergleich und Anfrageform', () => {
    expect(parseImport(JSON.stringify(created.result))).toEqual({ ok: true, request: { result: created.result } })
    expect(parseImport(JSON.stringify(created))).toEqual({ ok: true, request: { title: created.title, result: created.result } })
    expect(parseImport(JSON.stringify({ title: ' ', result: created.result }))).toEqual({ ok: true, request: { result: created.result } })
    expect(parseImport('{')).toEqual({ ok: false, key: 'importUnreadable' })
    expect(parseImport('[1]')).toEqual({ ok: false, key: 'importInvalid' })
    expect(parseImport('{"result": {"rows": []}}')).toEqual({ ok: false, key: 'importInvalid' })
  })
})
