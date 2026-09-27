import { requestFile, requestJson, type RestOptions } from '@auditcore/common'
import type { ReporttemplatesPort } from './types'

/** Port auf die Vorlagen-Endpunkte von `reporting_ui/1` (`auditcore_reporting.web`, Starlette oder FastAPI). */
export function createReportTemplatesRestPort(options: RestOptions): ReporttemplatesPort {
  const path = (id: string, suffix = ''): string => `/templates/${encodeURIComponent(id)}${suffix}`
  return {
    templates: () => requestJson(options, '/templates'),
    template: (id, version) => requestJson(options, path(id, version ? `?version=${encodeURIComponent(version)}` : '')),
    preview: (id, request) => requestJson(options, path(id, '/preview'), request),
    render: (id, request) => requestFile(options, path(id, '/render'), request, `${id}.${request.format}`),
  }
}
