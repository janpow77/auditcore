import { describe, expect, it } from 'vitest'
import { createExtrapolationController, extrapolationExportsResidual, extrapolationMethod, terMetrics, translator, extrapolationMessages, residualMetrics, residualRemarks } from '../../src'
import { evaluationResult, extrapolationCatalogue, fakeExtrapolationPort, fixtureStrata, fixtureUnits, residualResult, residualWithinResult } from './fake-port'

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
    expect(port.calls.export[0]?.[0].residual).toEqual(port.calls.residual[0])
  })

  it('exportiert ohne RER, solange keine berechnet ist, und verwirft sie bei neuer Hochrechnung und neuen Eingaben', async () => {
    const { created, port } = controller()
    await created.load()
    created.selectMethod('mus.standard')
    created.setConfidence(0.9)
    await created.evaluate()
    await created.exportEvaluation('json')
    expect(port.calls.export[0]?.[0]).not.toHaveProperty('residual')
    created.setResidual({ auditPopulation: '1000', terRate: '1,5', corrections: '20' })
    await created.computeResidual()
    expect(created.store.get().lastResidualRequest).toEqual(port.calls.residual[0])
    await created.evaluate()
    expect(created.store.get().residual).toBeNull()
    expect(created.store.get().lastResidualRequest).toBeNull()
    await created.exportEvaluation('csv')
    expect(port.calls.export[1]?.[0]).not.toHaveProperty('residual')
    await created.computeResidual()
    expect(created.store.get().lastResidualRequest).not.toBeNull()
    created.applyInputs()
    expect(created.store.get().residual).toBeNull()
    expect(created.store.get().lastResidualRequest).toBeNull()
  })

  it('verwirft eine RER-Antwort, die nach neuer Hochrechnung oder neuen Eingaben eintrifft', async () => {
    const { created, port } = controller()
    const answer = port.residual
    const pending: (() => void)[] = []
    port.residual = (body) => new Promise((resolve) => pending.push(() => resolve(answer(body))))
    await created.load()
    created.selectMethod('mus.standard')
    created.setConfidence(0.9)
    await created.evaluate()
    created.setResidual({ terRate: '9' })
    const late = created.computeResidual()
    await created.evaluate()
    pending.shift()?.()
    await late
    expect(created.store.get().residual).toBeNull()
    expect(created.store.get().lastResidualRequest).toBeNull()
    await created.exportEvaluation('csv')
    expect(port.calls.export[0]?.[0]).not.toHaveProperty('residual')
    const afterInputs = created.computeResidual()
    created.applyInputs()
    pending.shift()?.()
    await afterInputs
    expect(created.store.get().residual).toBeNull()
    expect(created.store.get().lastResidualRequest).toBeNull()
  })

  it('verwirft eine RER, die während einer laufenden Hochrechnung gestartet wurde', async () => {
    const { created, port } = controller()
    await created.load()
    created.selectMethod('mus.standard')
    created.setConfidence(0.9)
    await created.evaluate()
    const evaluateAnswer = port.evaluate
    const residualAnswer = port.residual
    let releaseEvaluate: () => void = () => {}
    let releaseResidual: () => void = () => {}
    port.evaluate = (body) => new Promise((resolve) => (releaseEvaluate = () => resolve(evaluateAnswer(body))))
    port.residual = (body) => new Promise((resolve) => (releaseResidual = () => resolve(residualAnswer(body))))
    const evaluating = created.evaluate()
    created.setResidual({ terRate: '9' })
    const late = created.computeResidual()
    releaseEvaluate()
    await evaluating
    releaseResidual()
    await late
    expect(created.store.get().result).not.toBeNull()
    expect(created.store.get().residual).toBeNull()
    expect(created.store.get().lastResidualRequest).toBeNull()
  })

  it('verwirft eine Hochrechnung, die nach neuen Eingaben eintrifft', async () => {
    const { created, port } = controller()
    const answer = port.evaluate
    let release: () => void = () => {}
    port.evaluate = (body) => new Promise((resolve) => (release = () => resolve(answer(body))))
    await created.load()
    created.selectMethod('mus.standard')
    created.setConfidence(0.9)
    const late = created.evaluate()
    created.applyInputs()
    release()
    await late
    expect(created.store.get().result).toBeNull()
    expect(created.store.get().lastRequest).toBeNull()
  })

  it('gibt die RER nur an Backends ab auditcore_extrapolation 0.3.1 in den Export', async () => {
    expect(extrapolationExportsResidual(extrapolationCatalogue)).toBe(true)
    expect(extrapolationExportsResidual({ ...extrapolationCatalogue, library: 'auditcore_extrapolation 0.3.0' })).toBe(false)
    expect(extrapolationExportsResidual({ ...extrapolationCatalogue, library: 'auditcore_extrapolation 0.10.0' })).toBe(true)
    expect(extrapolationExportsResidual({ ...extrapolationCatalogue, library: 'auditcore_extrapolation 1.0.0' })).toBe(true)
    expect(extrapolationExportsResidual(null)).toBe(false)
    const port = fakeExtrapolationPort()
    port.profiles = async () => ({ ...extrapolationCatalogue, library: 'auditcore_extrapolation 0.3.0' })
    const { created } = controller(port)
    await created.load()
    created.selectMethod('mus.standard')
    created.setConfidence(0.9)
    await created.evaluate()
    await created.computeResidual()
    expect(created.store.get().residual).not.toBeNull()
    await created.exportEvaluation('json')
    expect(port.calls.export[0]?.[0]).not.toHaveProperty('residual')
  })

  it('liefert Begründung für „entfällt“ und Hinweise der RER unverändert aus dem Backend', () => {
    const within = residualRemarks(residualWithinResult.residual_error_rate)
    expect(within.notApplicable).toBe('Entfällt: Restfehlerquote nicht über der Signifikanzschwelle von 2 %.')
    expect(within.notes).toHaveLength(2)
    expect(within.notes[0]).toContain('übersteigen den Risikobetrag')
    const above = residualRemarks(residualResult.residual_error_rate)
    expect(above.notApplicable).toBeNull()
    expect(above.notes).toEqual(residualResult.residual_error_rate.notes)
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
    expect(rer[0]).toEqual({ id: 'rer', label: 'Restfehlerquote (RER)', value: '2,29\u00a0%', detail: 'über der Signifikanzschwelle' })
  })
})
