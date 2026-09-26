import { EMPTY_VALUE, localeTag, toFiniteNumber, type DisplayOptions } from './locale'

/** Eingaben der Zahlformatierer: Zahl oder Dezimal-String aus dem Backend. */
export type NumberInput = number | string | null | undefined

/** Optionen für `formatNumber`. */
export interface NumberFormatOptions extends DisplayOptions {
  /** Feste Nachkommastellen (setzt `minDigits` und `maxDigits`). */
  digits?: number
  /** Mindestens so viele Nachkommastellen (Standard 0). */
  minDigits?: number
  /** Höchstens so viele Nachkommastellen (Standard 2). */
  maxDigits?: number
  /** Tausendertrenner (Standard `true`). */
  grouping?: boolean
}

function fractionDigits(options: NumberFormatOptions): { min: number; max: number } {
  if (options.digits !== undefined) return { min: options.digits, max: options.digits }
  const min = options.minDigits ?? 0
  return { min, max: Math.max(min, options.maxDigits ?? 2) }
}

/** Zahl mit Tausenderpunkt und Dezimalkomma (`1.234,5`); leer/ungültig → `—`. */
export function formatNumber(value: NumberInput, options: NumberFormatOptions = {}): string {
  const number = toFiniteNumber(value)
  if (number === null) return options.empty ?? EMPTY_VALUE
  const { min, max } = fractionDigits(options)
  return new Intl.NumberFormat(localeTag(options.locale ?? 'de'), {
    minimumFractionDigits: min,
    maximumFractionDigits: max,
    useGrouping: options.grouping ?? true,
  }).format(number)
}

/** Ganze Zahl mit Tausenderpunkt (`12.345`). */
export function formatInt(value: NumberInput, options: DisplayOptions = {}): string {
  return formatNumber(value, { ...options, digits: 0 })
}

/** Optionen für `formatPercent`. */
export interface PercentFormatOptions extends DisplayOptions {
  /** `ratio`: 0,125 → 12,5 % (Standard); `percent`: 12,5 → 12,5 %. */
  scale?: 'ratio' | 'percent'
  /** Nachkommastellen (Standard 0 bis 1). */
  digits?: number
}

/** Prozentwert mit geschütztem Leerzeichen vor „%“ (`12,5 %`). */
export function formatPercent(value: NumberInput, options: PercentFormatOptions = {}): string {
  const number = toFiniteNumber(value)
  if (number === null) return options.empty ?? EMPTY_VALUE
  const ratio = options.scale === 'percent' ? number / 100 : number
  const digits = options.digits
  return new Intl.NumberFormat(localeTag(options.locale ?? 'de'), {
    style: 'percent',
    minimumFractionDigits: digits ?? 0,
    maximumFractionDigits: digits ?? 1,
  }).format(ratio)
}
