import { requestJson, type RestOptions } from '@flowaudit/common'
import type { BenfordPort } from './types'

/** Port auf den REST-Vertrag von `auditcore_statistics.web` (Starlette oder FastAPI). */
export function createBenfordRestPort(options: RestOptions): BenfordPort {
  return {
    profiles: () => requestJson(options, '/profiles'),
    analyse: (request) => requestJson(options, '/analyze', request),
  }
}
