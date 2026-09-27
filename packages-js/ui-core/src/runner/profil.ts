// Reine Hilfen für den Profil-Entwurf: Werte lesen und unveränderlich setzen,
// Unterschiede zweier Stände, Prioritäten verschieben. Keine Fachregeln –
// gültig ist, was `POST /api/profil/pruefen` sagt.

import type { RunnerProfil } from './types'

export type RunnerPfad = readonly (string | number)[]

export interface RunnerPrioritaet {
  klasse: string
  rang: number
  verdraengbar: boolean
  min: number
}

export interface RunnerUnterschied {
  pfad: string
  entwurf: string
  gespeichert: string
}

/** Felder, die das Backend beim Anwenden selbst setzt; für Unterschiede und „geändert“ ohne Belang. */
const VERWALTET = new Set(['version', 'aenderung'])

function isObject(value: unknown): value is Readonly<Record<string, unknown>> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

export function runnerWert(profil: RunnerProfil | null | undefined, pfad: RunnerPfad): unknown {
  let current: unknown = profil
  for (const teil of pfad) {
    if (Array.isArray(current) && typeof teil === 'number') current = current[teil]
    else if (isObject(current) && typeof teil === 'string') current = current[teil]
    else return undefined
  }
  return current
}

function setzeIn(container: unknown, pfad: RunnerPfad, wert: unknown): unknown {
  if (pfad.length === 0) return wert
  const [kopf, ...rest] = pfad
  if (typeof kopf === 'number') {
    const liste = Array.isArray(container) ? [...(container as unknown[])] : []
    liste[kopf] = setzeIn(liste[kopf], rest, wert)
    return liste
  }
  const objekt = isObject(container) ? { ...container } : {}
  objekt[kopf as string] = setzeIn(objekt[kopf as string], rest, wert)
  return objekt
}

/** Neuer Entwurf mit geändertem Wert; der alte bleibt unverändert. */
export function runnerSetze(profil: RunnerProfil, pfad: RunnerPfad, wert: unknown): RunnerProfil {
  return setzeIn(profil, pfad, wert) as RunnerProfil
}

function flach(wert: unknown, prefix: string, ziel: Map<string, string>): void {
  if (isObject(wert)) {
    for (const [key, inner] of Object.entries(wert)) {
      if (!prefix && VERWALTET.has(key)) continue
      flach(inner, prefix ? `${prefix}.${key}` : key, ziel)
    }
    return
  }
  ziel.set(prefix, JSON.stringify(wert ?? null))
}

/** Feldweise Unterschiede (Pfad in Punktschreibweise), sortiert; ohne `version` und `aenderung`. */
export function runnerUnterschiede(entwurf: RunnerProfil, gespeichert: RunnerProfil): RunnerUnterschied[] {
  const a = new Map<string, string>()
  const b = new Map<string, string>()
  flach(entwurf, '', a)
  flach(gespeichert, '', b)
  const pfade = [...new Set([...a.keys(), ...b.keys()])].sort()
  return pfade
    .filter((pfad) => a.get(pfad) !== b.get(pfad))
    .map((pfad) => ({ pfad, entwurf: a.get(pfad) ?? '–', gespeichert: b.get(pfad) ?? '–' }))
}

export function runnerGeaendert(entwurf: RunnerProfil | null, gespeichert: RunnerProfil | null): boolean {
  if (!entwurf || !gespeichert) return false
  return runnerUnterschiede(entwurf, gespeichert).length > 0
}

export function runnerVersion(profil: RunnerProfil | null | undefined): number {
  const version = runnerWert(profil, ['version'])
  return typeof version === 'number' ? version : 0
}

/** Prioritäten des Entwurfs nach Rang (1 = höchster), fehlerhafte Einträge übersprungen. */
export function runnerPrioritaeten(profil: RunnerProfil | null | undefined): RunnerPrioritaet[] {
  const liste = runnerWert(profil, ['prioritaeten'])
  if (!Array.isArray(liste)) return []
  return liste
    .filter(isObject)
    .map((eintrag) => ({
      klasse: String(eintrag.klasse ?? ''),
      rang: typeof eintrag.rang === 'number' ? eintrag.rang : 0,
      verdraengbar: eintrag.verdraengbar !== false,
      min: typeof eintrag.min === 'number' ? eintrag.min : 0,
    }))
    .sort((x, y) => x.rang - y.rang || x.klasse.localeCompare(y.klasse))
}

