import { requestJson, type RestOptions } from '@auditcore/common'
import type { AttributesPort } from './types'

/** Port auf `auditcore_extrapolation.web` (`GET /profiles`, `POST /attributes`). */
export function createAttributesRestPort(options: RestOptions): AttributesPort {
  return {
    profiles: () => requestJson(options, '/profiles'),
    evaluate: (request) => requestJson(options, '/attributes', request),
  }
}
