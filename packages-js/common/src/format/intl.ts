/**
 * Kurzformatierer mit `Intl` in der Zeitzone des Rechners und leerem
 * Ersatzwert – unverändert aus `@flowaudit/ui` (i18n/format.ts) übernommen.
 * `@flowaudit/ui` exportiert sie weiter als `formatDate`, `formatNumber`
 * und `formatPercent`. Neue Anwendungen nutzen `formatDate`/`formatNumber`/
 * `formatPercent` dieses Pakets (Berliner Zeit, Ersatzwert „—“).
 */
import { localeTag, type AppLocale } from './locale'

/** Datum (ISO-Zeichenkette oder Date) kurz und sprachabhängig; ungültige Werte bleiben leer. */
export function intlFormatDate(value: string | Date | null | undefined, locale: AppLocale, withTime = false): string {
  if (value === null || value === undefined || value === '') return ''
  const date = typeof value === 'string' ? new Date(value) : value
  if (Number.isNaN(date.getTime())) return ''
  const options: Intl.DateTimeFormatOptions = withTime
    ? { dateStyle: 'medium', timeStyle: 'short' }
    : { dateStyle: 'medium' }
  return new Intl.DateTimeFormat(localeTag(locale), options).format(date)
}

/** Zahl mit `Intl.NumberFormat` und frei wählbaren Optionen. */
export function intlFormatNumber(value: number, locale: AppLocale, options?: Intl.NumberFormatOptions): string {
  return new Intl.NumberFormat(localeTag(locale), options).format(value)
}

/** Anteil (0–1) als Prozent mit fester Nachkommazahl. */
export function intlFormatPercent(ratio: number, locale: AppLocale, fractionDigits = 0): string {
  return intlFormatNumber(ratio, locale, {
    style: 'percent',
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  })
}
