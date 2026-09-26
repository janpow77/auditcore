import { describe, expect, it } from 'vitest'
import { createExtrapolationController, extrapolationMethod, terMetrics, translator, extrapolationMessages, residualMetrics } from '../../src'
import { evaluationResult, fakeExtrapolationPort, fixtureStrata, fixtureUnits, residualResult } from './fake-port'

function controller(port = fakeExtrapolationPort()) {
  const events: string[] = []
  const created = createExtrapolationController({
    port: () => port,
    strata: () => fixtureStrata,
    units: () => fixtureUnits,
    format: (value) => String(value),
    callbacks: () => ({ evaluated: () => events.push('evaluated'), residualComputed: () => events.push('residual'), failed: (message) => events.push(message) }),
  })
  return { created, port, events }
}

describe('createExtrapolationController', () => {
  it('lädt den Katalog, übernimmt die Eingaben und wählt keine Methode vor', async () => {
    const { created } = controller()
    await created.load()
    const state = created.store.get()
    expect(state.form.methodId).toBe('')
    expect(state.form.profileId).toBe('kom_2017_tables')
    expect(state.form.materiality).toBe('2')
    expect(state.form.units).toHaveLength(5)
  })

  it('rechnet hoch, füllt das RER-Formular und berechnet die RER getrennt', async () => {
    const { created, port, events } = controller()
    await created.load()
    await created.evaluate()
    expect(created.store.get().formError).toBe('method')
    created.selectMethod('mus.standard')
    created.setConfidence(0.9)
    await created.evaluate()
    expect(port.calls.evaluate).toHaveLength(1)
    expect(extrapolationMethod(created.store.get())?.id).toBe('mus.standard')
    expect(created.store.get().residualForm.terRate).toBe('1.6')
    created.setResidual({ terRate: '2,5', auditPopulation: '1000', corrections: '2,1' })
    await created.computeResidual()
    expect(port.calls.residual[0]).toMatchObject({ audit_population: 1000, total_error_rate: 0.025, financial_corrections: 2.1 })
    expect(created.store.get().residual).toBe(residualResult)
    expect(events).toEqual(['evaluated', 'residual'])
    const file = await created.exportEvaluation('csv')
    expect(file?.filename).toBe('hochrechnung.csv')
  })

  it('behält das Konfidenzniveau nur, wenn die neue Methode es erlaubt', async () => {
    const { created } = controller()
    await created.load()
    created.selectMethod('srs.ratio')
    created.setConfidence(0.6)
    created.selectMethod('mus.conservative')
    expect(created.store.get().form.confidence).toBe(0.6)
    created.setConfidence(0.95)
    created.selectMethod('mus.standard')
    expect(created.store.get().form.confidence).toBe(0.95)
  })

  it('Zeilen hinzufügen, ändern und entfernen', async () => {
    const { created } = controller()
    await created.load()
    created.addStratum()
    created.updateStratum(1, { name: 'Zwei' })
    created.addUnit()
    expect(created.store.get().form.units.at(-1)?.stratum).toBe('Programm')
    created.removeUnit(5)
    created.removeStratum(1)
    expect(created.store.get().form.strata).toHaveLength(1)
    expect(created.store.get().form.units).toHaveLength(5)
  })

  it('meldet abgelehnte Anfragen', async () => {
    const { created, events } = controller(fakeExtrapolationPort('evaluate'))
    await created.load()
    created.selectMethod('nonstatistical.pps')
    created.updateStratum(0, { populationSize: '36' })
    await created.evaluate()
    expect(created.store.get().error).toContain('Tabelle 3')
    expect(events[0]).toContain('Tabelle 3')
  })

  it('Kennzahlen der TER und RER', () => {
    const t = translator(extrapolationMessages, 'de')
    const metrics = terMetrics(evaluationResult, t, 'de')
    expect(metrics.map((metric) => metric.id)).toEqual(['projected', 'systemic', 'anomalous', 'excluded', 'total', 'ter', 'tolerable', 'precision', 'upper'])
    expect(metrics.find((metric) => metric.id === 'ter')?.value).toBe('1,60\u00a0%')
    const rer = residualMetrics(residualResult.residual_error_rate, t, 'de')
    expect(rer[0]).toEqual({ id: 'rer', label: 'Restfehlerquote (RER)', value: '2,29\u00a0%', detail: 'über der Wesentlichkeitsschwelle' })
  })
})
