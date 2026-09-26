import { requestJson, type RestOptions } from '@flowaudit/common'
import type { IdentifiersPort } from './types'

/** Port auf den REST-Vertrag `identifiers_ui/1` von `auditcore_identifiers.web` (Starlette oder FastAPI). */
export function createIdentifiersRestPort(options: RestOptions): IdentifiersPort {
  return {
    catalogue: () => requestJson(options, '/catalogue'),
    check: (request) => requestJson(options, '/check', request),
    checkBatch: (request) => requestJson(options, '/check/batch', request),
  }
}
