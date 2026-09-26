import { EMPTY_VALUE, localeTag, toFiniteNumber, type DisplayOptions } from './locale'

/** Einheiten zur Basis 1024 (Festlegung `filesize_units`). */
export const BYTE_UNITS = ['B', 'KB', 'MB', 'GB', 'TB'] as const

/** Optionen für `formatBytes`. */
export interface BytesFormatOptions extends DisplayOptions {
  /** Höchstens so viele Nachkommastellen (Standard 1; „,0“ entfällt). */
  digits?: number
}

/** Dateigröße zur Basis 1024: `512 B`, `1,5 KB`, `117,7 MB`; negativ/leer → `—`. */
export function formatBytes(bytes: number | string | null | undefined, options: BytesFormatOptions = {}): string {
  const value = toFiniteNumber(bytes)
  if (value === null || value < 0) return options.empty ?? EMPTY_VALUE
  const digits = options.digits ?? 1
  let unit = 0
  let scaled = value
  while (scaled >= 1024 && unit < BYTE_UNITS.length - 1) {
    scaled /= 1024
    unit += 1
  }
  const factor = 10 ** digits
  if (Math.round(scaled * factor) / factor >= 1024 && unit < BYTE_UNITS.length - 1) {
    scaled /= 1024
    unit += 1
  }
  const text = new Intl.NumberFormat(localeTag(options.locale ?? 'de'), {
    maximumFractionDigits: unit === 0 ? 0 : digits,
    useGrouping: false,
  }).format(scaled)
  return `${text} ${BYTE_UNITS[unit]}`
}
