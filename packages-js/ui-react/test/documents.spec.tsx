import { act, cleanup, fireEvent, render, screen } from '@testing-library/react'
import { createRef } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { created, fakePort, file, imported, summaries } from '../../ui-core/test/documents/fake-port'
import { FlowauditComparisons, type FlowauditComparisonsHandle } from '../src'

const flush = () => act(() => new Promise<void>((resolve) => setTimeout(resolve, 0)))

afterEach(() => {
  cleanup()
  document.body.innerHTML = ''
})

function choose(input: Element | null, chosen: File): void {
  fireEvent.change(input as HTMLInputElement, { target: { files: [chosen] } })
}

describe('FlowauditComparisons (nativ)', () => {
  it('legt einen Vergleich an, meldet ihn und leert die Dateiauswahl', async () => {
    const port = fakePort()
    const onComparisonCreated = vi.fn()
    const { container } = render(<FlowauditComparisons port={port} onComparisonCreated={onComparisonCreated} />)
    await flush()
    choose(container.querySelector('[data-testid="comparisons-oldFile"]'), file('alt.docx'))
    choose(container.querySelector('[data-testid="comparisons-newFile"]'), file('neu.pdf'))
    expect(container.textContent).toContain('PDF-Dateien werden immer als Fließtext verglichen.')
    fireEvent.submit(container.querySelector('form') as HTMLFormElement)
    await flush()
    expect(port.create).toHaveBeenCalledWith(expect.any(File), 'alt.docx', expect.any(File), 'neu.pdf', expect.objectContaining({ mode: 'auto', threshold: 85 }))
    expect(onComparisonCreated).toHaveBeenCalledWith(created)
    expect(screen.getByRole('status').textContent).toBe(`„${created.title}“ wurde angelegt.`)
    expect(container.textContent).toContain('DOCX, DOCM oder PDF, höchstens 20 MiB')
  })

  it('zeigt Befunde vor dem Hochladen und Servermeldungen', async () => {
    const port = fakePort({ create: vi.fn(async () => Promise.reject(new TypeError('Failed to fetch'))) })
    const onError = vi.fn()
    const { container } = render(<FlowauditComparisons port={port} maxUploadBytes={1024} onError={onError} />)
    await flush()
    choose(container.querySelector('[data-testid="comparisons-oldFile"]'), file('alt.docx', 2048))
    fireEvent.submit(container.querySelector('form') as HTMLFormElement)
    await flush()
    expect(container.querySelector('.fa-comparisons-form__problems')?.textContent).toContain('alt.docx ist größer als 1 KiB.')
    choose(container.querySelector('[data-testid="comparisons-oldFile"]'), file('alt.docx'))
    choose(container.querySelector('[data-testid="comparisons-newFile"]'), file('neu.docx'))
    fireEvent.submit(container.querySelector('form') as HTMLFormElement)
    await flush()
    expect(screen.getByRole('alert').textContent).toBe('Keine Verbindung zum Server (Failed to fetch).')
    expect(onError).toHaveBeenCalledOnce()
  })

  it('löscht nach Bestätigung im Dialog', async () => {
    const port = fakePort()
    const onComparisonRemoved = vi.fn()
    const { container } = render(<FlowauditComparisons port={port} onComparisonRemoved={onComparisonRemoved} />)
    await flush()
    const target = summaries[0]!
    fireEvent.click(screen.getByRole('button', { name: `„${target.title}“ löschen` }))
    const dialog = screen.getByRole('dialog', { name: 'Vergleich löschen?' })
    expect(dialog.textContent).toContain('wird endgültig gelöscht')
    fireEvent.click(dialog.querySelector('[data-testid="comparisons-confirm-remove"]') as HTMLButtonElement)
    await flush()
    expect(port.remove).toHaveBeenCalledWith(target.id)
    expect(onComparisonRemoved).toHaveBeenCalledWith(target.id)
    expect(container.querySelectorAll('.fa-comparisons-list__item')).toHaveLength(summaries.length - 1)
    expect(screen.queryByRole('dialog')).toBeNull()
  })

  it('importiert eine JSON-Datei', async () => {
    const port = fakePort()
    const onComparisonImported = vi.fn()
    const { container } = render(<FlowauditComparisons port={port} onComparisonImported={onComparisonImported} />)
    await flush()
    choose(container.querySelector('[data-testid="comparisons-import"]'), new File([JSON.stringify(created.result)], 'e.json'))
    await vi.waitFor(() => expect(onComparisonImported).toHaveBeenCalledWith(imported))
    expect(port.importResult).toHaveBeenCalledWith({ result: created.result })
  })

  it('öffnet ohne Synopse nur per Rückruf und bietet reload/open über ref', async () => {
    const port = fakePort()
    const onComparisonOpen = vi.fn()
    const ref = createRef<FlowauditComparisonsHandle>()
    const { container } = render(<FlowauditComparisons ref={ref} port={port} showSynopsis={false} onComparisonOpen={onComparisonOpen} />)
    await flush()
    fireEvent.click(container.querySelector('.fa-comparisons-list__actions button') as HTMLButtonElement)
    expect(onComparisonOpen).toHaveBeenCalledWith(summaries[0]?.id)
    expect(port.load).not.toHaveBeenCalled()
    await act(() => ref.current?.reload())
    expect(port.list).toHaveBeenCalledTimes(2)
  })
})
