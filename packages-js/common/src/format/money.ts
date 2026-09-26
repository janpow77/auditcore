import { toPlainDecimal, roundHalfUp } from './decimal'
import { EMPTY_VALUE, localeTag, type DisplayOptions } from './locale'
import type { NumberInput } from './number'

/** Optionen für `formatEur`. */
export interface MoneyFormatOptions extends DisplayOptions {
  /** Nachkommastellen (Standard 2, kaufmännisch gerundet). */
  digits?: number
  /** Eingabe in Cent (Standard `false`). */
  cents?: boolean
  /** Währung nach ISO 4217 (Standard `EUR`). */
  currency?: string
}

function decimalOf(value: NumberInput, cents: boolean): string | null {
  if (value === null || value === undefined || value === '') return null
  const plain = toPlainDecimal(value)
  if (plain === null) return null
  return cents ? shiftTwo(plain) : plain
}

function shiftTwo(plain: string): string {
  const negative = plain.startsWith('-')
  const [integer = '0', fraction = ''] = plain.replace('-', '').split('.')
  const digits = integer.padStart(3, '0')
  const shifted = `${digits.slice(0, -2)}.${digits.slice(-2)}${fraction}`
  return negative ? `-${shifted}` : shifted
}

/**
 * Betrag wie `Intl.NumberFormat('de-DE', {style: 'currency'})`: `1.234,50 €`
 * mit geschütztem Leerzeichen, kaufmännisch gerundet; Zahl oder Decimal-String;
 * leer/ungültig → `—`.
 */
export function formatEur(value: NumberInput, options: MoneyFormatOptions = {}): string {
  const decimal = decimalOf(value, options.cents ?? false)
  if (decimal === null) return options.empty ?? EMPTY_VALUE
  const digits = options.digits ?? 2
  const rounded = Number(roundHalfUp(decimal, digits))
  return new Intl.NumberFormat(localeTag(options.locale ?? 'de'), {
    style: 'currency',
    currency: options.currency ?? 'EUR',
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(rounded)
}

const COMPACT_STEPS: readonly { limit: number; suffix: string; digits: number }[] = [
  { limit: 1e9, suffix: ' Mrd. €', digits: 1 },
  { limit: 1e6, suffix: ' Mio. €', digits: 1 },
  { limit: 1e3, suffix: ' T€', digits: 0 },
]

/** Kurzform für Kennzahlen: `1,2 Mio. €`, `850 T€`, `3,4 Mrd. €`; unter 1.000 wie `formatEur`. */
export function formatEurCompact(value: NumberInput, options: DisplayOptions = {}): string {
  const decimal = decimalOf(value, false)
  if (decimal === null) return options.empty ?? EMPTY_VALUE
  const amount = Number(decimal)
  const step = COMPACT_STEPS.find((entry) => Math.abs(amount) >= entry.limit)
  if (!step) return formatEur(amount, options)
  const scaled = Number(roundHalfUp(toPlainDecimal(amount / step.limit) ?? '0', step.digits))
  const number = new Intl.NumberFormat(localeTag(options.locale ?? 'de'), { maximumFractionDigits: step.digits }).format(scaled)
  return `${number}${step.suffix}`
}
