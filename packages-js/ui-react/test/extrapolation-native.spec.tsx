import { act, cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { evaluationResult, fakeExtrapolationPort, fixtureStrata, fixtureUnits, residualResult } from '../../ui-core/test/extrapolation/fake-port'
import { FlowauditExtrapolation } from '../src/extrapolation/FlowauditExtrapolation'

vi.mock('@flowaudit/common/browser', () => ({ saveFile: vi.fn() }))

const flush = () => act(() => new Promise<void>((resolve) => setTimeout(resolve, 0)))

afterEach(() => cleanup())

async function evaluated(port = fakeExtrapolationPort(), handlers: Record<string, (value: unknown) => void> = {}) {
  render(<FlowauditExtrapolation port={port} strata={fixtureStrata} units={fixtureUnits} onEvaluationCompleted={handlers.evaluated} onResidualComputed={handlers.residual} onError={handlers.error} />)
  await flush()
  fireEvent.change(screen.getByTestId('extrapolation-method'), { target: { value: 'mus.standard' } })
  fireEvent.change(screen.getByTestId('extrapolation-confidence'), { target: { value: '0.9' } })
  fireEvent.click(screen.getByTestId('extrapolation-evaluate'))
  await flush()
  return port
}

describe('FlowauditExtrapolation (nativ)', () => {
  it('rechnet hoch und zeigt TER, Ergebnis und Herleitung', async () => {
    const onEvaluated = vi.fn()
    const port = await evaluated(fakeExtrapolationPort(), { evaluated: onEvaluated })
    expect(port.calls.evaluate[0]).toMatchObject({ method: 'mus.standard', confidence_level: 0.9, materiality_rate: 0.02 })
    expect(onEvaluated).toHaveBeenCalledWith(evaluationResult)
    expect(screen.getByTestId('extrapolation-conclusion').textContent).toBe('Nicht schlüssig – weitere Prüfungshandlungen')
    expect(screen.getByTestId('extrapolation-metrics').textContent).toContain('Fehlerobergrenze (ULE)')
    expect(document.body.textContent).toContain('Korrigierte anomale Fehler sind nicht Teil der Gesamtfehlerquote.')
  })

  it('berechnet die RER getrennt und exportiert', async () => {
    const onResidual = vi.fn()
    const port = await evaluated(fakeExtrapolationPort(), { residual: onResidual })
    fireEvent.change(screen.getByTestId('extrapolation-rer-corrections'), { target: { value: '2,1' } })
    fireEvent.click(screen.getByTestId('extrapolation-residual'))
    await flush()
    expect(port.calls.residual[0]).toMatchObject({ audit_population: 1_000_000, total_error_rate: 0.016, financial_corrections: 2.1 })
    expect(onResidual).toHaveBeenCalledWith(residualResult)
    expect(screen.getByTestId('extrapolation-rer').textContent).toContain('über der Wesentlichkeitsschwelle')
    fireEvent.click(screen.getByTestId('extrapolation-export-json'))
    await flush()
    expect(port.calls.export[0]?.[1]).toBe('json')
  })

  it('meldet Feldbefunde und abgelehnte Anfragen', async () => {
    const onError = vi.fn()
    render(<FlowauditExtrapolation port={fakeExtrapolationPort('evaluate')} strata={fixtureStrata} units={fixtureUnits} onError={onError} />)
    await flush()
    fireEvent.change(screen.getByTestId('extrapolation-method'), { target: { value: 'mus.conservative' } })
    fireEvent.change(screen.getByTestId('extrapolation-confidence'), { target: { value: '0.9' } })
    fireEvent.click(screen.getByTestId('extrapolation-evaluate'))
    await flush()
    expect(screen.getByTestId('extrapolation-form-error').textContent).toBe('Bitte die markierten Felder prüfen.')
    expect(screen.getByTestId('extrapolation-sample-size').getAttribute('aria-invalid')).toBe('true')
    fireEvent.change(screen.getByTestId('extrapolation-sample-size'), { target: { value: '40' } })
    fireEvent.click(screen.getByTestId('extrapolation-evaluate'))
    await flush()
    expect(onError).toHaveBeenCalledWith(expect.stringContaining('Tabelle 3'))
  })
})
