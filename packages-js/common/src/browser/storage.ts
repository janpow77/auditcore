// JSON-Ablage im Web Storage mit Präfix und Versionsnummer. Jeder Zugriff
// ist abgesichert: gesperrter Speicher, private Fenster, volle Quote oder
// fehlerhaftes JSON ergeben den Rückfallwert statt einer Ausnahme.

/** Präfix, Version und Speicherart für `safeStorage`. */
export interface SafeStorageOptions {
  /** Schlüsselpräfix, z. B. App-Name (Standard `flowaudit`). */
  prefix?: string
  /** Datenversion; ältere Einträge werden ignoriert (Standard 1). */
  version?: number
  storage?: 'local' | 'session'
}

/** Abgesicherte JSON-Ablage; Fehler ergeben den Rückfallwert. */
export interface SafeStorage {
  get<T>(key: string, fallback: T): T
  set(key: string, value: unknown): boolean
  remove(key: string): void
}

interface Envelope {
  v: number
  data: unknown
}

function resolveStorage(kind: 'local' | 'session'): Storage | null {
  try {
    return (kind === 'local' ? globalThis.localStorage : globalThis.sessionStorage) ?? null
  } catch {
    return null
  }
}

/** Abgesicherte JSON-Ablage (`localStorage` oder `sessionStorage`). */
export function safeStorage(options: SafeStorageOptions = {}): SafeStorage {
  const prefix = options.prefix ?? 'flowaudit'
  const version = options.version ?? 1
  const storage = (): Storage | null => resolveStorage(options.storage ?? 'local')
  const full = (key: string): string => `${prefix}:${key}`
  return {
    get<T>(key: string, fallback: T): T {
      try {
        const raw = storage()?.getItem(full(key))
        if (raw === null || raw === undefined) return fallback
        const parsed = JSON.parse(raw) as Partial<Envelope>
        return parsed.v === version ? (parsed.data as T) : fallback
      } catch {
        return fallback
      }
    },
    set(key, value) {
      try {
        const target = storage()
        if (!target) return false
        target.setItem(full(key), JSON.stringify({ v: version, data: value } satisfies Envelope))
        return true
      } catch {
        return false
      }
    },
    remove(key) {
      try {
        storage()?.removeItem(full(key))
      } catch {
        // Speicher gesperrt: nichts zu entfernen.
      }
    },
  }
}
