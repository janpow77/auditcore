/**
 * Befristete Ausnahmen des UI-Paritäts-Gates (`quality/ui-parity-exceptions.json`).
 *
 * Regeln (Ratchet, nur Abbau):
 * - jede Ausnahme hat Kennung, Begründung (mindestens 20 Zeichen) und Ablaufdatum
 *   (höchstens 366 Tage in der Zukunft);
 * - abgelaufene Ausnahmen und Ausnahmen ohne passende Lücke schlagen fehl
 *   (geschlossene Lücken müssen aus der Datei entfernt werden);
 * - gegenüber dem Vergleichsstand (`--compare-ref`) dürfen weder neue Kennungen
 *   hinzukommen noch Ablaufdaten später werden.
 */
import { execFileSync } from 'node:child_process'
import { existsSync, readFileSync } from 'node:fs'

export const EXCEPTIONS_FILE = 'quality/ui-parity-exceptions.json'
const MAX_DAYS = 366
const DAY = 24 * 60 * 60 * 1000

function parseDate(text) {
  if (typeof text !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(text)) return null
  const date = new Date(`${text}T00:00:00Z`)
  return Number.isNaN(date.getTime()) ? null : date
}

/** @returns {{ id: string, reason: string, expires: string }[]} */
export function parseExceptions(text) {
  const data = JSON.parse(text)
  const list = Array.isArray(data?.exceptions) ? data.exceptions : null
  if (!list) throw new Error(`${EXCEPTIONS_FILE}: Feld "exceptions" (Liste) fehlt.`)
  return list
}

export function loadExceptions(path) {
  return existsSync(path) ? parseExceptions(readFileSync(path, 'utf8')) : []
}

function expiryProblem(id, text, today) {
  const expires = parseDate(text)
  if (!expires) return `${id}: Ablaufdatum "expires" (JJJJ-MM-TT) fehlt oder ist ungültig.`
  if (expires.getTime() < today.getTime()) return `${id}: Ausnahme ist am ${text} abgelaufen – Lücke schließen.`
  if (expires.getTime() - today.getTime() > MAX_DAYS * DAY) return `${id}: Ablaufdatum ${text} liegt mehr als ${MAX_DAYS} Tage in der Zukunft.`
  return null
}

/** Formfehler, Ablauf und Höchstdauer einer Ausnahme. */
function entryProblems(entry, today) {
  const valid = typeof entry?.id === 'string' && entry.id.split(':').length >= 3
  const id = typeof entry?.id === 'string' ? entry.id : '(ohne Kennung)'
  const reasonOk = typeof entry?.reason === 'string' && entry.reason.trim().length >= 20
  return [
    valid ? null : `${id}: Kennung muss <prüfung>:<familie>:<gegenstand> sein.`,
    reasonOk ? null : `${id}: Begründung fehlt oder ist kürzer als 20 Zeichen.`,
    expiryProblem(id, entry?.expires, today),
  ].filter((problem) => problem !== null)
}

/**
 * Verletzungen mit den Ausnahmen abgleichen.
 * @returns {{ open: object[], excepted: object[], problems: string[] }}
 */
export function applyExceptions(violations, exceptions, today) {
  const problems = []
  const seen = new Set()
  for (const entry of exceptions) {
    problems.push(...entryProblems(entry, today))
    if (seen.has(entry?.id)) problems.push(`${entry.id}: doppelte Ausnahme.`)
    seen.add(entry?.id)
  }
  const ids = new Set(violations.map((item) => item.id))
  for (const entry of exceptions) {
    if (typeof entry?.id === 'string' && !ids.has(entry.id)) problems.push(`${entry.id}: Lücke besteht nicht mehr – Ausnahme aus ${EXCEPTIONS_FILE} entfernen.`)
  }
  const valid = new Set(exceptions.filter((entry) => entryProblems(entry, today).length === 0).map((entry) => entry.id))
  return {
    open: violations.filter((item) => !valid.has(item.id)),
    excepted: violations.filter((item) => valid.has(item.id)),
    problems,
  }
}

const git = (root, args) => execFileSync('git', args, { cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] })

/**
 * Ausnahmedatei im Vergleichsstand oder `null`, wenn es sie dort noch nicht gab.
 * Ein unbekannter Vergleichsstand ist ein Fehler (fail closed).
 */
export function exceptionsAt(root, ref) {
  try {
    git(root, ['rev-parse', '--verify', '--quiet', `${ref}^{commit}`])
  } catch {
    throw new Error(`Vergleichsstand ${ref} ist unbekannt (fetch-depth?).`)
  }
  try {
    git(root, ['cat-file', '-e', `${ref}:${EXCEPTIONS_FILE}`])
  } catch {
    return null
  }
  return parseExceptions(git(root, ['show', `${ref}:${EXCEPTIONS_FILE}`]))
}

/** Ratchet gegenüber dem Vergleichsstand: keine neuen Ausnahmen, keine Verlängerung. */
export function ratchetProblems(current, base) {
  if (base === null) return []
  const before = new Map(base.map((entry) => [entry.id, entry]))
  const problems = []
  for (const entry of current) {
    const previous = before.get(entry.id)
    if (!previous) {
      problems.push(`${entry.id}: neue Ausnahme – ${EXCEPTIONS_FILE} darf nur schrumpfen; Lücke schließen (npm run ui:neu erzeugt das Gerüst).`)
    } else if (String(entry.expires) > String(previous.expires)) {
      problems.push(`${entry.id}: Ablaufdatum von ${previous.expires} auf ${entry.expires} verlängert – nicht zulässig.`)
    }
  }
  return problems
}
