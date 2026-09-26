import { parseDateInput, type DateInput } from './date'
import { EMPTY_VALUE, localeTag, toFiniteNumber, type DisplayOptions } from './locale'

const SECOND = 1000
const MINUTE = 60 * SECOND
const HOUR = 60 * MINUTE
const DAY = 24 * HOUR

function decimal(value: number, locale: string): string {
  return new Intl.NumberFormat(locale, { maximumFractionDigits: 1 }).format(value)
}

function pair(big: number, bigUnit: string, small: number, smallUnit: string): string {
  return small > 0 ? `${big} ${bigUnit} ${small} ${smallUnit}` : `${big} ${bigUnit}`
}

/**
 * Dauer in Millisekunden kompakt: `250 ms`, `3,2 s`, `4 min 5 s`,
 * `2 h 5 min`, `3 d 4 h`; negativ/leer → `—`.
 */
export function formatDuration(ms: number | string | null | undefined, options: DisplayOptions = {}): string {
  const value = toFiniteNumber(ms)
  if (value === null || value < 0) return options.empty ?? EMPTY_VALUE
  const locale = localeTag(options.locale ?? 'de')
  if (value < SECOND) return `${Math.round(value)} ms`
  if (value < MINUTE) return `${decimal(Math.floor(value / 100) / 10, locale)} s`
  if (value < HOUR) return pair(Math.floor(value / MINUTE), 'min', Math.floor((value % MINUTE) / SECOND), 's')
  if (value < DAY) return pair(Math.floor(value / HOUR), 'h', Math.floor((value % HOUR) / MINUTE), 'min')
  return pair(Math.floor(value / DAY), 'd', Math.floor((value % DAY) / HOUR), 'h')
}

/** Laufzeit in Sekunden (Dienste, eGPU): `45 s`, `12 min 3 s`, `5 d 2 h`. */
export function formatUptime(seconds: number | string | null | undefined, options: DisplayOptions = {}): string {
  const value = toFiniteNumber(seconds)
  if (value === null || value < 0) return options.empty ?? EMPTY_VALUE
  if (value < 60) return `${Math.floor(value)} s`
  return formatDuration(Math.floor(value) * SECOND, options)
}

/** Optionen für `formatRelativeTime`. */
export interface RelativeTimeOptions extends DisplayOptions {
  /** Bezugszeitpunkt (Standard: jetzt). */
  now?: DateInput
}

const RELATIVE_STEPS: readonly [Intl.RelativeTimeFormatUnit, number][] = [
  ['year', 365 * DAY],
  ['month', 30 * DAY],
  ['week', 7 * DAY],
  ['day', DAY],
  ['hour', HOUR],
  ['minute', MINUTE],
]

/** Relative Zeit mit `Intl.RelativeTimeFormat`: „vor 5 Minuten“, „gestern“, „in 2 Tagen“. */
export function formatRelativeTime(value: DateInput, options: RelativeTimeOptions = {}): string {
  const date = parseDateInput(value)
  const now = options.now === undefined ? new Date() : parseDateInput(options.now)
  if (!date || !now) return options.empty ?? EMPTY_VALUE
  const diff = date.getTime() - now.getTime()
  const format = new Intl.RelativeTimeFormat(localeTag(options.locale ?? 'de'), { numeric: 'auto' })
  const step = RELATIVE_STEPS.find(([, size]) => Math.abs(diff) >= size)
  if (!step) return format.format(Math.round(diff / SECOND), 'second')
  return format.format(Math.trunc(diff / step[1]), step[0])
}
