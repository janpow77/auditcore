// Zahleneingaben strikt lesen (Beträge, Mengen, Importwerte). Ergebnis ist
// ein Dezimal-String ohne Rundung (`parseDecimalString`) oder eine Zahl
// (`parseDecimal`); ungültige, leere und mehrdeutige Eingaben ergeben `null`
// – nie 0 und nie ein geratener Wert. `parseDecimalResult` nennt den Grund.
//
// - `strict-de` (Betragsfelder): Komma dezimal, Punkt/Leerzeichen nur als
//   Tausendertrenner in Dreiergruppen, höchstens zwei Nachkommastellen.
//   „1.5“ und „1.234“ sind mehrdeutig, „1,234“ ebenso.
// - `strict-en`: Punkt dezimal, Komma/Leerzeichen als Tausendertrenner.
// - `auto` (Fremddateien): der letzte Trenner entscheidet; ein einzelner
//   Trenner vor genau drei Ziffern ist mehrdeutig.
//
// Währungszeichen (€, EUR), Leerraum (auch U+00A0, U+202F) und das
// typografische Minus (U+2212) werden verarbeitet.

/** `strict-de` (Betragsfelder), `strict-en` oder `auto` (Fremddateien). */
export type ParseMode = 'strict-de' | 'strict-en' | 'auto'

/** Optionen der Zahleneingabe. */
export interface ParseDecimalOptions {
  /** Standard `strict-de`; `de`/`en` sind Kurzformen. */
  mode?: ParseMode | 'de' | 'en'
  /** Negative Werte zulassen (Standard `true`). */
  allowNegative?: boolean
  /** €/EUR entfernen (Standard `true`). */
  stripCurrency?: boolean
  /** Höchstzahl der Nachkommastellen (Standard: 2 bei `strict-de`, sonst unbegrenzt). */
  maxFractionDigits?: number
}

/** Grund einer Ablehnung: leer (nur Leerraum/Trenner/Währung), mehrdeutig oder ungültig. */
export type ParseFailure = 'empty' | 'ambiguous' | 'invalid' | 'negative'

/** Ergebnis mit Dezimal-String oder Ablehnungsgrund. */
export type ParseDecimalResult = { ok: true; value: string } | { ok: false; reason: ParseFailure }

interface Separators {
  group: '.' | ','
  decimal: ',' | '.'
}

const DE: Separators = { group: '.', decimal: ',' }
const EN: Separators = { group: ',', decimal: '.' }

function fail(reason: ParseFailure): ParseDecimalResult {
  return { ok: false, reason }
}

function normalizeMode(mode: ParseDecimalOptions['mode']): ParseMode {
  if (mode === 'de' || mode === undefined) return 'strict-de'
  return mode === 'en' ? 'strict-en' : mode
}

interface Signed {
  negative: boolean
  body: string
}

function splitSign(text: string, stripCurrency: boolean): Signed | null {
  let rest = text.replace(/−/g, '-')
  if (stripCurrency) rest = rest.replace(/€|EUR/gi, ' ')
  rest = rest.trim()
  const negative = rest.startsWith('-')
  if (negative) rest = rest.slice(1).trim()
  if (rest.includes('-')) return null
  return { negative, body: rest.replace(/\s+/g, ' ') }
}

function groupedInteger(integer: string, group: string): boolean {
  if (/^\d+$/.test(integer)) return true
  for (const separator of [group, ' ']) {
    const pieces = integer.split(separator)
    const [head = '', ...tail] = pieces
    if (tail.length > 0 && /^\d{1,3}$/.test(head) && tail.every((piece) => /^\d{3}$/.test(piece))) return true
  }
  return false
}

function canonical(negative: boolean, integer: string, fraction: string | undefined): string {
  const digits = integer.replace(/\D/g, '').replace(/^0+(?=\d)/, '')
  const text = fraction === undefined ? digits : `${digits}.${fraction}`
  return negative && /[1-9]/.test(text) ? `-${text}` : text
}

