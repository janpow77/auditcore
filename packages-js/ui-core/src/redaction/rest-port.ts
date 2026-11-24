import { contentDispositionFilename, RestError, type RestOptions } from '@auditcore/common'
import type { RedactionCatalogue, RedactionPlan, RedactionPort, RedactionReport, RedactionResult } from './types'

async function failure(response: Response): Promise<RestError> {
  const data = (await response.json().catch(() => ({}))) as { error?: { code?: string; message?: string } }
  return new RestError(data.error?.message ?? `HTTP ${response.status}`, response.status, data.error?.code ?? 'http_error')
}

const count = (headers: Headers, name: string): number => {
  const value = Number(headers.get(name) ?? '0')
  return Number.isFinite(value) ? value : 0
}

/** Zahlen des Berichts aus den Antwortköpfen `X-Redaction*` (CORS: `Access-Control-Expose-Headers`). */
export function redactionReportFromHeaders(headers: Headers): RedactionReport {
  return {
    redactions: count(headers, 'X-Redactions'),
    areas: count(headers, 'X-Redaction-Areas'),
    hidden: count(headers, 'X-Redaction-Hidden'),
    deselected: count(headers, 'X-Redaction-Deselected'),
    pages: count(headers, 'X-Redaction-Pages'),
    sanitized: headers.get('X-Redaction-Sanitized') === 'true',
    verified: headers.get('X-Redaction-Verified') === 'true',
  }
}

/** Port auf den REST-Vertrag `pdf_redaction/1` von `auditcore_pdf.web` (Starlette oder FastAPI). */
export function createRedactionRestPort(options: RestOptions): RedactionPort {
  const base = options.baseUrl.replace(/\/$/, '')
  const fetchImpl = options.fetch ?? ((input, init) => globalThis.fetch(input, init))
  const headers = { ...options.headers }
  async function send(path: string, file: Blob, filename: string, fields: Record<string, string>, accept: string): Promise<Response> {
    const form = new FormData()
    form.append('file', file, filename)
    for (const [name, value] of Object.entries(fields)) form.append(name, value)
    const response = await fetchImpl(`${base}${path}`, { method: 'POST', headers: { Accept: accept, ...headers }, body: form })
    if (!response.ok) throw await failure(response)
    return response
  }
  return {
    async catalogue() {
      const response = await fetchImpl(`${base}/catalogue`, { method: 'GET', headers: { Accept: 'application/json', ...headers } })
      if (!response.ok) throw await failure(response)
      return (await response.json()) as RedactionCatalogue
    },
    async plan(file, filename, criteria) {
      const response = await send('/plan', file, filename, { criteria: JSON.stringify(criteria) }, 'application/json')
      return (await response.json()) as RedactionPlan
    },
    async preview(file, filename, page) {
      return (await send('/preview', file, filename, { page: String(page) }, 'image/png')).blob()
    },
    async apply(file, filename, selection): Promise<RedactionResult> {
      const response = await send('/apply', file, filename, { selection: JSON.stringify(selection) }, 'application/pdf')
      return {
        blob: await response.blob(),
        filename: contentDispositionFilename(response.headers.get('Content-Disposition')) ?? 'geschwärzt.pdf',
        report: redactionReportFromHeaders(response.headers),
      }
    },
  }
}
