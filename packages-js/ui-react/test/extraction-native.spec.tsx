import { act, cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { fakeExtractionPort, runDonut, runOk, syntheticFile } from '../../ui-core/test/extraction/fake-port'
import { FlowauditExtraction } from '../src/extraction/FlowauditExtraction'

const flush = () => act(() => new Promise<void>((resolve) => setTimeout(resolve, 0)))
const submit = () => fireEvent.submit(screen.getByTestId('extraction-run').closest('form') as HTMLFormElement)

afterEach(() => cleanup())

describe('FlowauditExtraction (nativ)', () => {
  it('lädt hoch, zeigt Feldkonfidenz, Entscheidung und Befunde und meldet das Ergebnis', async () => {
    const port = fakeExtractionPort()
    const onExtractionCompleted = vi.fn()
    render(<FlowauditExtraction port={port} onExtractionCompleted={onExtractionCompleted} />)
    await flush()
    submit()
    await flush()
    expect(screen.getByRole('alert').textContent).toBe('Bitte eine Datei auswählen.')
    fireEvent.change(screen.getByTestId('extraction-file'), { target: { files: [syntheticFile()] } })
    fireEvent.change(screen.getByTestId('extraction-profile'), { target: { value: 'auditcore.pipeline.donut' } })
    submit()
    await flush()
    expect(port.calls).toEqual([['beleg.png', 'auditcore.pipeline.donut', 64]])
    expect(screen.getByTestId('extraction-status').textContent).toBe('Prüfung erforderlich')
    const total = document.querySelector('[data-field="total"]')
    expect(total?.textContent).toContain('verworfen (Plausibilität)')
    expect(total?.textContent).toContain('Vorschlag: 99.999,99')
    expect(document.querySelector('[data-field="date"] .fa-badge--warning')?.textContent).toMatch(/81\s%/)
    expect(onExtractionCompleted).toHaveBeenCalledWith(runDonut)
  })

  it('zeigt ein übergebenes Ergebnis ohne Port', async () => {
    render(<FlowauditExtraction result={runOk} />)
    await flush()
    expect(document.body.textContent).toContain('Kein Port übergeben')
    expect(screen.getByTestId('extraction-status').textContent).toBe('Ohne Auffälligkeiten')
    expect(document.querySelector('form')).toBeNull()
  })

  it('meldet abgelehnte Läufe über onError', async () => {
    const onError = vi.fn()
    render(<FlowauditExtraction port={fakeExtractionPort({ failing: 'run' })} onError={onError} />)
    await flush()
    fireEvent.change(screen.getByTestId('extraction-file'), { target: { files: [syntheticFile()] } })
    submit()
    await flush()
    expect(onError).toHaveBeenCalledWith('Dienst nicht erreichbar')
    expect(document.querySelector('.fa-extraction__failure')?.textContent).toBe('Anfrage abgelehnt: Dienst nicht erreichbar')
  })
})
