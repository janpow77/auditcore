import { requestFile, requestJson, type RestOptions } from '@flowaudit/common'
import type { ExtrapolationPort } from './types'

/** Port auf den REST-Vertrag von `auditcore_extrapolation.web` (Starlette oder FastAPI). */
export function createExtrapolationRestPort(options: RestOptions): ExtrapolationPort {
  return {
    profiles: () => requestJson(options, '/profiles'),
    evaluate: (request) => requestJson(options, '/evaluate', request),
    residual: (request) => requestJson(options, '/residual', request),
    exportEvaluation: (request, format) =>
      requestFile(options, '/evaluate/export', { ...request, format }, `hochrechnung-${request.method}.${format}`),
  }
}
