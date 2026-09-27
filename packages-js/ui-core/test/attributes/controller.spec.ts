import { describe, expect, it } from 'vitest'
import { attributesMessages, attributesMetrics, buildAttributesRequest, createAttributesController, EMPTY_ATTRIBUTES_FORM, translator } from '../../src'
import { discoveryResult, fakeAttributesPort, normalResult } from './fake-port'

const t = translator(attributesMessages, 'de')

describe('Merkmalsstichprobe (Leitfaden 7.9)', () => {
  it('prüft die Eingaben', () => {
    const empty = buildAttributesRequest(EMPTY_ATTRIBUTES_FORM)
    expect(empty.ok).toBe(false)
    if (!empty.ok) expect(empty.issues).toMatchObject({ sampleSize: 'required', deviations: 'required', rate: 'required', confidence: 'required', profileId: 'required' })
    const tooMany = buildAttributesRequest({ ...EMPTY_ATTRIBUTES_FORM, sampleSize: '10', deviations: '11', rate: '5', confidence: 0.9, profileId: 'kom_2017_tables' })
    expect(tooMany.ok ? null : tooMany.issues.deviations).toBe('range')
    const discovery = buildAttributesRequest({ ...EMPTY_ATTRIBUTES_FORM, approach: 'discovery', sampleSize: '59', deviations: '0', rate: '5', confidence: 0.95 })
    expect(discovery.ok ? discovery.request : null).toEqual({ approach: 'discovery', deviations: 0, sample_size: 59, confidence_level: 0.95, tolerable_rate: 0.05 })
  })

  it('lädt, wertet aus und meldet Fehler', async () => {
    const port = fakeAttributesPort()
    const events: string[] = []
    const created = createAttributesController({ port: () => port, callbacks: () => ({ evaluated: () => events.push('ok'), failed: (message) => events.push(message) }) })
    await created.load()
    expect(created.store.get().form.profileId).toBe('kom_2017_tables')
    created.update({ sampleSize: '150', deviations: '3', rate: '5', confidence: 0.95 })
    await created.evaluate()
    expect(port.calls[0]).toMatchObject({ approach: 'normal', factor_profile: 'kom_2017_tables', tolerable_rate: 0.05 })
    expect(created.store.get().result?.attributes.conclusion).toBe('supported')
    expect(events).toEqual(['ok'])
    const failing = createAttributesController({ port: () => fakeAttributesPort('profiles') })
    await failing.load()
    expect(failing.store.get().error).toBe('Dienst nicht erreichbar')
  })

  it('zeigt Kennzahlen je Verfahren', () => {
    expect(attributesMetrics(normalResult, t, 'de').map((metric) => metric.id)).toEqual(['rate', 'precision', 'upper', 'threshold'])
    expect(attributesMetrics(discoveryResult, t, 'de').map((metric) => metric.id)).toEqual(['rate', 'upper', 'threshold'])
  })
})
