import { requestFile, requestJson, type RestOptions } from '@auditcore/common'
import type { ReportingPort } from './types'

/** Port auf den REST-Vertrag `reporting_ui/1` von `auditcore_reporting.web` (Starlette oder FastAPI). */
export function createReportingRestPort(options: RestOptions): ReportingPort {
  return {
    profiles: () => requestJson(options, '/profiles'),
    preview: (request) => requestJson(options, '/preview', request),
    exportWorkbook: (request) => requestFile(options, '/export', request, request.filename ?? 'bericht.xlsx'),
  }
}
