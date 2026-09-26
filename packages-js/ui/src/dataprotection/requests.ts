import { ref, shallowRef, type Ref, type ShallowRef } from 'vue'
import { RestError } from '../rest'
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

export interface Requests<P> {
  busy: Ref<string | null>
  error: ShallowRef<DataProtectionError | null>
  /** Letzte Erfolgsmeldung (für `aria-live`). */
  notice: Ref<string>
  run: <T>(kind: string, task: (port: P) => Promise<T>) => Promise<T | null>
}

export function asError(error: unknown, hooks: RequestHooks): DataProtectionError {
  if (error instanceof RestError) return { code: error.code, message: error.message, status: error.status }
  const raw = error instanceof Error ? error.message : String(error)
  return { code: 'network_error', message: hooks.networkMessage?.(raw) ?? raw, status: 0 }
}

/** Gemeinsamer Ablauf der Portanfragen beider Komponenten: Beschäftigt-Status, Fehler, Meldung. */
export function createRequests<P>(port: () => P | null, hooks: RequestHooks): Requests<P> {
  const busy = ref<string | null>(null)
  const error = shallowRef<DataProtectionError | null>(null)
  const notice = ref('')
  async function run<T>(kind: string, task: (active: P) => Promise<T>): Promise<T | null> {
    const active = port()
    if (!active) return null
    busy.value = kind
    error.value = null
    try {
      return await task(active)
    } catch (caught) {
      error.value = asError(caught, hooks)
      hooks.onError?.(error.value)
      return null
    } finally {
      busy.value = null
    }
  }
  return { busy, error, notice, run }
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
