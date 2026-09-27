import { describe, expect, it } from 'vitest'
import { buildRequest, createSamplesizeController, createSamplesizeMemoryPort, formFromRequest, methodById, samplesizeAllocation, samplesizeDerivation, samplesizeFields, samplesizeSummary, samplesizeMessages, translator, type SampleSizeRequest, type SamplesizePort } from '../../src'
import { conservativeRequest, fakeSamplesizePort, samplesizeCatalogue, samplesizeRecorded, stratifiedRequest } from './fake-port'

const t = translator(samplesizeMessages, 'de')

function controller(port: SamplesizePort | null = fakeSamplesizePort(), request?: SampleSizeRequest) {
  const events: string[] = []
  const created = createSamplesizeController({
    port: () => port,
    request: () => request,
    callbacks: () => ({ planned: (plan) => events.push(`n=${plan.sample_size}`), failed: (message) => events.push(message) }),
  })
  return { created, events }
}

describe('createSamplesizeController', () => {
  it('lädt den Katalog, wählt die Methode und rechnet im Backend', async () => {
    const port = fakeSamplesizePort()
    const { created, events } = controller(port)
    await created.load()
    created.selectMethod('guidance.mus_conservative')
    expect(created.store.get().form.values).toEqual({ materiality_rate: '2' })
    for (const [field, text] of [['factor_profile', 'kom_2017_tables'], ['confidence_level', '0.9'], ['book_value', '4.199.882.024'], ['anticipated_error_rate', '0,2']] as const) {
      created.setValue(field, text)
    }
    await created.calculate()
    expect(port.calls[0]).toEqual(conservativeRequest)
    expect(events).toEqual(['n=136'])
    const plan = created.store.get().plan!
    expect(samplesizeSummary(plan, t, 'de')[0]).toEqual({ key: 'Stichprobenumfang', text: '136' })
    expect(samplesizeDerivation(plan, 'de')[0]).toEqual(['Zuverlässigkeitsfaktor', 'RF', '2,31', 'EGESIF_16-0014-01, Tabelle 4'])
  })

  it('meldet fehlende und ungültige Angaben, ohne das Backend zu fragen', async () => {
    const port = fakeSamplesizePort()
    const { created } = controller(port)
    await created.load()
    created.selectMethod('guidance.srs')
    created.setValue('population_size', '12,5')
    await created.calculate()
    const issues = created.store.get().issues
    expect(issues.population_size).toBe('invalid')
    expect(issues.factor_profile).toBe('required')
    expect(port.calls).toHaveLength(0)
    const fields = samplesizeFields(created.store.get(), t, 'de')
    expect(fields.find((field) => field.key === 'confidence_level')?.options.map((o) => o.label.replace(/\s/g, ' '))).toEqual(['60 %', '70 %', '80 %', '90 %', '95 %'])
  })

  it('belegt aus einer Anfrage vor und verwaltet Schichten', async () => {
    const { created } = controller(fakeSamplesizePort(), stratifiedRequest)
    await created.load()
    const form = created.store.get().form
    expect(form.strata).toHaveLength(3)
    expect(form.values.anticipated_error_rate).toBe('1,8')
    created.addStratum()
    created.setStratum(3, { name: '  ' })
    created.removeStratum(0)
    expect(created.store.get().form.strata).toHaveLength(3)
    const method = methodById(samplesizeCatalogue, 'guidance.srs_stratified')!
    const rebuilt = buildRequest(formFromRequest(stratifiedRequest, samplesizeCatalogue), method)
    expect(rebuilt).toEqual({ request: stratifiedRequest })
    const plan = samplesizeRecorded['guidance.srs_stratified']!.response
    expect(samplesizeAllocation(plan, t, 'de').map((row) => row[1])).toEqual(['90', '31', '5'])
  })

  it('meldet Ablehnungen des Backends und des Ports', async () => {
    const { created, events } = controller(fakeSamplesizePort('plan'), conservativeRequest)
    await created.load()
    await created.calculate()
    expect(created.store.get().error).toContain('Tabelle 4')
    expect(events).toHaveLength(1)
    const memory = controller(createSamplesizeMemoryPort(samplesizeCatalogue), conservativeRequest)
    await memory.created.load()
    await memory.created.calculate()
    expect(memory.created.store.get().error).toContain('Keine Antwort')
  })

  it('ohne Port: nichts geladen, Berechnen ohne Methode wirkungslos', async () => {
    const { created, events } = controller(null)
    await created.load()
    await created.calculate()
    expect(created.store.get().catalogue).toBeNull()
    expect(events).toEqual([])
  })
})
