/**
 * Vertrag der lokalen JSON-API von `auditcore_runner` (`auditcore-runner ui`,
 * Doku `packages/auditcore_runner/docs/api.md`). Feldnamen wie im Backend.
 */

export type RunnerAnsicht = 'status' | 'einstellungen' | 'werkzeuge' | 'prioritaeten'

/** Stand einer Runner-Klasse im Status. `null`: unbekannt (z. B. GitHub nicht erreichbar). */
export interface RunnerKlasseStatus {
  aktiv: boolean
  max: number
  soll: number | null
  gruende: readonly string[]
  instanzen_aktiv: number
  registriert: number | null
  belegt: number | null
  /** Wartende Jobs der Klasse (sobald das Backend sie liefert). */
  warteschlange?: number | null
}

export interface RunnerAenderung {
  zeit: string
  quelle: string
  wer: string
}

/** `GET /api/status` (Schema `auditcore-runner/status/1`). */
export interface RunnerStatus {
  rechner: string
  profil_version: number
  profil_hash: string
  aenderung: RunnerAenderung
  /** `aus` oder Name der zentralen Verwaltung. */
  sync: string
  ziel: string
  soll_quelle: string
  hardware: Readonly<Record<string, unknown>>
  klassen: Readonly<Record<string, RunnerKlasseStatus>>
  image_vorhanden: boolean
  netz_vorhanden: boolean | null
  netzsperre_aktiv: boolean | null
  unbekannte_runner: readonly string[] | null
  github_rest_kontingent: number | null
  /** Runner-Version im Image und Frist, bis zu der sie aktualisiert sein muss (optional). */
  runner_version?: string | null
  runner_frist?: string | null
  nur_lesen?: boolean
}

/** Profil als JSON (Schema `auditcore-runner/profil/…`); unbekannte Felder bleiben erhalten. */
export type RunnerProfil = Readonly<Record<string, unknown>>

export interface RunnerProblem {
  feld: string
  meldung: string
}

/** `GET /api/profil`. */
export interface RunnerProfilStand {
  profil: RunnerProfil
  profil_hash: string
  hardware: Readonly<Record<string, unknown>>
  probleme: readonly RunnerProblem[]
  netzsperre_befehl: string | null
  nur_lesen?: boolean
}

export interface RunnerDateiAenderung {
  datei: string
  diff: string
}

/** Ergebnis von `POST /api/profil/pruefen` bzw. `…/anwenden`. */
export interface RunnerPruefung {
  gueltig: boolean
  probleme: readonly RunnerProblem[]
  aktive_version: number | null
  aenderungen: readonly RunnerDateiAenderung[]
  schritte: readonly string[]
  netzsperre_befehl: string | null
  angewendet?: boolean
  konflikt?: boolean
  meldung?: string
  version?: number
}

export interface RunnerWerkzeug {
  name: string
  bereich: string
  installation: string
  autofix: boolean
  kosten_minuten: number
  /** Installierte Version im Runner-Image, leer: nicht installiert. */
  im_image: string
}

export interface RunnerWerkzeugEinstellung {
  aktiv: boolean
  zeitlimit_s: number
  prioritaet: number
}

/** Prüfprofil → Werkzeug → Einstellung. */
export type RunnerWerkzeugProfile = Readonly<Record<string, Readonly<Record<string, RunnerWerkzeugEinstellung>>>>

/** `GET /api/werkzeuge`. */
export interface RunnerWerkzeuge {
  werkzeuge: readonly RunnerWerkzeug[]
  profile: RunnerWerkzeugProfile
}

/** Fachlogik hinter der Oberfläche; Vue und React rufen nur diesen Port auf. */
export interface RunnerPort {
  status: () => Promise<RunnerStatus>
  profil: () => Promise<RunnerProfilStand>
  pruefen: (profil: RunnerProfil) => Promise<RunnerPruefung>
  /** Konflikt (HTTP 409) liefert `konflikt: true` statt eines Fehlers. */
  anwenden: (profil: RunnerProfil, erwarteteVersion: number | null) => Promise<RunnerPruefung>
  werkzeuge: () => Promise<RunnerWerkzeuge>
  werkzeugeSpeichern: (profile: RunnerWerkzeugProfile) => Promise<void>
}
