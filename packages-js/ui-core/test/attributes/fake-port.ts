/** Port mit Antworten des echten Python-Backends (tools/ui_fixtures.py, synthetische Daten). */
import type { AttributesCatalogue, AttributesPort, AttributesRequest, AttributesResult } from '../../src'
import discovery from '../fixtures/attributes-discovery.json'
import normal from '../fixtures/attributes-normal.json'
import profiles from '../fixtures/extrapolation-profiles.json'

export const attributesCatalogue = profiles as unknown as AttributesCatalogue
export const normalResult = normal as unknown as AttributesResult
export const discoveryResult = discovery as unknown as AttributesResult

export interface AttributesFake extends AttributesPort {
  calls: AttributesRequest[]
}

export function fakeAttributesPort(failing?: keyof AttributesPort, message = 'Dienst nicht erreichbar'): AttributesFake {
  const calls: AttributesRequest[] = []
  return {
    calls,
    profiles: async () => {
      if (failing === 'profiles') throw new Error(message)
      return attributesCatalogue
    },
    evaluate: async (request) => {
      if (failing === 'evaluate') throw new Error(message)
      calls.push(request)
      return request.approach === 'normal' ? normalResult : discoveryResult
    },
  }
}
