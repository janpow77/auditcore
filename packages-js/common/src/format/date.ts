import { DISPLAY_TIME_ZONE, EMPTY_VALUE, localeTag, type AppLocale, type DisplayOptions } from './locale'

/** Eingaben der Datumsformatierer: ISO-Zeichenkette, `Date` oder Epoch-Millisekunden. */
export type DateInput = string | number | Date | null | undefined

/** Optionen der Datumsformatierer. */
export interface DateFormatOptions extends DisplayOptions {
  /** Anzeigezeitzone (Standard `Europe/Berlin`). */
  timeZone?: string
}

/** Optionen der Uhrzeitformatierer. */
export interface TimeFormatOptions extends DateFormatOptions {
  /** Sekunden anzeigen (Standard `false`). */
  seconds?: boolean
}

const DATE_ONLY = /^(\d{4})-(\d{2})-(\d{2})$/

interface CalendarDay {
  year: number
  month: number
  day: number
}

/** Reines Datum `JJJJ-MM-TT` als Kalendertag (ohne Zeitzone); `null` bei anderem Format oder ungültigem Tag. */
export function parseCalendarDay(value: string): CalendarDay | null {
  const match = DATE_ONLY.exec(value.trim())
  if (!match) return null
  const [year, month, day] = [Number(match[1]), Number(match[2]), Number(match[3])]
  const probe = new Date(Date.UTC(year, month - 1, day))
  const valid = probe.getUTCFullYear() === year && probe.getUTCMonth() === month - 1 && probe.getUTCDate() === day
  return valid ? { year, month, day } : null
}

/**
 * Eingabe → `Date` oder `null`. Reine Datumswerte `JJJJ-MM-TT` werden als
 * lokale Mitternacht gelesen (nicht wie `new Date('JJJJ-MM-TT')` als UTC),
 * damit sie in keiner Zeitzone auf den Vortag rutschen.
 */
export function parseDateInput(value: DateInput): Date | null {
  if (value === null || value === undefined || value === '') return null
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value
  if (typeof value === 'number') return Number.isFinite(value) ? new Date(value) : null
  const day = parseCalendarDay(value)
  if (day) return new Date(day.year, day.month - 1, day.day)
  if (DATE_ONLY.test(value.trim())) return null
  const date = new Date(value.trim())
  return Number.isNaN(date.getTime()) ? null : date
}

const DATE_PARTS: Intl.DateTimeFormatOptions = { day: '2-digit', month: '2-digit', year: 'numeric' }

function calendarDay(value: DateInput): CalendarDay | null {
  return typeof value === 'string' ? parseCalendarDay(value) : null
}

function formatCalendarDay(day: CalendarDay, locale: AppLocale): string {
  const noon = new Date(Date.UTC(day.year, day.month - 1, day.day, 12))
  return new Intl.DateTimeFormat(localeTag(locale), { ...DATE_PARTS, timeZone: 'UTC' }).format(noon)
}

function format(value: DateInput, options: DateFormatOptions, parts: Intl.DateTimeFormatOptions): string {
  const date = parseDateInput(value)
  if (!date) return options.empty ?? EMPTY_VALUE
  const timeZone = options.timeZone ?? DISPLAY_TIME_ZONE
  return new Intl.DateTimeFormat(localeTag(options.locale ?? 'de'), { ...parts, timeZone }).format(date)
}

/** Datum `TT.MM.JJJJ` in Berliner Zeit; reine Datumswerte ohne Umrechnung; leer/ungültig → `—`. */
export function formatDate(value: DateInput, options: DateFormatOptions = {}): string {
  const day = calendarDay(value)
  if (day) return formatCalendarDay(day, options.locale ?? 'de')
  return format(value, options, DATE_PARTS)
}

function timeParts(seconds: boolean | undefined): Intl.DateTimeFormatOptions {
  return seconds ? { hour: '2-digit', minute: '2-digit', second: '2-digit' } : { hour: '2-digit', minute: '2-digit' }
}

/**
 * Datum mit Uhrzeit `TT.MM.JJJJ, HH:MM` in Berliner Zeit. Ein reines Datum
 * hat keine Uhrzeit und erscheint wie bei `formatDate`.
 */
export function formatDateTime(value: DateInput, options: TimeFormatOptions = {}): string {
  const day = calendarDay(value)
  if (day) return formatCalendarDay(day, options.locale ?? 'de')
  return format(value, options, { ...DATE_PARTS, ...timeParts(options.seconds) })
}

/** Uhrzeit `HH:MM` (optional mit Sekunden) in Berliner Zeit. */
export function formatTime(value: DateInput, options: TimeFormatOptions = {}): string {
  if (calendarDay(value)) return options.empty ?? EMPTY_VALUE
  return format(value, options, timeParts(options.seconds))
}

/** Kalendertag `JJJJ-MM-TT` eines Zeitpunkts in der Anzeigezeitzone (Standard Berlin); `null` bei ungültig. */
export function toIsoDate(value: DateInput, timeZone: string = DISPLAY_TIME_ZONE): string | null {
  const day = calendarDay(value)
  if (day) return `${day.year}-${String(day.month).padStart(2, '0')}-${String(day.day).padStart(2, '0')}`
  const date = parseDateInput(value)
  if (!date) return null
  const parts = new Intl.DateTimeFormat('en-CA', { year: 'numeric', month: '2-digit', day: '2-digit', timeZone }).formatToParts(date)
  const part = (type: Intl.DateTimeFormatPartTypes): string => parts.find((entry) => entry.type === type)?.value ?? ''
  return `${part('year')}-${part('month')}-${part('day')}`
}