/** Eintrag an Position `index` um eine Stelle verschieben; Ränge werden fortlaufend neu vergeben. */
export function runnerVerschiebe(profil: RunnerProfil, index: number, richtung: -1 | 1): RunnerProfil {
  const liste = runnerPrioritaeten(profil)
  const ziel = index + richtung
  if (index < 0 || ziel < 0 || ziel >= liste.length) return profil
  const neu = [...liste]
  ;[neu[index], neu[ziel]] = [neu[ziel] as RunnerPrioritaet, neu[index] as RunnerPrioritaet]
  return runnerSetze(profil, ['prioritaeten'], neu.map((eintrag, i) => ({ ...eintrag, rang: i + 1 })))
}

/** Eigenschaft eines Prioritätseintrags (Position in der sortierten Liste) ändern. */
export function runnerPrioritaetSetze(profil: RunnerProfil, index: number, aenderung: Partial<Pick<RunnerPrioritaet, 'verdraengbar' | 'min'>>): RunnerProfil {
  const liste = runnerPrioritaeten(profil)
  if (!liste[index]) return profil
  return runnerSetze(profil, ['prioritaeten'], liste.map((eintrag, i) => (i === index ? { ...eintrag, ...aenderung } : eintrag)))
}

/** Wer bei knapper Kapazität zuerst weicht: der verdrängbare Eintrag mit dem niedrigsten Rang (größte Zahl). */
export function runnerWeichtZuerst(liste: readonly RunnerPrioritaet[]): RunnerPrioritaet | null {
  return [...liste].reverse().find((eintrag) => eintrag.verdraengbar) ?? null
}

/** Klassenname wie im Backend (`auditcore_runner.profile.CLASS_NAME`). */
export const RUNNER_KLASSEN_NAME = /^[a-z0-9][a-z0-9-]{0,30}$/
export type RunnerKlassenArt = 'cpu' | 'gpu'

export function runnerKlassen(profil: RunnerProfil | null | undefined): string[] {
  const klassen = runnerWert(profil, ['klassen'])
  return isObject(klassen) ? Object.keys(klassen).sort() : []
}

export function runnerKlassenArt(profil: RunnerProfil | null | undefined, name: string): RunnerKlassenArt {
  return runnerWert(profil, ['klassen', name, 'art']) === 'gpu' ? 'gpu' : 'cpu'
}

/** Fehlerart eines Klassennamens; `null` = gültig. `alt` ist der bisherige Name beim Umbenennen. */
export function runnerKlassenNameFehler(profil: RunnerProfil | null | undefined, name: string, alt?: string): 'ungueltig' | 'vergeben' | null {
  if (!RUNNER_KLASSEN_NAME.test(name)) return 'ungueltig'
  if (name !== alt && runnerKlassen(profil).includes(name)) return 'vergeben'
  return null
}

/** Neue Klasse der Art `cpu` mit neutralen Werten (höchstens eine Instanz). */
export function runnerKlasseHinzu(profil: RunnerProfil, name: string): RunnerProfil {
  if (runnerKlassenNameFehler(profil, name)) return profil
  return runnerSetze(profil, ['klassen', name], {
    art: 'cpu', aktiv: true, cpus: 2, speicher_gb: 4, min_instanzen: 0, max_instanzen: 1, leise_max: -1, vram_mb: 0,
    labels: ['self-hosted', 'linux', 'x64', name],
  })
}

/** Klasse umbenennen; Verweise in Karten, Prioritäten und das gleichnamige Label ziehen mit. */
export function runnerKlasseUmbenennen(profil: RunnerProfil, alt: string, neu: string): RunnerProfil {
  const klassen = runnerWert(profil, ['klassen'])
  if (alt === neu || !isObject(klassen) || !(alt in klassen) || runnerKlassenNameFehler(profil, neu, alt)) return profil
  const eintrag = klassen[alt]
  const labels = runnerWert(eintrag as RunnerProfil, ['labels'])
  const umbenannt = isObject(eintrag) && Array.isArray(labels) ? { ...eintrag, labels: labels.map((l) => (l === alt ? neu : l)) } : eintrag
  const neueKlassen = Object.fromEntries(Object.entries(klassen).map(([k, v]) => (k === alt ? [neu, umbenannt] : [k, v])))
  let ergebnis = runnerSetze(profil, ['klassen'], neueKlassen)
  for (const liste of ['gpus', 'prioritaeten'] as const) {
    const eintraege = runnerWert(ergebnis, [liste])
    if (Array.isArray(eintraege)) {
      ergebnis = runnerSetze(ergebnis, [liste], eintraege.map((e) => (isObject(e) && e.klasse === alt ? { ...e, klasse: neu } : e)))
    }
  }
  return ergebnis
}
