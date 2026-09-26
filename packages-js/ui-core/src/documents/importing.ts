/**
 * Import eines fertigen Vergleichsergebnisses (`POST /comparisons/import`):
 * akzeptiert die JSON-Ausgabe (`export?format=json`, ein `ComparisonResult`),
 * einen gespeicherten Vergleich (`{id, title, result}`) oder die
 * Anfrageform `{title?, result}`. Die fachliche Prüfung macht der Server.
 */
import type { ImportRequest } from '../synopsis/port'
import type { ComparisonResult } from '../synopsis/types'

export type ImportParse =
  | { ok: true; request: ImportRequest }
  | { ok: false; key: 'importUnreadable' | 'importInvalid' }

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

/** Kennzeichen eines `ComparisonResult.to_dict()`; Einzelheiten prüft `ComparisonResult.from_dict`. */
export function looksLikeResult(value: unknown): value is ComparisonResult {
  return (
    isRecord(value) &&
    Array.isArray(value.rows) &&
    typeof value.old_filename === 'string' &&
    typeof value.new_filename === 'string'
  )
}

function withTitle(result: ComparisonResult, title: unknown): ImportRequest {
  return typeof title === 'string' && title.trim() ? { title: title.trim(), result } : { result }
}

export function parseImport(text: string): ImportParse {
  let data: unknown
  try {
    data = JSON.parse(text)
  } catch {
    return { ok: false, key: 'importUnreadable' }
  }
  if (looksLikeResult(data)) return { ok: true, request: { result: data } }
  if (isRecord(data) && looksLikeResult(data.result)) return { ok: true, request: withTitle(data.result, data.title) }
  return { ok: false, key: 'importInvalid' }
}
