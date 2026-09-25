import type { Locale } from './i18n'

const TAGS: Readonly<Record<Locale, string>> = { de: 'de-DE', en: 'en-GB' }

export function localeTag(locale: Locale): string {
  return TAGS[locale]
}

/** Datum (ISO-Zeichenkette oder Date) kurz und sprachabhängig; ungültige Werte bleiben leer. */
export function formatDate(value: string | Date | null | undefined, locale: Locale, withTime = false): string {
  if (value === null || value === undefined || value === '') return ''
  const date = typeof value === 'string' ? new Date(value) : value
  if (Number.isNaN(date.getTime())) return ''
  const options: Intl.DateTimeFormatOptions = withTime
    ? { dateStyle: 'medium', timeStyle: 'short' }
    : { dateStyle: 'medium' }
  return new Intl.DateTimeFormat(localeTag(locale), options).format(date)
}

export function formatNumber(value: number, locale: Locale, options?: Intl.NumberFormatOptions): string {
  return new Intl.NumberFormat(localeTag(locale), options).format(value)
}

export function formatPercent(ratio: number, locale: Locale, fractionDigits = 0): string {
  return formatNumber(ratio, locale, {
    style: 'percent',
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  })
}