function withSeparators(body: string, negative: boolean, separators: Separators, maxFraction: number): ParseDecimalResult {
  const parts = body.split(separators.decimal)
  if (parts.length > 2) return fail('invalid')
  const [integer = '', fraction] = parts
  if (!groupedInteger(integer, separators.group)) return fail('invalid')
  if (fraction !== undefined && !/^\d+$/.test(fraction)) return fail('invalid')
  if (fraction !== undefined && fraction.length > maxFraction) return fail('invalid')
  return { ok: true, value: canonical(negative, integer, fraction) }
}

/** strict-de: eine einzelne Dreiergruppe hinter Punkt oder Komma ist mehrdeutig, ein einzelner Punkt ohne Komma ebenso. */
function ambiguousDe(body: string): boolean {
  if (/^\d{1,3},\d{3}$/.test(body) || /^\d+,\d{3}$/.test(body)) return true
  return /^\d+\.\d+$/.test(body)
}

/** auto: Dezimaltrenner aus dem letzten Trenner; `null` = mehrdeutig. */
function detectSeparators(body: string): Separators | null {
  const comma = body.lastIndexOf(',')
  const dot = body.lastIndexOf('.')
  if (comma >= 0 && dot >= 0) return comma > dot ? DE : EN
  const mark = comma >= 0 ? ',' : '.'
  const count = body.split(mark).length - 1
  if (count === 0) return DE
  if (count > 1) return mark === '.' ? DE : EN
  return /^\d{1,3}[.,]\d{3}$/.test(body) ? null : mark === ',' ? DE : EN
}

function parseBody(signed: Signed, mode: ParseMode, options: ParseDecimalOptions): ParseDecimalResult {
  const { body, negative } = signed
  if (!/[0-9]/.test(body)) return fail(/^[\s.,]*$/.test(body) ? 'empty' : 'invalid')
  if (!/^[\d.,\s]+$/.test(body)) return fail('invalid')
  if (mode === 'strict-de' && ambiguousDe(body)) return fail('ambiguous')
  const separators = mode === 'strict-de' ? DE : mode === 'strict-en' ? EN : detectSeparators(body)
  if (!separators) return fail('ambiguous')
  const maxFraction = options.maxFractionDigits ?? (mode === 'strict-de' ? 2 : Number.POSITIVE_INFINITY)
  return withSeparators(body, negative, separators, maxFraction)
}

/** Liest eine Zahleneingabe und nennt bei Ablehnung den Grund (`empty`, `ambiguous`, `invalid`, `negative`). */
export function parseDecimalResult(text: string | null | undefined, options: ParseDecimalOptions = {}): ParseDecimalResult {
  if (typeof text !== 'string') return fail('empty')
  const signed = splitSign(text, options.stripCurrency ?? true)
  if (!signed) return fail('invalid')
  const result = parseBody(signed, normalizeMode(options.mode), options)
  if (result.ok && options.allowNegative === false && result.value.startsWith('-')) return fail('negative')
  return result
}

/** Zahleneingabe → Dezimal-String (`"1234.56"`) ohne Rundungsverlust; sonst `null`. */
export function parseDecimalString(text: string | null | undefined, options: ParseDecimalOptions = {}): string | null {
  const result = parseDecimalResult(text, options)
  return result.ok ? result.value : null
}

/** Zahleneingabe → `number`; sonst `null`. Für Beträge mit Rechenbedarf `parseDecimalString` bevorzugen. */
export function parseDecimal(text: string | null | undefined, options: ParseDecimalOptions = {}): number | null {
  const value = parseDecimalString(text, options)
  return value === null ? null : Number(value)
}

/** Deutsche Hinweistexte zu den Ablehnungsgründen (für Formularfelder). */
export const PARSE_FAILURE_HINTS: Readonly<Record<ParseFailure, string>> = {
  empty: 'leer',
  ambiguous: 'mehrdeutig – bitte mit Komma als Dezimaltrenner eingeben (z. B. 1.234,56)',
  invalid: 'keine gültige Zahl',
  negative: 'negative Werte sind nicht zulässig',
}
