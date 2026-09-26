import { ref, type Ref } from 'vue'

export interface Runner<P, K extends string> {
  busy: Ref<K | null>
  failure: Ref<string>
  /** Führt eine Portanfrage aus; Fehler landen in `failure` und im Rückruf, Ergebnis sonst `null`. */
  run: <T>(kind: K, task: (port: P) => Promise<T>) => Promise<T | null>
}

/** Gemeinsamer Ablauf für Portanfragen: Beschäftigt-Status, Fehlermeldung, Rückruf. */
export function createRunner<P, K extends string>(port: () => P | null, failed?: (message: string) => void): Runner<P, K> {
  const busy = ref<K | null>(null) as Ref<K | null>
  const failure = ref('')
  async function run<T>(kind: K, task: (active: P) => Promise<T>): Promise<T | null> {
    const active = port()
    if (!active) return null
    busy.value = kind
    failure.value = ''
    try {
      return await task(active)
    } catch (error) {
      failure.value = error instanceof Error ? error.message : String(error)
      failed?.(failure.value)
      return null
    } finally {
      busy.value = null
    }
  }
  return { busy, failure, run }
}
