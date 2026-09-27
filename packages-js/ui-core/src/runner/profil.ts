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
