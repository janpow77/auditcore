import { act, cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { createRef } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { ExportPayload, RowUpdate, SynopsisPort } from '@flowaudit/ui-core'
import { article, checklist, standard } from '../../ui-core/test/synopsis/fixtures'
import { FlowauditSynopsis, type FlowauditSynopsisHandle } from '../src'

const flush = () => act(() => new Promise<void>((resolve) => setTimeout(resolve, 0)))

afterEach(() => {
  cleanup()
  document.body.innerHTML = ''
  vi.restoreAllMocks()
})

const titles = (container: HTMLElement): string[] =>
  Array.from(container.querySelectorAll('.fa-synopsis-row__title')).map((node) => (node.textContent ?? '').replace(/, [^,]+$/, ''))

describe('FlowauditSynopsis (nativ)', () => {
  it('zeigt Kopf, Hinweise und nur Änderungen nebeneinander mit del/ins', () => {
    const { container } = render(<FlowauditSynopsis comparison={standard} />)
    expect(screen.getByRole('heading', { level: 2 }).textContent).toBe(standard.title)
    expect(container.textContent).toContain('3 geändert · 2 entfallen · 3 neu')
    expect(container.querySelectorAll('article')).toHaveLength(8)
    const first = container.querySelector('article') as HTMLElement
    expect(first.getAttribute('aria-labelledby')).toBeTruthy()
    expect(Array.from(first.querySelectorAll('h4')).map((node) => node.textContent)).toEqual(['Bisherige Fassung', 'Neue Fassung'])
    expect(first.querySelector('ins')?.textContent).toContain('Unternehmen in Hessen.')
    expect(first.querySelector('ins .fa-sr-only')?.textContent?.trim()).toBe('eingefügt:')
    expect(container.querySelector('script')).toBeNull()
  })

  it('wechselt auf die Inline-Ansicht und filtert nach Art und Suchbegriff', () => {
    const onLayoutChange = vi.fn()
    const { container } = render(<FlowauditSynopsis comparison={standard} onLayoutChange={onLayoutChange} />)
    const [sideBySide, inline] = within(container.querySelector('[role="group"]') as HTMLElement).getAllByRole('button')
    expect(sideBySide?.getAttribute('aria-pressed')).toBe('true')
    fireEvent.click(inline as HTMLElement)
    expect(onLayoutChange).toHaveBeenCalledWith('inline')
    expect(container.querySelector('.fa-synopsis-row__inline del')).not.toBeNull()
    const boxes = container.querySelectorAll('fieldset input[type="checkbox"]')
    fireEvent.click(boxes[5] as HTMLElement) // unverändert
    expect(container.querySelectorAll('article')).toHaveLength(11)
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'Umsatzsteuer' } })
    expect(titles(container)).toEqual(['§ 2 Förderfähige Ausgaben, Absatz 3'])
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'gibt es nicht' } })
    expect(container.textContent).toContain('Keine passenden Unterschiede')
  })

  it('navigiert per Taste, Schaltfläche und ref und meldet die Position', () => {
    const onNavigate = vi.fn()
    const ref = createRef<FlowauditSynopsisHandle>()
    const { container } = render(<FlowauditSynopsis ref={ref} comparison={standard} onNavigate={onNavigate} />)
    const status = screen.getByRole('status')
    expect(status.getAttribute('aria-live')).toBe('polite')
    expect(status.textContent).toBe('8 Änderungen in dieser Ansicht')
    const section = container.querySelector('section') as HTMLElement
    fireEvent.keyDown(section, { key: 'n' })
    expect(status.textContent).toBe('Änderung 1 von 8')
    expect(document.activeElement?.getAttribute('data-row-id')).toBe(standard.result.rows[0]?.row_id)
    fireEvent.keyDown(section, { key: 'j' })
    fireEvent.keyDown(section, { key: 'k' })
    expect(status.textContent).toBe('Änderung 1 von 8')
    fireEvent.click(screen.getByRole('button', { name: 'Nächste Änderung' }))
    expect(status.textContent).toBe('Änderung 2 von 8')
    expect(onNavigate).toHaveBeenCalledTimes(4)
    expect(container.querySelector('[aria-current="true"]')?.getAttribute('data-row-id')).toBe(standard.result.rows[1]?.row_id)
    fireEvent.keyDown(screen.getByRole('searchbox'), { key: 'n' })
    expect(status.textContent).toBe('Änderung 2 von 8')
    act(() => void ref.current?.previous())
    expect(status.textContent).toBe('Änderung 1 von 8')
  })

  it('bearbeitet Auswahl und Grund und speichert über den Port', async () => {
    const updateRows = vi.fn<NonNullable<SynopsisPort['updateRows']>>(async () => checklist)
    const port: SynopsisPort = { load: async () => checklist, updateRows, exportUrl: (id, format) => `/x/${id}/${format}` }
    const onRowUpdate = vi.fn<(update: RowUpdate) => void>()
    const { container } = render(<FlowauditSynopsis comparison={checklist} editable port={port} onRowUpdate={onRowUpdate} />)
    expect(container.textContent).toContain('5 von 6 Zeilen für die Ausgabe ausgewählt')
    fireEvent.click(container.querySelector('.fa-synopsis-row__include input') as HTMLElement)
    await flush()
    const rowId = checklist.result.rows[0]?.row_id ?? ''
    expect(onRowUpdate).toHaveBeenCalledWith({ row_id: rowId, selected: false })
    expect(updateRows).toHaveBeenCalledWith(checklist.id, [{ row_id: rowId, selected: false }])
    expect(container.textContent).toContain('4 von 6 Zeilen')
    const reason = container.querySelector('textarea') as HTMLTextAreaElement
    fireEvent.change(reason, { target: { value: 'redaktionell' } })
    fireEvent.blur(reason)
    await flush()
    expect(updateRows).toHaveBeenLastCalledWith(checklist.id, [{ row_id: rowId, reason: 'redaktionell' }])
    expect(Array.from(container.querySelectorAll('a[download]')).map((link) => link.getAttribute('href'))).toEqual([
      `/x/${checklist.id}/docx`,
      `/x/${checklist.id}/pdf`,
      `/x/${checklist.id}/json`,
    ])
    updateRows.mockRejectedValueOnce(new Error('offline'))
    const again = container.querySelector('textarea') as HTMLTextAreaElement
    fireEvent.change(again, { target: { value: 'neu' } })
    fireEvent.blur(again)
    await flush()
    expect(screen.getByRole('alert').textContent).toBe('Die Änderung konnte nicht gespeichert werden.')
  })

  it('lädt über den Port und meldet Ladefehler', async () => {
    const port: SynopsisPort = { load: vi.fn(async () => article) }
    const { container, unmount } = render(<FlowauditSynopsis comparisonId={article.id} port={port} />)
    expect(container.textContent).toContain('Vergleich wird geladen')
    await flush()
    expect(screen.getByRole('heading', { level: 2 }).textContent).toBe(article.title)
    expect(container.textContent).toContain('Änderungsbefehle erkannt')
    expect(container.querySelector('details summary')?.textContent).toBe('Konsolidierte Arbeitsfassung')
    unmount()
    render(<FlowauditSynopsis comparisonId="x" port={{ load: async () => Promise.reject(new Error('404')) }} />)
    await flush()
    expect(screen.getByRole('alert').textContent).toBe('Der Vergleich konnte nicht geladen werden.')
  })

  it('exportiert HTML und Markdown als Ereignis und Datei', () => {
    const createObjectURL = vi.fn(() => 'blob:x')
    Object.assign(URL, { createObjectURL, revokeObjectURL: vi.fn() })
    const onExport = vi.fn<(payload: ExportPayload) => void>()
    render(<FlowauditSynopsis comparison={standard} onExport={onExport} />)
    fireEvent.click(screen.getByRole('button', { name: 'Markdown' }))
    fireEvent.click(screen.getByRole('button', { name: 'HTML' }))
    expect(onExport.mock.calls.map(([payload]) => [payload.format, payload.filename])).toEqual([
      ['markdown', 'Förderrichtlinie_Mittelstand_Fassung_2025_und_2026.md'],
      ['html', 'Förderrichtlinie_Mittelstand_Fassung_2025_und_2026.html'],
    ])
    expect(onExport.mock.calls[0]?.[0].content).toContain('**Unternehmen in Hessen.**')
    expect(createObjectURL).toHaveBeenCalledTimes(2)
    fireEvent.click(screen.getByRole('button', { name: 'Druckansicht / PDF' }))
    expect(document.querySelector('iframe[aria-hidden="true"]')).not.toBeNull()
  })

  it('spricht Englisch und zeigt ohne Daten einen leeren Zustand', () => {
    const { container, unmount } = render(<FlowauditSynopsis result={standard.result} locale="en" />)
    expect(container.textContent).toContain('Previous version')
    expect(container.textContent).toContain('Next change')
    unmount()
    expect(render(<FlowauditSynopsis />).container.textContent).toBe('Kein Vergleich ausgewählt.')
  })
})
