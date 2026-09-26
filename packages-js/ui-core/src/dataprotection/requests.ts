import { RestError } from '@flowaudit/common'
import { dataprotectionMessages, type DataProtectionKey, type DataProtectionTranslate } from './messages'

/** Fehler einer Portanfrage: Code und Meldung des Servers bzw. `network_error` mit Status 0. */
export interface DataProtectionError {
  code: string
  message: string
  status: number
}

export interface RequestHooks {
  onError?: (error: DataProtectionError) => void
  /** Meldung für Fehler ohne Serverantwort (Netz, Programmfehler). */
  networkMessage?: (message: string) => string
}

export function asError(error: unknown, hooks: RequestHooks): DataProtectionError {
  if (error instanceof RestError) return { code: error.code, message: error.message, status: error.status }
  const raw = error instanceof Error ? error.message : String(error)
  return { code: 'network_error', message: hooks.networkMessage?.(raw) ?? raw, status: 0 }
}

/** Übersetzter Status (`entwurf`, `freigegeben`, …); unbekannte Werte bleiben stehen. */
export function statusLabel(t: DataProtectionTranslate, status: string): string {
  const key = `status_${status}`
  return key in dataprotectionMessages.de ? t(key as DataProtectionKey) : status
}

export function prefixedLabel(t: DataProtectionTranslate, prefix: string, value: string, fallback = value): string {
  const key = `${prefix}_${value}`
  return key in dataprotectionMessages.de ? t(key as DataProtectionKey) : fallback
}
