/**
 * Kleiner JSON-Client für die REST-Ports der Fachkomponenten. Komponenten
 * rufen ihn nie selbst auf, sondern erhalten einen Port; dieser Client ist
 * nur die mitgelieferte Standardumsetzung. `fetch` ist injizierbar
 * (Authentisierung, Tests, Proxy).
 */

export type FetchLike = (input: string, init?: RequestInit) => Promise<Response>

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

async function dispatch(options: RestOptions, path: string, init: RequestInit): Promise<Response> {
  const fetchImpl = options.fetch ?? ((input, request) => globalThis.fetch(input, request))
  const response = await fetchImpl(url(options, path), init)
  if (response.ok) return response
  throw await toError(response)
}

function send(options: RestOptions, path: string, body?: unknown): Promise<Response> {
  const init: RequestInit = body === undefined
    ? { method: 'GET', headers: { Accept: 'application/json', ...options.headers } }
    : {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json', ...options.headers },
        body: JSON.stringify(body),
      }
  return dispatch(options, path, init)
}

async function toError(response: Response): Promise<RestError> {
  try {
    const data = (await response.json()) as { error?: { code?: string; message?: string } }
    const message = data.error?.message ?? `HTTP ${response.status}`
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

/** POST mit Rohdaten (z. B. eine hochgeladene Datei) und JSON-Antwort. */
export async function requestUpload<T>(options: RestOptions, path: string, body: Blob, contentType: string): Promise<T> {
  const response = await dispatch(options, path, {
    method: 'POST',
    headers: { 'Content-Type': contentType, Accept: 'application/json', ...options.headers },
    body,
  })
  return (await response.json()) as T
}

/** POST mit Dateiantwort; der Dateiname kommt aus `Content-Disposition`. */
export async function requestFile(options: RestOptions, path: string, body: unknown, fallbackName: string): Promise<DownloadFile> {
  const response = await send(options, path, body)
  const disposition = response.headers.get('Content-Disposition') ?? ''
  const match = /filename="([^"]+)"/.exec(disposition)
  return {
    blob: await response.blob(),
    filename: match?.[1] ?? fallbackName,
    mediaType: response.headers.get('Content-Type') ?? 'application/octet-stream',
  }
}
