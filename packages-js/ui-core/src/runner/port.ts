import { RestError, requestJson, type FetchLike, type RestOptions } from '@auditcore/common'
import type { RunnerPort, RunnerProfil, RunnerProfilStand, RunnerPruefung, RunnerStatus, RunnerWerkzeuge, RunnerWerkzeugProfile } from './types'

/** Kopfzeile, ohne die `auditcore-runner ui` schreibende Anfragen ablehnt. */
export const RUNNER_SCHREIB_KOPF = { 'X-Auditcore-Runner': '1' } as const
export const RUNNER_WERKZEUG_SCHEMA = 'auditcore-runner/werkzeuge/1'

/** Port im Arbeitsspeicher (Demo, Tests); Konflikt, wenn `erwarteteVersion` nicht zur gespeicherten passt. */
export function createRunnerMemoryPort(start: {
  status: RunnerStatus
  profil: RunnerProfilStand
  werkzeuge?: RunnerWerkzeuge
  pruefen?: (profil: RunnerProfil) => RunnerPruefung
}): RunnerPort {
  let stand = start.profil
  let werkzeuge = start.werkzeuge ?? { werkzeuge: [], profile: {} }
  const pruefen = start.pruefen ?? (() => ({ gueltig: true, probleme: [], aktive_version: versionOf(stand.profil), aenderungen: [], schritte: [], netzsperre_befehl: null }))
  return {
    status: async () => ({ ...start.status, profil_version: versionOf(stand.profil) }),
    profil: async () => stand,
    pruefen: async (profil) => pruefen(profil),
    async anwenden(profil, erwarteteVersion) {
      const aktuell = versionOf(stand.profil)
      const ergebnis = pruefen(profil)
      if (erwarteteVersion !== null && erwarteteVersion !== aktuell) {
        return { ...ergebnis, angewendet: false, konflikt: true, meldung: `Version ${aktuell}, erwartet ${erwarteteVersion}` }
      }
      if (!ergebnis.gueltig) return { ...ergebnis, angewendet: false, konflikt: false }
      stand = { ...stand, profil: { ...profil, version: aktuell + 1 } }
      return { ...ergebnis, angewendet: true, konflikt: false, version: aktuell + 1 }
    },
    werkzeuge: async () => werkzeuge,
    async werkzeugeSpeichern(profile) {
      werkzeuge = { ...werkzeuge, profile }
    },
  }
}

/** Die Runner-API meldet Fehler als `{"fehler": "…"}`; umgesetzt in die auditcore-Hülle `{error: {message}}`. */
function fehlerHuelle(basis: FetchLike | undefined): FetchLike {
  const fetchImpl: FetchLike = basis ?? ((input, init) => globalThis.fetch(input, init))
  return async (input, init) => {
    const response = await fetchImpl(input, init)
    if (response.ok) return response
    const data: unknown = await response.clone().json().catch(() => null)
    const fehler = typeof data === 'object' && data !== null ? (data as { fehler?: unknown }).fehler : undefined
    if (typeof fehler !== 'string') return response
    return new Response(JSON.stringify({ error: { code: `http_${response.status}`, message: fehler } }), {
      status: response.status,
      headers: { 'Content-Type': 'application/json' },
    })
  }
}

function versionOf(profil: RunnerProfil): number {
  return typeof profil.version === 'number' ? profil.version : 0
}

/**
 * Port auf die JSON-API von `auditcore-runner ui` (Basis z. B. `/api`).
 * Schreibende Aufrufe senden `X-Auditcore-Runner: 1`; HTTP 409 beim Anwenden
 * wird zum Ergebnis mit `konflikt: true`.
 */
export function createRunnerRestPort(rest: RestOptions): RunnerPort {
  const options: RestOptions = { ...rest, fetch: fehlerHuelle(rest.fetch) }
  const schreiben: RestOptions = { ...options, headers: { ...options.headers, ...RUNNER_SCHREIB_KOPF } }
  return {
    status: () => requestJson<RunnerStatus>(options, '/status'),
    profil: () => requestJson<RunnerProfilStand>(options, '/profil'),
    pruefen: (profil) => requestJson<RunnerPruefung>(schreiben, '/profil/pruefen', { profil }),
    async anwenden(profil, erwarteteVersion) {
      try {
        return await requestJson<RunnerPruefung>(schreiben, '/profil/anwenden', { profil, erwartete_version: erwarteteVersion })
      } catch (error) {
        if (error instanceof RestError && error.status === 409) {
          return { gueltig: true, probleme: [], aktive_version: null, aenderungen: [], schritte: [], netzsperre_befehl: null, angewendet: false, konflikt: true, meldung: error.message }
        }
        throw error
      }
    },
    werkzeuge: () => requestJson<RunnerWerkzeuge>(options, '/werkzeuge'),
    async werkzeugeSpeichern(profile: RunnerWerkzeugProfile) {
      await requestJson<unknown>(schreiben, '/werkzeuge', { schema: RUNNER_WERKZEUG_SCHEMA, profile })
    },
  }
}
