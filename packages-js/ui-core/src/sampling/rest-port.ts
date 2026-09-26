import { requestFile, requestJson, type RestOptions } from '@flowaudit/common'
import type { SamplingPort } from './types'

/** Port auf den REST-Vertrag von `auditcore_sampling.web` (Starlette oder FastAPI). */
export function createSamplingRestPort(options: RestOptions): SamplingPort {
  return {
    profiles: () => requestJson(options, '/profiles'),
    size: (request) => requestJson(options, '/size', request),
    allocation: (request) => requestJson(options, '/allocation', request),
    selection: (request) => requestJson(options, '/selection', request),
    exportSelection: (request, format) =>
      requestFile(options, '/selection/export', { ...request, format }, `stichprobe-seed-${request.seed}.${format}`),
  }
}
