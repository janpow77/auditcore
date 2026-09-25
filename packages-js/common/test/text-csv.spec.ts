import { describe, expect, it } from 'vitest'
import { CSV_BOM, csvBlob, escapeCsvCell, escapeHtml, initials, parseCsv, recordsToCsv, slugify, toCsv, truncate } from '../src'

describe('Text', () => {
  it('maskiert, kürzt und bildet Kennungen', () => {
    expect(escapeHtml(`<a href="x">'&'</a>`)).toBe('&lt;a href=&quot;x&quot;&gt;&#39;&amp;&#39;&lt;/a&gt;')
    expect(escapeHtml(null)).toBe('')
    expect(truncate('Verwaltungskontrolle', 10)).toBe('Verwaltun…')
    expect(truncate('kurz', 10)).toBe('kurz')
    expect(initials('Jan Riener')).toBe('JR')
    expect(initials('riener, jan')).toBe('RJ')
    expect(initials('')).toBe('')
    expect(slugify('Prüfbericht Größe 2026!')).toBe('pruefbericht-groesse-2026')
    expect(slugify('Café – Übersicht', 8)).toBe('cafe-ueb')
  })
})

describe('CSV', () => {
  it('schützt Formeln nur in Texten und respektiert Optionen', () => {
    expect(escapeCsvCell(-5)).toBe('-5')
    expect(escapeCsvCell('-5')).toBe("'-5")
    expect(escapeCsvCell('=1', { guardFormulas: false })).toBe('=1')
    expect(escapeCsvCell(1.5, { decimal: '.', delimiter: ',' })).toBe('1.5')
    expect(escapeCsvCell('a,b', { delimiter: ',' })).toBe('"a,b"')
    expect(escapeCsvCell(true)).toBe('true')
    expect(escapeCsvCell(Number.NaN)).toBe('')
    expect(escapeCsvCell(new Date('2026-01-31T00:00:00Z'))).toBe('2026-01-31T00:00:00.000Z')
    expect(escapeCsvCell(12n)).toBe('12')
  })

  it('schreibt Datensätze über deklarative Spalten', () => {
    const csv = recordsToCsv(
      [{ name: 'Müller', betrag: 1234.5 }],
      [{ label: 'Name', value: 'name' }, { label: 'Betrag', value: (row) => row.betrag * 2 }],
      { bom: false },
    )
    expect(csv).toBe('Name;Betrag\r\nMüller;2469\r\n')
    expect(toCsv([['a']], { lineEnding: '\n' })).toBe(`${CSV_BOM}a\n`)
  })

  it('liest CSV nach RFC 4180 zurück', () => {
    const written = toCsv([['Bemerkung', 'Wert'], ['a;b "c"\nd', 1.5], ['=1', null]])
    expect(parseCsv(written)).toEqual([['Bemerkung', 'Wert'], ['a;b "c"\nd', '1,5'], ["'=1", '']])
    expect(parseCsv('a,b\nc,d', { delimiter: ',' })).toEqual([['a', 'b'], ['c', 'd']])
    expect(parseCsv('a;b\rc;d')).toEqual([['a', 'b'], ['c', 'd']])
    expect(parseCsv('')).toEqual([])
  })

  it('erzeugt einen Blob', async () => {
    const blob = csvBlob('a;b')
    expect(blob.type).toBe('text/csv;charset=utf-8')
    expect(await blob.text()).toBe('a;b')
  })
})
