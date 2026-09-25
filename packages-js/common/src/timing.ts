// Zeitsteuerung ohne Framework: Entprellen, Drosseln, Abfragen im Intervall.

/** Entprellte bzw. gedrosselte Funktion mit Steuerung des ausstehenden Aufrufs. */
export interface Debounced<A extends unknown[]> {
  (...args: A): void
  /** Verwirft den ausstehenden Aufruf. */
  cancel(): void
  /** Führt den ausstehenden Aufruf sofort aus. */
  flush(): void
  /** Wartet ein Aufruf? */
  pending(): boolean
}

/** Führt `fn` erst aus, wenn `ms` lang kein weiterer Aufruf kam (letzte Argumente gewinnen). */
export function debounce<A extends unknown[]>(fn: (...args: A) => void, ms: number): Debounced<A> {
  let timer: ReturnType<typeof setTimeout> | undefined
  let lastArgs: A | undefined
  const run = (): void => {
    timer = undefined
    const args = lastArgs
    lastArgs = undefined
    if (args) fn(...args)
  }
  const debounced = (...args: A): void => {
    lastArgs = args
    if (timer !== undefined) clearTimeout(timer)
    timer = setTimeout(run, ms)
  }
  debounced.cancel = (): void => {
    if (timer !== undefined) clearTimeout(timer)
    timer = undefined
    lastArgs = undefined
  }
  debounced.flush = (): void => {
    if (timer === undefined) return
    clearTimeout(timer)
    run()
  }
  debounced.pending = (): boolean => timer !== undefined
  return debounced
}

/** Führt `fn` höchstens alle `ms` aus: sofort beim ersten Aufruf, danach einmal am Ende des Fensters. */
export function throttle<A extends unknown[]>(fn: (...args: A) => void, ms: number): Debounced<A> {
  let last = Number.NEGATIVE_INFINITY
  let timer: ReturnType<typeof setTimeout> | undefined
  let lastArgs: A | undefined
  const run = (): void => {
    timer = undefined
    last = Date.now()
    const args = lastArgs
    lastArgs = undefined
    if (args) fn(...args)
  }
  const throttled = (...args: A): void => {
    lastArgs = args
    const wait = last + ms - Date.now()
    if (wait <= 0 && timer === undefined) run()
    else if (timer === undefined) timer = setTimeout(run, wait)
  }
  throttled.cancel = (): void => {
    if (timer !== undefined) clearTimeout(timer)
    timer = undefined
    lastArgs = undefined
  }
  throttled.flush = (): void => {
    if (timer === undefined) return
    clearTimeout(timer)
    run()
  }
  throttled.pending = (): boolean => timer !== undefined
  return throttled
}

/** Entprellung je Schlüssel; `cancel()` ohne Schlüssel verwirft alle. */
export interface KeyedDebounced<K, A extends unknown[]> {
  (key: K, ...args: A): void
  cancel(key?: K): void
}

/** Entprellen je Schlüssel (z. B. Speichern je Datensatz). */
export function keyedDebounce<K, A extends unknown[]>(fn: (key: K, ...args: A) => void, ms: number): KeyedDebounced<K, A> {
  const entries = new Map<K, Debounced<A>>()
  const keyed = (key: K, ...args: A): void => {
    let entry = entries.get(key)
    if (!entry) {
      entry = debounce((...inner: A) => {
        entries.delete(key)
        fn(key, ...inner)
      }, ms)
      entries.set(key, entry)
    }
    entry(...args)
  }
  keyed.cancel = (key?: K): void => {
    const targets = key === undefined ? [...entries.keys()] : [key]
    for (const target of targets) {
      entries.get(target)?.cancel()
      entries.delete(target)
    }
  }
  return keyed
}

/** Optionen für `poll`. */
export interface PollOptions<T> {
  /** Abstand zwischen zwei Abfragen in ms. */
  intervalMs: number
  /** Abbruch (z. B. beim Verlassen der Seite). */
  signal?: AbortSignal
  /** Ende, sobald die Bedingung erfüllt ist (Standard: nie – bis zum Abbruch). */
  until?: (result: T) => boolean
  /** Wachsender Abstand nach Fehlern: Faktor und Obergrenze. */
  backoff?: { factor: number; maxMs: number }
  /** Höchstzahl Abfragen (Standard unbegrenzt). */
  maxAttempts?: number
}

function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) return reject(signal.reason ?? new Error('abgebrochen'))
    const timer = setTimeout(() => {
      signal?.removeEventListener('abort', onAbort)
      resolve()
    }, ms)
    const onAbort = (): void => {
      clearTimeout(timer)
      reject(signal?.reason ?? new Error('abgebrochen'))
    }
    signal?.addEventListener('abort', onAbort, { once: true })
  })
}

/**
 * Ruft `fn` im Intervall auf, bis `until` erfüllt ist; liefert das letzte
 * Ergebnis. Fehler verlängern bei `backoff` den Abstand; nach
 * `maxAttempts` wird der letzte Fehler geworfen. Abbruch über `signal`.
 */
export async function poll<T>(fn: () => Promise<T>, options: PollOptions<T>): Promise<T> {
  let delay = options.intervalMs
  let lastError: unknown = null
  for (let attempt = 1; attempt <= (options.maxAttempts ?? Number.POSITIVE_INFINITY); attempt += 1) {
    if (options.signal?.aborted) throw options.signal.reason ?? new Error('abgebrochen')
    try {
      const result = await fn()
      if (options.until?.(result)) return result
      delay = options.intervalMs
      lastError = null
    } catch (error) {
      lastError = error
      if (!options.backoff) throw error
      delay = Math.min(delay * options.backoff.factor, options.backoff.maxMs)
    }
    await sleep(delay, options.signal)
  }
  throw lastError ?? new Error('Abfrage ohne Ergebnis beendet')
}
