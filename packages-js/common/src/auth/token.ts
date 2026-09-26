// Ablage des Zugangstokens hinter einer schmalen Schnittstelle. Anwendungen
// wählen den Speicher (`local`, `session`, `memory`); Login/Logout bleiben
// app-spezifisch. Speicherzugriffe sind abgesichert (SSR, gesperrter
// Speicher, private Fenster) und fallen auf den Arbeitsspeicher zurück.

/** Rückruf bei Tokenänderung (`null` nach `clear`). */
export type TokenListener = (token: string | null) => void

/** Schnittstelle für Token-Speicher (eigene Umsetzungen, z. B. Cookies, sind möglich). */
export interface TokenStore {
  get(): string | null
  set(token: string): void
  clear(): void
  /** Benachrichtigt bei jeder Änderung; gibt die Abmeldefunktion zurück. */
  subscribe(listener: TokenListener): () => void
}

/** Ablageort des Tokens. */
export type TokenStorageKind = 'local' | 'session' | 'memory'

/** Optionen für `createTokenStore`. */
export interface TokenStoreOptions {
  /** Schlüssel im Web Storage (Standard `flowaudit_token`). */
  key?: string
  storage?: TokenStorageKind
}

interface KeyValue {
  getItem(key: string): string | null
  setItem(key: string, value: string): void
  removeItem(key: string): void
}

function webStorage(kind: TokenStorageKind): KeyValue | null {
  if (kind === 'memory') return null
  try {
    const storage = kind === 'local' ? globalThis.localStorage : globalThis.sessionStorage
    return storage ?? null
  } catch {
    return null
  }
}

function safely<T>(action: () => T, fallback: T): T {
  try {
    return action()
  } catch {
    return fallback
  }
}

/** Token-Speicher über Web Storage oder Arbeitsspeicher (Standard `local`, Schlüssel `flowaudit_token`). */
export function createTokenStore(options: TokenStoreOptions = {}): TokenStore {
  const key = options.key ?? 'flowaudit_token'
  const storage = webStorage(options.storage ?? 'local')
  const listeners = new Set<TokenListener>()
  let memory: string | null = storage ? safely(() => storage.getItem(key), null) : null
  const notify = (): void => listeners.forEach((listener) => listener(memory))
  return {
    get: () => (storage ? safely(() => storage.getItem(key), memory) : memory),
    set(token) {
      memory = token
      if (storage) safely(() => storage.setItem(key, token), undefined)
      notify()
    },
    clear() {
      memory = null
      if (storage) safely(() => storage.removeItem(key), undefined)
      notify()
    },
    subscribe(listener) {
      listeners.add(listener)
      return () => listeners.delete(listener)
    },
  }
}

/** Kopfzeile `Authorization: Bearer …`, leer ohne Token. */
export function bearerHeaders(store: Pick<TokenStore, 'get'>): Record<string, string> {
  const token = store.get()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function decodeBase64Url(segment: string): string | null {
  const base64 = segment.replace(/-/g, '+').replace(/_/g, '/').padEnd(Math.ceil(segment.length / 4) * 4, '=')
  try {
    const binary = globalThis.atob(base64)
    return new TextDecoder().decode(Uint8Array.from(binary, (char) => char.charCodeAt(0)))
  } catch {
    return null
  }
}

/** Nutzdaten eines JWT ohne Signaturprüfung (nur zur Anzeige und Ablaufsteuerung); `null` bei Fehlform. */
export function jwtPayload(token: string): Record<string, unknown> | null {
  const payload = token.split('.')[1]
  const json = payload ? decodeBase64Url(payload) : null
  if (!json) return null
  try {
    const value: unknown = JSON.parse(json)
    return typeof value === 'object' && value !== null && !Array.isArray(value) ? (value as Record<string, unknown>) : null
  } catch {
    return null
  }
}

/** Ablaufzeit (`exp`) eines JWT; `null`, wenn keine lesbar ist. */
export function jwtExpiry(token: string): Date | null {
  const exp = jwtPayload(token)?.exp
  return typeof exp === 'number' && Number.isFinite(exp) ? new Date(exp * 1000) : null
}

/** Bezugszeit und Sicherheitsabstand für `isTokenExpired`. */
export interface ExpiryOptions {
  now?: Date
  /** Sicherheitsabstand in Sekunden (Standard 30). */
  leewaySeconds?: number
}

/** Abgelaufen oder läuft innerhalb des Sicherheitsabstands ab? Tokens ohne `exp` gelten als nicht abgelaufen. */
export function isTokenExpired(token: string, options: ExpiryOptions = {}): boolean {
  const expiry = jwtExpiry(token)
  if (!expiry) return false
  const now = (options.now ?? new Date()).getTime()
  return expiry.getTime() - (options.leewaySeconds ?? 30) * 1000 <= now
}
