import { act, cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { fakeSamplingPort, populationItems, selectionResult, sizeResult, type SamplingFake } from '../../ui-core/test/sampling/fake-port'
import { FlowauditSampling, type FlowauditSamplingProps } from '../src/sampling/FlowauditSampling'

const flush = () => act(() => new Promise<void>((resolve) => setTimeout(resolve, 0)))

afterEach(() => cleanup())

async function mounted(port: SamplingFake = fakeSamplingPort(), extra: Partial<FlowauditSamplingProps> = {}) {
  const view = render(<FlowauditSampling port={port} items={populationItems} {...extra} />)
  await flush()
  return { ...view, port }
}

const byTestId = (id: string) => screen.getByTestId(id) as HTMLInputElement

async function fillSize(): Promise<void> {
  fireEvent.change(byTestId('sampling-population_value'), { target: { value: '475.478,94' } })
  fireEvent.change(byTestId('sampling-materiality'), { target: { value: '50.000' } })
  fireEvent.change(byTestId('sampling-expected_error_rate'), { target: { value: '0,5' } })
  fireEvent.change(byTestId('sampling-confidence'), { target: { value: '0.95' } })
  fireEvent.submit(byTestId('sampling-calculate').closest('form') as HTMLFormElement)
  await flush()
}

describe('FlowauditSampling (nativ)', () => {
  it('lädt die Profile und wählt die empfohlene Methode sichtbar vor', async () => {
    await mounted()
    expect(byTestId('sampling-method').value).toBe('portal.mus_poisson')
    expect(screen.getByText('Empfohlen')).toBeTruthy()
    expect(document.body.textContent).toContain('n = ⌈RF · V / max(M − V · r, M / 2)⌉')
  })

  it('meldet fehlende Pflichtangaben mit role=alert statt zu raten', async () => {
    const { port } = await mounted()
    fireEvent.submit(byTestId('sampling-calculate').closest('form') as HTMLFormElement)
    await flush()
    expect(port.calls.size).toEqual([])
    expect(screen.getAllByRole('alert').length).toBeGreaterThanOrEqual(3)
    expect(byTestId('sampling-materiality').getAttribute('aria-invalid')).toBe('true')
    expect(byTestId('sampling-materiality').getAttribute('aria-describedby')).toMatch(/-materiality-error$/)
  })

  it('berechnet den Umfang mit Herleitung und meldet onSizeCalculated', async () => {
    const onSizeCalculated = vi.fn()
    const { port } = await mounted(fakeSamplingPort(), { onSizeCalculated })
    await fillSize()
    expect(port.calls.size).toEqual([{ method: 'portal.mus_poisson', population_value: 475478.94, materiality: 50000, expected_error_rate: 0.005, confidence_level: 0.95 }])
    expect(byTestId('sampling-size').textContent).toBe('n = 30')
    expect(document.body.textContent).toContain('Präzision')
    expect(onSizeCalculated).toHaveBeenCalledWith(sizeResult)
    expect(byTestId('sampling-sample-size').value).toBe('30')
  })

  it('zieht mit Aufteilung je Schicht, zeigt den Seed und exportiert', async () => {
    const onSelectionDrawn = vi.fn()
    const { port } = await mounted(fakeSamplingPort(), { onSelectionDrawn })
    fireEvent.change(byTestId('sampling-sample-size'), { target: { value: '6' } })
    fireEvent.submit(byTestId('sampling-draw').closest('form') as HTMLFormElement)
    await flush()
    expect(screen.getByRole('alert').textContent).toBe('Aufteilung auf Schichten wählen.')
    fireEvent.change(byTestId('sampling-allocation'), { target: { value: 'proportional' } })
    fireEvent.submit(byTestId('sampling-draw').closest('form') as HTMLFormElement)
    await flush()
    expect(port.calls.selection[0]).toMatchObject({ method: 'mus', variant: 'portal', sample_size: 6, allocation: 'proportional' })
    expect(port.calls.selection[0]).not.toHaveProperty('seed')
    expect(byTestId('sampling-seed-used').textContent).toContain('Seed 42')
    expect(byTestId('sampling-seed').value).toBe('42')
    expect(onSelectionDrawn).toHaveBeenCalledWith(selectionResult)
    expect(within(screen.getByTestId('sampling-rows')).getAllByRole('row')).toHaveLength(selectionResult.rows.length + 1)
    URL.createObjectURL = vi.fn(() => 'blob:x')
    URL.revokeObjectURL = vi.fn()
    fireEvent.click(byTestId('sampling-export-csv'))
    await flush()
    expect(port.calls.export[0]).toEqual([expect.objectContaining({ seed: 42 }), 'csv'])
    expect(URL.createObjectURL).toHaveBeenCalled()
  })

  it('neu ziehen verwirft den Seed und lässt ihn vom Server erzeugen', async () => {
    const { port } = await mounted(fakeSamplingPort(), { items: populationItems.map(({ id, value }) => ({ id, value })) })
    fireEvent.change(byTestId('sampling-sample-size'), { target: { value: '6' } })
    fireEvent.change(byTestId('sampling-seed'), { target: { value: '7' } })
    fireEvent.submit(byTestId('sampling-draw').closest('form') as HTMLFormElement)
    await flush()
    expect(port.calls.selection[0]).toMatchObject({ seed: 7 })
    fireEvent.click(byTestId('sampling-redraw'))
    await flush()
    expect(port.calls.selection[1]).not.toHaveProperty('seed')
  })

  it('zeigt Serverfehler und meldet onError', async () => {
    const onError = vi.fn()
    await mounted(fakeSamplingPort('size'), { onError })
    await fillSize()
    expect(document.body.textContent).toContain('Anfrage abgelehnt: Konfidenzniveau 0.93 ist nicht definiert')
    expect(onError).toHaveBeenCalledWith('Konfidenzniveau 0.93 ist nicht definiert')
  })

  it('übersetzt Beschriftungen mit locale=en und fällt sonst auf Deutsch zurück', async () => {
    await mounted(fakeSamplingPort(), { locale: 'en' })
    expect(document.body.textContent).toContain('Calculate sample size')
    expect(document.body.textContent).toContain('Draw sample')
    expect(document.body.textContent).toContain('Grundgesamtheit')
    expect(document.querySelector('.fa-sampling')?.getAttribute('lang')).toBe('en')
  })

  it('übernimmt eine Datei als Grundgesamtheit mit Kennungs- und Schichtspalte', async () => {
    await mounted(fakeSamplingPort(), { items: [] })
    const file = new File(['Beleg;Betrag;Los\nA;1.234,50;L1\nB;17,00;L2\n'], 'belege.csv', { type: 'text/csv' })
    fireEvent.change(document.querySelector('input[type="file"]') as HTMLInputElement, { target: { files: [file] } })
    await flush()
    expect(document.body.textContent).toContain('belege.csv: 2 Zeilen')
    const [, idColumn, stratumColumn] = screen.getAllByRole('combobox').filter((node) => node.closest('.fa-import'))
    fireEvent.change(idColumn as HTMLSelectElement, { target: { value: '0' } })
    fireEvent.change(stratumColumn as HTMLSelectElement, { target: { value: '2' } })
    fireEvent.click(screen.getByTestId('import-apply'))
    await flush()
    expect(byTestId('sampling-population').textContent).toBe('2 Elemente, Summe 1.251,5 · 2 Schichten')
  })
})
