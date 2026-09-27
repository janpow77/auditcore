/**
 * Port mit den Antworten des echten Python-Backends (Fixtures von
 * auditcore_sampling.web, erzeugt mit packages/auditcore_sampling/tools/ui_fixtures.py,
 * synthetische Daten aus den Beispielen des Leitfadens).
 */
import type { SampleSizeCatalogue, SampleSizePlan, SampleSizeRequest, SamplesizePort } from '../../src'
import plans from '../fixtures/samplesize-plans.json'
import profiles from '../fixtures/samplesize-profiles.json'

type Recorded = Record<string, { request: SampleSizeRequest; response: SampleSizePlan }>

export const samplesizeCatalogue = profiles as unknown as SampleSizeCatalogue
export const samplesizeRecorded = plans as unknown as Recorded
export const conservativeRequest = samplesizeRecorded['guidance.mus_conservative']!.request
export const stratifiedRequest = samplesizeRecorded['guidance.srs_stratified']!.request

export interface SamplesizeFake extends SamplesizePort {
  calls: SampleSizeRequest[]
}

export function fakeSamplesizePort(failing?: keyof SamplesizePort, message = 'Konfidenzniveau 97.00% ist in Tabelle 4 des Leitfadens nicht enthalten'): SamplesizeFake {
  const calls: SampleSizeRequest[] = []
  const fail = (name: keyof SamplesizePort): void => {
    if (failing === name) throw new Error(message)
  }
  return {
    calls,
    profiles: async () => (fail('profiles'), samplesizeCatalogue),
    plan: async (request) => {
      fail('plan')
      calls.push(request)
      const found = samplesizeRecorded[request.method]
      if (!found) throw new Error(`Keine Antwort für '${request.method}'.`)
      return found.response
    },
  }
}
