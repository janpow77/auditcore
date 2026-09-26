import { act, cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { benfordAnalysis, fakeBenfordPort } from '../../ui-core/test/sampling/fake-port'
import { FlowauditBenford } from '../src/benford/FlowauditBenford'

const flush = () => act(() => new Promise<void>((resolve) => setTimeout(resolve, 0)))
const submit = () => fireEvent.submit(screen.getByTestId('benford-analyse').closest('form') as HTMLFormElement)

afterEach(() => cleanup())

describe('FlowauditBenford (nativ)', () => {
  it('analysiert übergebene Werte, zeigt Kennzahlen, Stufe und hebt Ziffern hervor', async () => {
    const port = fakeBenfordPort()
    const onAnalysisCompleted = vi.fn()
    render(<FlowauditBenford port={port} values={[123, 45.6, null, 0]} onAnalysisCompleted={onAnalysisCompleted} />)
    await flush()
    expect(screen.getByTestId('benford-count').textContent).toBe('4 Werte übernommen')
    submit()
    await flush()
    expect(port.calls).toEqual([{ test: 'first', profile: 'nigrini.2012', values: [123, 45.6, null, 0] }])
    expect(screen.getByTestId('benford-level').textContent).toBe(benfordAnalysis.conformity.mad_label)
    expect(screen.getByTestId('benford-exceeding').textContent).toBe(benfordAnalysis.conformity.exceeding_digits.join(', '))
    const flagged = Array.from(document.querySelectorAll('.fa-benford__bar--exceeds')).map((bar) => Number(bar.getAttribute('data-digit')))
    expect(flagged).toEqual(benfordAnalysis.conformity.exceeding_digits)
    expect(screen.getByRole('img', { name: /Erste Ziffer/ })).toBe(screen.getByTestId('benford-chart'))
    expect(document.body.textContent).toContain('keine Feststellungen')
    expect(onAnalysisCompleted).toHaveBeenCalledWith(benfordAnalysis)
  })

  it('verlangt bei zweistelligen Tests die Regel für kurze Werte', async () => {
    const port = fakeBenfordPort()
    render(<FlowauditBenford port={port} values={[12, 34]} />)
    await flush()
    fireEvent.change(screen.getByTestId('benford-test'), { target: { value: 'second' } })
    submit()
    await flush()
    expect(screen.getByRole('alert').textContent).toContain('Regel für Werte')
    expect(port.calls).toEqual([])
    fireEvent.click(screen.getByTestId('benford-short-exclude'))
    submit()
    await flush()
    expect(port.calls).toEqual([{ test: 'second', profile: 'nigrini.2012', short_values: 'exclude', values: [12, 34] }])
  })

  it('liest eine CSV-Datei mit Dezimalkomma und meldet unlesbare Zeilen', async () => {
    render(<FlowauditBenford port={fakeBenfordPort()} />)
    await flush()
    const file = new File(['Beleg;Betrag\nA;1.234,50\nB;x\nC;17,00\n'], 'belege.csv', { type: 'text/csv' })
    fireEvent.change(document.querySelector('input[type="file"]') as HTMLInputElement, { target: { files: [file] } })
    await flush()
    expect(document.body.textContent).toContain('belege.csv: 3 Zeilen')
    expect(document.body.textContent).toContain('1 Zeilen nicht lesbar (Zeilen 2)')
    fireEvent.click(screen.getByTestId('import-apply'))
    expect(screen.getByTestId('benford-count').textContent).toBe('2 Werte übernommen')
  })

  it('zeigt Fehler der Analyse und meldet onError', async () => {
    const onError = vi.fn()
    render(<FlowauditBenford port={fakeBenfordPort('analyse')} values={[1, 2]} onError={onError} />)
    await flush()
    submit()
    await flush()
    expect(screen.getByRole('alert').textContent).toBe('Anfrage abgelehnt: Dienst nicht erreichbar')
    expect(onError).toHaveBeenCalledWith('Dienst nicht erreichbar')
  })

  it('neue Werte über die Eigenschaft verwerfen das Ergebnis', async () => {
    const view = render(<FlowauditBenford port={fakeBenfordPort()} values={[1, 2]} />)
    await flush()
    submit()
    await flush()
    expect(screen.queryByTestId('benford-chart')).toBeTruthy()
    view.rerender(<FlowauditBenford port={fakeBenfordPort()} values={[3, 4, 5]} />)
    await flush()
    expect(screen.queryByTestId('benford-chart')).toBeNull()
    expect(screen.getByTestId('benford-count').textContent).toBe('3 Werte übernommen')
  })
})
