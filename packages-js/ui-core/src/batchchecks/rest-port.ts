import { requestFile, requestJson, type RestOptions } from '@auditcore/common'
import type { BatchchecksPort } from './types'

/** Port auf den REST-Vertrag `documents_batch_checks/1` von `auditcore_documents.web` (Starlette oder FastAPI). */
export function createBatchchecksRestPort(options: RestOptions): BatchchecksPort {
  return {
    catalogue: () => requestJson(options, '/catalogue'),
    run: (request) => requestJson(options, '/runs', request),
    exportRun: (request, format) => requestFile(options, '/export', { ...request, format }, `befunde-bestand.${format}`),
  }
}
