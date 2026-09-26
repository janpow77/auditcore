/**
 * Port zur Anwendung. Die Komponente ruft nie selbst `fetch` auf: Anwendungen
 * übergeben einen Port – etwa {@link createSynopsisRestClient} für den
 * REST-Vertrag aus `auditcore_documents.web` – oder eigene Implementierungen.
 */
import { RestError, type FetchLike, type RestOptions } from '@flowaudit/common'
import type { Comparison, ComparisonProfile, ComparisonResult, ComparisonSummary, RowUpdate, ServerExportFormat } from './types'

export interface SynopsisPort {
  /** Vergleich laden (`GET /comparisons/{id}`). */
  load(id: string): Promise<Comparison>
  /** Auswahl/Grund speichern (`PATCH /comparisons/{id}/rows`); liefert den neuen Stand. */
  updateRows?(id: string, rows: readonly RowUpdate[]): Promise<Comparison>
  /** Adresse einer Server-Ausgabe (DOCX, PDF, JSON, Markdown) für einen Download-Link. */
  exportUrl?(id: string, format: ServerExportFormat): string
}

/** Optionen wie bei `src/rest`: `baseUrl` (z. B. `/api/synopsis`), injizierbares `fetch`, Kopfzeilen. */
export type RestClientOptions = RestOptions

export interface CompareFields {
  title?: string
  comparison_type?: 'standard' | 'article_law'
  mode?: 'auto' | 'checklist' | 'text'
  threshold?: number
  include_answers?: boolean
  include_notes?: boolean
  include_editorial?: boolean
  highlight_words?: boolean
  output_sections?: readonly string[]
  profile?: string
}

/** Anfrage von `POST /comparisons/import`: ein fertiges Ergebnis aus der Auftragssteuerung ablegen. */
export interface ImportRequest {
  title?: string
  result: ComparisonResult
}

export interface SynopsisRestClient extends Required<SynopsisPort> {
  profiles(): Promise<ComparisonProfile[]>
  list(): Promise<ComparisonSummary[]>
  create(oldFile: Blob, oldName: string, newFile: Blob, newName: string, fields?: CompareFields): Promise<Comparison>
  /** `POST /comparisons/import`. */
  importResult(request: ImportRequest): Promise<Comparison>
  remove(id: string): Promise<void>
}

async function parse<T>(response: Response): Promise<T> {
  if (response.ok) return (response.status === 204 ? undefined : await response.json()) as T
  let detail = `HTTP ${response.status}`
  try {
    // auditcore_documents.web: {"detail": …}; andere Router: {"error": {"message": …}}.
    const body = (await response.json()) as { detail?: unknown; error?: { message?: unknown } }
    const message = body.detail ?? body.error?.message
    if (typeof message === 'string') detail = message
  } catch {
    // Kein JSON-Körper: Statuszeile genügt.
  }
  throw new RestError(detail, response.status, 'http_error')
}

function formFields(fields: CompareFields): Array<[string, string]> {
  return Object.entries(fields)
    .filter(([, value]) => value !== undefined)
    .map(([key, value]) => [key, Array.isArray(value) ? value.join(',') : String(value)])
}

function asFile(blob: Blob, name: string): File {
  return blob instanceof File && blob.name === name ? blob : new File([blob], name, { type: blob.type })
}

export function createSynopsisRestClient(options: RestClientOptions): SynopsisRestClient {
  const base = options.baseUrl.replace(/\/+$/, '')
  const fetchImpl: FetchLike = options.fetch ?? ((input, init) => globalThis.fetch(input, init))
  const request: FetchLike = (input, init) =>
    fetchImpl(input, { ...init, headers: { Accept: 'application/json', ...options.headers, ...init?.headers } })
  const url = (path: string): string => `${base}${path}`
  const item = (id: string): string => url(`/comparisons/${encodeURIComponent(id)}`)
  const json = { 'Content-Type': 'application/json' }
  return {
    load: async (id) => parse<Comparison>(await request(item(id))),
    updateRows: async (id, rows) =>
      parse<Comparison>(await request(`${item(id)}/rows`, { method: 'PATCH', headers: json, body: JSON.stringify({ rows }) })),
    exportUrl: (id, format) => `${item(id)}/export?format=${encodeURIComponent(format)}`,
    profiles: async () => (await parse<{ items: ComparisonProfile[] }>(await request(url('/profiles')))).items,
    list: async () => (await parse<{ items: ComparisonSummary[] }>(await request(url('/comparisons')))).items,
    async create(oldFile, oldName, newFile, newName, fields = {}) {
      const form = new FormData()
      form.append('old_file', asFile(oldFile, oldName))
      form.append('new_file', asFile(newFile, newName))
      for (const [key, value] of formFields(fields)) form.append(key, value)
      return parse<Comparison>(await request(url('/comparisons'), { method: 'POST', body: form }))
    },
    importResult: async (body) =>
      parse<Comparison>(await request(url('/comparisons/import'), { method: 'POST', headers: json, body: JSON.stringify(body) })),
    async remove(id) {
      await parse<undefined>(await request(item(id), { method: 'DELETE' }))
    },
  }
}
