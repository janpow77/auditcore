import { describe, expect, it } from 'vitest'
import { escapeHtml, exportFilename, toHtml, toMarkdown } from '../../src/synopsis/exporters'
import { buildSynopsisView, filterRows, DEFAULT_SYNOPSIS_FILTER } from '../../src/synopsis/viewModel'
import { article, standard, t } from './fixtures'

function input(comparison = standard, rowsOverride?: typeof standard.result.rows) {
  const result = rowsOverride ? { ...comparison.result, rows: rowsOverride } : comparison.result
  const view = buildSynopsisView(result, t, { title: comparison.title })
  return { view, rows: filterRows(view.rows, DEFAULT_SYNOPSIS_FILTER), t, generatedAt: '2026-09-25T10:00:00Z' }
}

describe('Exporte', () => {
  it('erzeugt eigenständiges HTML mit del/ins, Druck-CSS und ohne externe Ressourcen', () => {
    const html = toHtml(input())
    expect(html.startsWith('<!doctype html><html lang="de">')).toBe(true)
    expect(html).toContain('<title>Förderrichtlinie Mittelstand – Fassung 2025 und 2026</title>')
    expect(html).toContain('<ins>Unternehmen in Hessen.</ins>')
    expect(html).toContain('@media print')
    expect(html).toContain('<th scope="col">Fundstelle</th>')
    expect(html).not.toMatch(/<script|<link|src=/)
  })

  it('maskiert Inhalte gegen HTML-Einschleusung', () => {
    const rows = standard.result.rows.map((row, index) => (index === 0 ? { ...row, new_text: '<img src=x onerror=alert(1)>', diff: {} } : row))
    const html = toHtml(input(standard, rows))
    expect(html).not.toContain('<img')
    expect(html).toContain('&lt;img src=x onerror=alert(1)&gt;')
    expect(escapeHtml(`"'&`)).toBe('&quot;&#39;&amp;')
  })

  it('berücksichtigt die Auswahl je Zeile', () => {
    const rows = standard.result.rows.map((row) => ({ ...row, selected: row.status === 'added' }))
    const markdown = toMarkdown(input(standard, rows))
    expect(markdown).toContain('(Neu)')
    expect(markdown).not.toContain('(Geändert)')
  })

  it('schreibt Markdown mit Streichungen, Einfügungen und Änderungsbefehlen', () => {
    const markdown = toMarkdown(input(article))
    expect(markdown.startsWith('# Zuwendungsgesetz – Synopse zum Änderungsgesetz\n')).toBe(true)
    expect(markdown).toContain('**Geltende Fassung:**')
    expect(markdown).toContain('~~drei~~')
    expect(markdown).toContain('**sechs**')
    expect(markdown).toContain('**Änderungsbefehl:**')
    expect(markdown).toContain('## Offene Änderungsbefehle')
    const html = toHtml(input(article))
    expect(html).toContain('<th scope="col">Änderungsbefehl</th>')
  })

  it('bildet sichere Dateinamen mit Umlauten', () => {
    expect(exportFilename('Prüfbericht 2026/27: Synopse', 'md')).toBe('Prüfbericht_2026_27_Synopse.md')
    expect(exportFilename('///', 'html')).toBe('Synopse.html')
  })
})
