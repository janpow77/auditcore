import { describe, expect, it } from 'vitest'
import {
  EMPTY_VALUE,
  formatBytes,
  formatDate,
  formatDateTime,
  formatDuration,
  formatEur,
  formatEurCompact,
  formatInt,
  formatNumber,
  formatPercent,
  formatRelativeTime,
  formatTime,
  formatUptime,
  intlFormatDate,
  intlFormatNumber,
  intlFormatPercent,
  isEmptyValue,
  localeTag,
  parseCalendarDay,
  parseDateInput,
  roundHalfUp,
  toFiniteNumber,
  toIsoDate,
  toPlainDecimal,
} from '../src'

describe('Datum', () => {
  it('zeigt reine Datumswerte ohne Umrechnung und Zeitstempel in Berliner Zeit', () => {
    expect(formatDate('2026-01-31')).toBe('31.01.2026')
    expect(formatDate('2026-01-31', { locale: 'en' })).toBe('31/01/2026')
    expect(formatDate('2026-01-31T23:30:00Z')).toBe('01.02.2026')
    expect(formatDate(Date.UTC(2026, 0, 31, 12))).toBe('31.01.2026')
    expect(formatDate('2026-02-30')).toBe(EMPTY_VALUE)
    expect(formatDate(null, { empty: '' })).toBe('')
  })

  it('formatiert Uhrzeiten mit und ohne Sekunden', () => {
    expect(formatDateTime('2026-07-15T10:05:09Z', { seconds: true })).toBe('15.07.2026, 12:05:09')
    expect(formatDateTime('2026-07-15')).toBe('15.07.2026')
    expect(formatTime('2026-07-15T10:05:00Z')).toBe('12:05')
    expect(formatTime('2026-07-15')).toBe(EMPTY_VALUE)
    expect(formatDateTime('2026-07-15T10:05:00Z', { timeZone: 'UTC' })).toBe('15.07.2026, 10:05')
  })

  it('liest Eingaben ohne Vortagsfehler', () => {
    const day = parseDateInput('2026-01-31')
    expect(day?.getDate()).toBe(31)
    expect(parseDateInput('kein Datum')).toBeNull()
    expect(parseDateInput(new Date(Number.NaN))).toBeNull()
    expect(parseDateInput(Number.POSITIVE_INFINITY)).toBeNull()
    expect(parseCalendarDay('2026-13-01')).toBeNull()
    expect(toIsoDate('2026-01-31T23:30:00Z')).toBe('2026-02-01')
    expect(toIsoDate('2026-03-05')).toBe('2026-03-05')
    expect(toIsoDate('x')).toBeNull()
  })
})

describe('Zahlen und Beträge', () => {
  it('formatiert Zahlen, ganze Zahlen und Prozente', () => {
    expect(formatNumber(1234.567)).toBe('1.234,57')
    expect(formatNumber('1234.5', { digits: 2 })).toBe('1.234,50')
    expect(formatNumber(1234.5, { locale: 'en', grouping: false })).toBe('1234.5')
    expect(formatNumber('abc')).toBe(EMPTY_VALUE)
    expect(formatInt(12345.6)).toBe('12.346')
    expect(formatPercent(0.125)).toBe('12,5 %')
    expect(formatPercent(12.5, { scale: 'percent', digits: 2 })).toBe('12,50 %')
    expect(formatPercent(null)).toBe(EMPTY_VALUE)
  })

  it('rundet Beträge kaufmännisch', () => {
    expect(formatEur(1.005)).toBe('1,01 €')
    expect(formatEur(-0.004)).toBe('0,00 €')
    expect(formatEur(123, { cents: true })).toBe('1,23 €')
    expect(formatEur(5, { cents: true })).toBe('0,05 €')
    expect(formatEur('12.345', { digits: 0 })).toBe('12 €')
    expect(formatEur('1,5')).toBe(EMPTY_VALUE)
    expect(roundHalfUp('9.995', 2)).toBe('10.00')
    expect(roundHalfUp('-2.5', 0)).toBe('-3')
    expect(() => roundHalfUp('x', 2)).toThrow(RangeError)
    expect(toPlainDecimal(1e-7)).toBe('0.0000001')
    expect(toPlainDecimal(1e21)).toBe('1000000000000000000000')
    expect(toPlainDecimal(Number.NaN)).toBeNull()
  })

  it('kürzt Kennzahlen', () => {
    expect(formatEurCompact(1234567)).toBe('1,2 Mio. €')
    expect(formatEurCompact(850000)).toBe('850 T€')
    expect(formatEurCompact(3.4e9)).toBe('3,4 Mrd. €')
    expect(formatEurCompact(999)).toBe('999,00 €')
    expect(formatEurCompact(undefined)).toBe(EMPTY_VALUE)
  })

  it('erkennt leere Werte und Zahlen', () => {
    expect([null, undefined, '', Number.NaN].every(isEmptyValue)).toBe(true)
    expect(isEmptyValue(0)).toBe(false)
    expect(toFiniteNumber(' 12.5 ')).toBe(12.5)
    expect(toFiniteNumber('1e3')).toBe(1000)
    expect(toFiniteNumber('1,5')).toBeNull()
    expect(toFiniteNumber(10n)).toBe(10)
  })
})

