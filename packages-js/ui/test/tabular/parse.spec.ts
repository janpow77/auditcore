import { describe, expect, it } from 'vitest'
import {
  detectDecimal,
  detectDelimiter,
  guessNumberColumn,
  numberColumn,
  parseNumber,
  parseTable,
  splitLine,
} from '../../src/tabular/parse'

describe('Tabellen einlesen', () => {
  it('erkennt Trennzeichen und Anführungszeichen', () => {
    expect(detectDelimiter('a;b;c')).toBe(';')
    expect(detectDelimiter('a\tb')).toBe('\t')
    expect(detectDelimiter('a,b,c')).toBe(',')
    expect(detectDelimiter('nur')).toBe(';')
    expect(splitLine('"Müller; GmbH";"1.234,56";"sagt ""ja"""', ';')).toEqual(['Müller; GmbH', '1.234,56', 'sagt "ja"'])
  })

  it('liest Kopfzeile, BOM und leere Zeilen', () => {
    const table = parseTable('﻿Beleg;Betrag\r\nB-1;10,5\r\n\r\nB-2;7', true)
    expect(table.header).toEqual(['Beleg', 'Betrag'])
    expect(table.rows).toEqual([['B-1', '10,5'], ['B-2', '7']])
    expect(parseTable('1;2\n3;4', false).header).toEqual(['Spalte 1', 'Spalte 2'])
  })

  it('liest Zahlen mit ausdrücklichem Dezimaltrenner', () => {
    expect(parseNumber('1.234,56', ',')).toBe(1234.56)
    expect(parseNumber('1,234.56', '.')).toBe(1234.56)
    expect(parseNumber('50.000', ',')).toBe(50000)
    expect(parseNumber('-12,5 €', ',')).toBe(-12.5)
    expect(parseNumber('(300)', ',')).toBe(-300)
    expect(parseNumber('1e3', '.')).toBe(1000)
    expect(parseNumber('', ',')).toBeNull()
    expect(parseNumber('abc', ',')).toBeUndefined()
    expect(parseNumber('1,2,3', ',')).toBeUndefined()
  })

  it('erkennt den Dezimaltrenner einer Spalte', () => {
    expect(detectDecimal(['1.234,56'], ',')).toBe(',')
    expect(detectDecimal(['1,234.56'], ';')).toBe('.')
    expect(detectDecimal(['12,5'], ',')).toBe(',')
    expect(detectDecimal(['0.25'], ';')).toBe('.')
    expect(detectDecimal(['1.000'], ';')).toBe(',')
    expect(detectDecimal(['1.000'], ',')).toBe('.')
  })

  it('meldet unlesbare Zeilen, statt sie zu 0 zu machen', () => {
    const table = parseTable('Name;Betrag\nA;12,5\nB;k. A.\nC;\nD;7', true)
    expect(guessNumberColumn(table)).toBe(1)
    expect(numberColumn(table, 1, ',')).toEqual({ values: [12.5, null, 7], rejected: [2] })
  })
})
