import { requestJson, type RestOptions } from '@auditcore/common'
import type { SampleSizeCatalogue, SampleSizePlan, SamplesizePort } from './types'

/** Port auf den REST-Vertrag `auditcore_sampling.guidance/1` (Starlette oder FastAPI). */
export function createSamplesizeRestPort(options: RestOptions): SamplesizePort {
  return {
    profiles: () => requestJson(options, '/guidance/profiles'),
    plan: (request) => requestJson(options, '/guidance/size', request),
  }
}

/**
 * Port im Arbeitsspeicher (Demo, Tests): feste Antworten je Methode; ohne
 * Antwort wird die Anfrage wie vom Backend abgelehnt.
 */
export function createSamplesizeMemoryPort(
  catalogue: SampleSizeCatalogue,
  plans: Readonly<Record<string, SampleSizePlan>> = {},
): SamplesizePort {
  return {
    profiles: async () => catalogue,
    plan: async (request) => {
      const plan = plans[request.method]
      if (!plan) throw new Error(`Keine Antwort für '${request.method}' hinterlegt.`)
      return plan
    },
  }
}