describe('Dateigröße und Dauer', () => {
  it('springt bei Rundung auf die nächste Einheit', () => {
    expect(formatBytes(1048575)).toBe('1 MB')
    expect(formatBytes(1536, { locale: 'en' })).toBe('1.5 KB')
    expect(formatBytes(2 ** 50)).toBe('1024 TB')
    expect(formatBytes('x')).toBe(EMPTY_VALUE)
  })

  it('formatiert Dauer, Laufzeit und relative Zeit', () => {
    expect(formatDuration(250)).toBe('250 ms')
    expect(formatDuration(3200)).toBe('3,2 s')
    expect(formatDuration(245000)).toBe('4 min 5 s')
    expect(formatDuration(120000)).toBe('2 min')
    expect(formatDuration(7500000)).toBe('2 h 5 min')
    expect(formatDuration(3 * 86400000 + 4 * 3600000)).toBe('3 d 4 h')
    expect(formatDuration(-1)).toBe(EMPTY_VALUE)
    expect(formatUptime(45)).toBe('45 s')
    expect(formatUptime(723)).toBe('12 min 3 s')
    expect(formatUptime(null)).toBe(EMPTY_VALUE)
    const now = '2026-09-25T12:00:00Z'
    expect(formatRelativeTime('2026-09-25T11:55:00Z', { now })).toBe('vor 5 Minuten')
    expect(formatRelativeTime('2026-09-24T12:00:00Z', { now })).toBe('gestern')
    expect(formatRelativeTime('2026-09-25T12:00:20Z', { now })).toBe('in 20 Sekunden')
    expect(formatRelativeTime('2026-09-27T12:00:00Z', { now, locale: 'en' })).toBe('in 2 days')
    expect(formatRelativeTime('x', { now })).toBe(EMPTY_VALUE)
  })
})

describe('Intl-Kurzformen aus @auditcore/ui (unverändert)', () => {
  it('verhalten sich wie bisher', () => {
    expect(localeTag('de')).toBe('de-DE')
    expect(localeTag('en')).toBe('en-GB')
    expect(intlFormatDate('2026-09-25T10:00:00', 'de')).toBe('25.09.2026')
    expect(intlFormatDate('kaputt', 'de')).toBe('')
    expect(intlFormatDate(null, 'de')).toBe('')
    expect(intlFormatDate(new Date(2026, 8, 25, 10, 5), 'en', true)).toMatch(/^25 Sept? 2026, 10:05$/)
    expect(intlFormatNumber(1234.5, 'de')).toBe('1.234,5')
    expect(intlFormatPercent(0.125, 'de', 1)).toBe('12,5 %')
  })
})
