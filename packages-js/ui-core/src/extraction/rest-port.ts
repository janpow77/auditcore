import { RestError, type RestOptions } from '@auditcore/common'
import type { ExtractionCatalogue, ExtractionPort, ExtractionRun } from './types'

async function parse<T>(response: Response): Promise<T> {
  const data = (await response.json().catch(() => ({}))) as { error?: { code?: string; message?: string } }
  if (response.ok) return data as T
  throw new RestError(data.error?.message ?? `HTTP ${response.status}`, response.status, data.error?.code ?? 'http_error')
}

/** Port auf den REST-Vertrag `documents_extraction/1` von `auditcore_documents.web` (Starlette oder FastAPI). */
export function createExtractionRestPort(options: RestOptions): ExtractionPort {
  const base = options.baseUrl.replace(/\/$/, '')
  const fetchImpl = options.fetch ?? ((input, init) => globalThis.fetch(input, init))
  const headers = { Accept: 'application/json', ...options.headers }
  return {
    catalogue: async () => parse<ExtractionCatalogue>(await fetchImpl(`${base}/profile`, { method: 'GET', headers })),
    async run(file, filename, profile) {
      const form = new FormData()
      form.append('file', file, filename)
      form.append('profile', profile)
      return parse<ExtractionRun>(await fetchImpl(`${base}/runs`, { method: 'POST', headers, body: form }))
    },
  }
}
