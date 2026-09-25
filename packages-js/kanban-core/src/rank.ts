/**
 * Rang-Schlüssel für die Reihenfolge in einer Spalte (fraktionale Indizes).
 * Zwischen zwei Karten entsteht immer ein neuer Schlüssel, ohne die übrigen
 * umzunummerieren. Identisch zu `auditcore_kanban.rank` (Paritätsfixtures).
 */
export const RANK_DIGITS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
const BASE = RANK_DIGITS.length
const MAX_SPREAD_LENGTH = 6

export class RankError extends Error {
  constructor(
    readonly code: 'INVALID_RANK' | 'INVALID_RANK_ORDER' | 'TOO_MANY_RANKS',
    message: string,
  ) {
    super(message)
    this.name = 'RankError'
  }
}

function digit(value: string): number {
  const index = RANK_DIGITS.indexOf(value)
  if (index < 0) throw new RankError('INVALID_RANK', `Ungültiges Rangzeichen: ${value}`)
  return index
}

function charAt(value: string, index: number): string {
  return value.charAt(index)
}

/** Gültig: nicht leer, nur Base-62-Zeichen, letzte Stelle nicht '0'. */
export function isValidRank(value: unknown): value is string {
  if (typeof value !== 'string' || value.length === 0 || value.endsWith('0')) return false
  for (const character of value) if (!RANK_DIGITS.includes(character)) return false
  return true
}

function commonPrefixLength(a: string, b: string): number {
  let length = 0
  while (length < b.length && (charAt(a, length) || '0') === charAt(b, length)) length += 1
  return length
}

/** Mittelpunkt zwischen a (leer = Anfang) und b (null = Ende); a < b vorausgesetzt. */
function midpoint(a: string, b: string | null): string {
  if (b !== null) {
    const prefix = commonPrefixLength(a, b)
    if (prefix > 0) return b.slice(0, prefix) + midpoint(a.slice(prefix), b.slice(prefix))
  }
  const low = a.length > 0 ? digit(charAt(a, 0)) : 0
  const high = b !== null ? digit(charAt(b, 0)) : BASE
  if (high - low > 1) return charAt(RANK_DIGITS, Math.floor((low + high) / 2))
  if (b !== null && b.length > 1) return b.slice(0, 1)
  return charAt(RANK_DIGITS, low) + midpoint(a.slice(1), null)
}

/** Neuer Schlüssel echt zwischen `before` und `after` (null = offenes Ende). */
export function rankBetween(before: string | null, after: string | null): string {
  for (const value of [before, after]) {
    if (value !== null && !isValidRank(value)) throw new RankError('INVALID_RANK', `Ungültiger Rang: ${value}`)
  }
  if (before !== null && after !== null && before >= after) {
    throw new RankError('INVALID_RANK_ORDER', `Rang ${before} liegt nicht vor ${after}`)
  }
  return midpoint(before ?? '', after)
}

function toBase62(value: bigint, length: number): string {
  const base = BigInt(BASE)
  let text = ''
  let rest = value
  for (let position = 0; position < length; position += 1) {
    text = charAt(RANK_DIGITS, Number(rest % base)) + text
    rest /= base
  }
  return text
}

/** `count` gleichmäßig verteilte, aufsteigende Schlüssel (Neuaufbau einer Spalte). */
export function spreadRanks(count: number): string[] {
  if (!Number.isInteger(count) || count < 0) throw new RankError('TOO_MANY_RANKS', 'Anzahl muss eine natürliche Zahl sein')
  if (count === 0) return []
  let length = 1
  while (BASE ** length <= count) length += 1
  if (length > MAX_SPREAD_LENGTH) throw new RankError('TOO_MANY_RANKS', `Zu viele Karten für eine Spalte: ${count}`)
  // BigInt: exakt wie Pythons Ganzzahlen, auch bei sechsstelligen Schlüsseln.
  const space = BigInt(BASE) ** BigInt(length)
  const ranks: string[] = []
  for (let index = 0; index < count; index += 1) {
    const value = (BigInt(index + 1) * space) / BigInt(count + 1)
    ranks.push(toBase62(value, length).replace(/0+$/, ''))
  }
  return ranks
}

/** Sortiervergleich nach Rang (Code-Einheiten-Reihenfolge wie Python-str). */
export function compareRanks(a: string, b: string): number {
  if (a === b) return 0
  return a < b ? -1 : 1
}
