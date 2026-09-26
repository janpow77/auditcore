import { bodyMessage } from './error'

// Kleiner JSON-Client für die REST-Ports der Fachkomponenten. Komponenten
// rufen ihn nie selbst auf, sondern erhalten einen Port; dieser Client ist
// nur die mitgelieferte Standardumsetzung. `fetch` ist injizierbar
// (Authentisierung, Tests, Proxy).

/** Signatur von `fetch` (injizierbar für Authentisierung, Tests, Proxy). */
export type FetchLike = (input: string, init?: RequestInit) => Promise<Response>

/** Basis-URL, `fetch` und Kopfzeilen eines REST-Ports. */
export interface RestOptions {
  /** Basis-URL der Router, z. B. `/api/sampling`. */
  baseUrl: string
  fetch?: FetchLike
  /** Zusätzliche Kopfzeilen, z. B. CSRF- oder Authentisierungstoken. */
  headers?: Readonly<Record<string, string>>
}

/** Fehler der REST-Schnittstelle mit Status, Code und deutscher Meldung des Servers. */
export class RestError extends Error {
  constructor(message: string, readonly status: number, readonly code: string) {
    super(message)
    this.name = 'RestError'
  }
}

/** Heruntergeladene Datei (Export). */
export interface DownloadFile {
  blob: Blob
  filename: string
  mediaType: string
}

function url(options: RestOptions, path: string): string {
  return `${options.baseUrl.replace(/\/$/, '')}${path}`
}

async function send(options: RestOptions, path: string, body?: unknown): Promise<Response> {
  const fetchImpl = options.fetch ?? ((input, init) => globalThis.fetch(input, init))
  const init: RequestInit = body === undefined
    ? { method: 'GET', headers: { Accept: 'application/json', ...options.headers } }
    : {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json', ...options.headers },
        body: JSON.stringify(body),
      }
  const response = await fetchImpl(url(options, path), init)
  if (response.ok) return response
  throw await toError(response)
}

async function toError(response: Response): Promise<RestError> {
  try {
    const data = (await response.json()) as { error?: { code?: string; message?: string } }
    const message = data.error?.message ?? bodyMessage(data) ?? `HTTP ${response.status}`
    return new RestError(message, response.status, data.error?.code ?? 'http_error')
  } catch {
    return new RestError(`HTTP ${response.status}`, response.status, 'http_error')
  }
}

/** GET/POST mit JSON-Antwort. Der Antworttyp ist der dokumentierte REST-Vertrag. */
export async function requestJson<T>(options: RestOptions, path: string, body?: unknown): Promise<T> {
  const response = await send(options, path, body)
  return (await response.json()) as T
}

/** POST mit Dateiantwort; der Dateiname kommt aus `Content-Disposition`. */
export async function requestFile(options: RestOptions, path: string, body: unknown, fallbackName: string): Promise<DownloadFile> {
  const response = await send(options, path, body)
  return {
    blob: await response.blob(),
    filename: contentDispositionFilename(response.headers.get('Content-Disposition')) ?? fallbackName,
    mediaType: response.headers.get('Content-Type') ?? 'application/octet-stream',
  }
}

function decodeExtended(value: string): string | null {
  const match = /^([\w-]+)'[^']*'(.+)$/.exec(value.trim().replace(/^"|"$/g, ''))
  if (!match) return null
  try {
    return decodeURIComponent(match[2] ?? '')
  } catch {
    return null
  }
}

/**
 * Dateiname aus `Content-Disposition`: `filename*=UTF-8''…` (RFC 5987, Umlaute)
 * vor `filename="…"` und `filename=…`; ohne Angabe `null`.
 */
export function contentDispositionFilename(header: string | null | undefined): string | null {
  if (!header) return null
  const extended = /filename\*\s*=\s*([^;]+)/i.exec(header)
  const decoded = extended?.[1] ? decodeExtended(extended[1]) : null
  if (decoded) return decoded
  const quoted = /filename\s*=\s*"([^"]+)"/i.exec(header)
  if (quoted?.[1]) return quoted[1]
  const plain = /filename\s*=\s*([^;\s]+)/i.exec(header)
  return plain?.[1] ?? null
}
