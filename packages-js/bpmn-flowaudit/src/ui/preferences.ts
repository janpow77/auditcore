/**
 * Preferences of this browser (views, panel widths). A blocked or missing
 * storage only loses the preference; reading never throws.
 */

export type PreferenceStorage = Pick<Storage, 'getItem' | 'setItem'>

export function browserStorage(): PreferenceStorage | null {
  try {
    return typeof localStorage === 'undefined' ? null : localStorage
  } catch {
    return null
  }
}

/** Stored choice among `options`; `fallback` when nothing (readable) is stored. */
export function readChoice<T extends string>(key: string, options: readonly T[], fallback: T, storage: PreferenceStorage | null = browserStorage()): T {
  try {
    const value = storage?.getItem(key)
    return (options as readonly string[]).includes(value ?? '') ? (value as T) : fallback
  } catch {
    return fallback
  }
}

export function writePreference(key: string, value: string, storage: PreferenceStorage | null = browserStorage()): void {
  try {
    storage?.setItem(key, value)
  } catch {
    // Private mode or blocked site data: the choice holds for this session only.
  }
}

/** Stored JSON object; `null` when missing or unreadable. */
export function readJson(key: string, storage: PreferenceStorage | null = browserStorage()): Record<string, unknown> | null {
  try {
    const value = JSON.parse(storage?.getItem(key) ?? 'null') as unknown
    return value && typeof value === 'object' && !Array.isArray(value) ? (value as Record<string, unknown>) : null
  } catch {
    return null
  }
}
