// Lesbarer Fehlertext aus beliebigen Fehlern von API-Aufrufen: Axios-Fehler
// (`error.response.data`), FastAPI-`detail` als Text und als 422-Liste
// (`[{loc, msg}]`), die auditcore-Hülle `{error: {code, message}}`,
// `Error`-Objekte und Zeichenketten. Nie „[object Object]“ oder Roh-JSON.

type Json = Readonly<Record<string, unknown>>

function isObject(value: unknown): value is Json {
  return typeof value === 'object' && value !== null
}

function text(value: unknown): string | null {
  return typeof value === 'string' && value.trim() !== '' ? value.trim() : null
}

/** Ort einer Validierungsmeldung ohne den Teil `body`/`query`/`path` (`["body", "betrag"]` → `betrag`). */
function location(loc: unknown): string {
  if (!Array.isArray(loc)) return ''
  const parts = loc.filter((part, index) => !(index === 0 && ['body', 'query', 'path', 'header'].includes(String(part))))
  return parts.map(String).join('.')
}

function validationEntry(entry: unknown): string | null {
  if (!isObject(entry)) return text(entry)
  const message = text(entry.msg) ?? text(entry.message)
  if (!message) return null
  const where = location(entry.loc)
  return where ? `${where}: ${message}` : message
}

/** FastAPI-`detail`: Text, 422-Liste (`[{loc, msg, type}]`) oder Objekt mit `message`. */
export function detailMessage(detail: unknown): string | null {
  if (Array.isArray(detail)) {
    const messages = detail.map(validationEntry).filter((entry): entry is string => entry !== null)
    return messages.length > 0 ? messages.join('; ') : null
  }
  if (isObject(detail)) return text(detail.message) ?? text(detail.msg)
  return text(detail)
}

/** Meldung aus einem Antwortkörper (`detail`, `{error: {message}}`, `message`, reiner Text). */
export function bodyMessage(data: unknown): string | null {
  if (!isObject(data)) return text(data)
  const envelope = isObject(data.error) ? text(data.error.message) : text(data.error)
  return detailMessage(data.detail) ?? envelope ?? text(data.message)
}

function responseOf(error: Json): Json | null {
  return isObject(error.response) ? error.response : null
}

/**
 * Fehlertext für die Oberfläche. Reihenfolge: Antwortkörper
 * (`error.response.data` oder der übergebene Körper selbst), dann
 * `error.message`, sonst `fallback`.
 */
export function errorMessage(error: unknown, fallback: string): string {
  if (typeof error === 'string') return text(error) ?? fallback
  if (!isObject(error)) return fallback
  const response = responseOf(error)
  const fromBody = (response ? bodyMessage(response.data) : null) ?? bodyMessage(isObject(error.data) ? error.data : null)
  if (fromBody) return fromBody
  const own = error instanceof Error ? null : bodyMessage(error)
  return own ?? text(error.message) ?? fallback
}

/** HTTP-Status eines Fehlers (`error.response.status` oder `error.status`); sonst `null`. */
export function httpStatus(error: unknown): number | null {
  if (!isObject(error)) return null
  const response = responseOf(error)
  const status = response ? response.status : error.status
  return typeof status === 'number' && Number.isInteger(status) ? status : null
}
