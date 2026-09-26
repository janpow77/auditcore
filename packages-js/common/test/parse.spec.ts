import { describe, expect, it } from 'vitest'
import { detectDecimal, parseDecimal, parseDecimalResult, parseDecimalString, parseNumber, parseTable } from '../src'

describe('parseDecimal', () => {
  it('liefert Zahl oder Dezimal-String', () => {
    expect(parseDecimal('1.234,56')).toBe(1234.56)
    expect(parseDecimalString('12.345.678,90')).toBe('12345678.90')
    expect(parseDecimalString('1.234,56', { mode: 'de' })).toBe('1234.56')
    expect(parseDecimalString('1,234.56', { mode: 'en' })).toBe('1234.56')
    expect(parseDecimal('abc')).toBeNull()
    expect(parseDecimal(null)).toBeNull()
  })

  it('nennt den Ablehnungsgrund', () => {
    expect(parseDecimalResult('1.5')).toEqual({ ok: false, reason: 'ambiguous' })
    expect(parseDecimalResult(' € ')).toEqual({ ok: false, reason: 'empty' })
    expect(parseDecimalResult('12a')).toEqual({ ok: false, reason: 'invalid' })
    expect(parseDecimalResult('-5', { allowNegative: false })).toEqual({ ok: false, reason: 'negative' })
    expect(parseDecimalResult(undefined)).toEqual({ ok: false, reason: 'empty' })
  })

  it('beachtet Optionen', () => {
    expect(parseDecimalString('1,2345', { maxFractionDigits: 4 })).toBe('1.2345')
    expect(parseDecimalString('0,5 %')).toBeNull()
    expect(parseDecimalString('5 €', { stripCurrency: false })).toBeNull()
    expect(parseDecimalString('1234.5678', { mode: 'auto' })).toBe('1234.5678')
    expect(parseDecimalString('1.234.567', { mode: 'auto' })).toBe('1234567')
    expect(parseDecimalString('1,234,567', { mode: 'auto' })).toBe('1234567')
    expect(parseDecimalString('12 345.5', { mode: 'en' })).toBe('12345.5')
  })
})

describe('Tabellen-Einlesen (aus @flowaudit/ui tabular, unverändert)', () => {
  it('liest Zellen mit ausdrücklichem Dezimaltrenner', () => {
    expect(parseNumber('1.234,56', ',')).toBe(1234.56)
    expect(parseNumber('(12,5)', ',')).toBe(-12.5)
    expect(parseNumber('', ',')).toBeNull()
    expect(parseNumber('abc', ',')).toBeUndefined()
    expect(detectDecimal(['1.234,5'], ';')).toBe(',')
    const table = parseTable('a;b\n1;2\n', true)
    expect(table.header).toEqual(['a', 'b'])
    expect(table.rows).toEqual([['1', '2']])
  })
})
