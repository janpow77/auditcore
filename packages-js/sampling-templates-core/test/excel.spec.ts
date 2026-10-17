import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { FormulaError, count, divide, eq, ge, gt, guard, ifError, indexOf, le, lt, minus, ne, plus, sameNumber, isBlank, isNumber, left, matchExact, max, min, n, required, roundUp, sameText, search, squareRoot, sum, sumIf, toneOf } from '../src/excel/index'

describe('Excel-Semantik', () => {
  it('N() macht aus Leerwert und Text 0', () => {
    expect([n(null), n(''), n('Text'), n(undefined), n(4.5)]).toEqual([0, 0, 0, 0, 4.5])
  })

  it('ISTZAHL kennt nur endliche Zahlen', () => {
    expect([isNumber(0), isNumber(Number.NaN), isNumber(Infinity), isNumber('1'), isNumber(null)]).toEqual([true, false, false, false, false])
    expect([isBlank(null), isBlank(''), isBlank(0), isBlank(undefined)]).toEqual([true, true, false, true])
  })

  it('AUFRUNDEN rundet von null weg', () => {
    expect([roundUp(91.2), roundUp(92), roundUp(-1.2), roundUp(0)]).toEqual([92, 92, -2, 0])
    expect([roundUp(1.231, 2), roundUp(1.23, 2)]).toEqual([1.24, 1.23])
  })

  it('AUFRUNDEN kürzt wie die Tabellenkalkulation zuerst auf zwölf signifikante Stellen', () => {
    expect(Math.ceil((0.1 + 0.2) * 10)).toBe(4)
    expect(roundUp((0.1 + 0.2) * 10)).toBe(3)
    expect([roundUp(100.0000000009), roundUp(100.000000001), roundUp(100.00000005), roundUp(39.0000000039), roundUp(31.00000000062)]).toEqual([100, 101, 101, 40, 32])
    expect([roundUp(1000000.0005), roundUp(2000000000.5), roundUp(4850000000.3), roundUp(8693697600)]).toEqual([1000001, 2000000001, 4850000001, 8693697600])
    expect([roundUp(123456789012.25), roundUp(1e-9), roundUp(0.5)]).toEqual([123456789012, 1, 1])
    // Oberhalb von zwölf ganzzahligen Stellen kürzt die Tabellenkalkulation ebenfalls auf zwölf geltende Stellen (Abnahme, Blatt 03 C21).
    expect([roundUp(3697929000034.2), roundUp(3697929000080.7), roundUp(369792900021302.4)]).toEqual([3697929000030, 3697929000080, 369792900021000])
  })

  it('Vergleiche: gleich innerhalb von 2⁻⁴⁸ des Betrags', () => {
    const sum = (411130.9 + 1023471.01 + 353646.09) / 89412400
    expect(sum > 0.02).toBe(true)
    expect([gt(sum, 0.02), eq(sum, 0.02), le(sum, 0.02), ge(sum, 0.02), lt(sum, 0.02), ne(sum, 0.02)]).toEqual([false, true, true, true, false, false])
    expect([eq(0.7000000000000001, 0.7), eq(0.1 + 0.2, 0.3), eq(1, 1 + 1e-14), eq(0, 1e-300), eq(0, 0)]).toEqual([true, true, false, false, true])
    expect([gt(2, 1), lt(1, 2), ge(1, 2), le(2, 1)]).toEqual([true, true, false, false])
    expect([minus(0.3, 0.1 + 0.2), minus(5, 3), plus(0.1 + 0.2, -0.3), plus(2, 3)]).toEqual([0, 2, 0, 5])
    expect([sameNumber(0.1 + 0.2, 0.3), sameNumber('1', 1), sameNumber(null, 0)]).toEqual([true, false, false])
  })

  it('Vergleiche und Aufrunden stimmen mit der Messung an LibreOffice überein', () => {
    const measured = JSON.parse(readFileSync(new URL('./fixtures/libreoffice-semantik.json', import.meta.url), 'utf8')) as {
      vergleiche: { a: number; b: number; eq: number; lt: number; le: number; gt: number; ge: number; minus: number }[]
      aufrunden: { x: number; roundUp0: number; roundUp2: number }[]
    }
    expect(measured.vergleiche.length).toBeGreaterThan(400)
    const flag = (value: boolean): number => (value ? 1 : 0)
    for (const row of measured.vergleiche) {
      const actual = { eq: flag(eq(row.b, row.a)), lt: flag(lt(row.b, row.a)), le: flag(le(row.b, row.a)), gt: flag(gt(row.b, row.a)), ge: flag(ge(row.b, row.a)) }
      expect(actual, `${row.b} gegen ${row.a}`).toEqual({ eq: row.eq, lt: row.lt, le: row.le, gt: row.gt, ge: row.ge })
      expect(minus(row.b, row.a) === 0, `${row.b} − ${row.a}`).toBe(row.minus === 0)
    }
    for (const row of measured.aufrunden) {
      expect(roundUp(row.x), `ROUNDUP(${row.x};0)`).toBe(row.roundUp0)
      expect(roundUp(row.x, 2), `ROUNDUP(${row.x};2)`).toBeCloseTo(row.roundUp2, 9)
    }
  })

  it('IFERROR(…;"") ergibt null für Fehlerwerte und nicht endliche Zahlen', () => {
    expect(guard(() => divide(1, 0))).toBeNull()
    expect(guard(() => squareRoot(-1))).toBeNull()
    expect(guard(() => required(null) * 2)).toBeNull()
    expect(guard(() => 1 / 0)).toBeNull()
    expect(guard(() => required(3) * 2)).toBe(6)
    expect([ifError(() => divide(1, 0), 1), ifError(() => divide(6, 3), 1), ifError(() => required(null), 'x')]).toEqual([1, 2, 'x'])
    expect(() => guard(() => { throw new TypeError('Programmfehler') })).toThrow(TypeError)
  })

  it('Bereichsfunktionen übergehen Text und Leerwerte', () => {
    const range = [1, null, 'x', 4, '']
    expect([sum(range), count(range), max(range), min(range)]).toEqual([5, 2, 4, 1])
    expect([sum([]), max([]), min([null])]).toEqual([0, 0, 0])
    expect(sumIf(['a', 'b', 'A'], 'a', [1, 2, 4])).toBe(5)
    expect(sumIf([1, 2, 1], 1, [10, 20, 30])).toBe(40)
  })

  it('Textfunktionen', () => {
    expect([left('Ausschluss (Art. 3)', 10), left(null, 3), left(1234, 2)]).toEqual(['Ausschluss', '', '12'])
    expect(search('ART', 'nach Art. 5')).toBe(6)
    expect(() => search('x', 'abc')).toThrow(FormulaError)
    expect([sameText('Ja', 'ja'), sameText(null, ''), sameText(1, '1')]).toEqual([true, false, false])
  })

  it('VERGLEICH und INDEX', () => {
    expect(matchExact(0.7, [0.6, 0.7, 0.8])).toBe(2)
    expect(matchExact('MITTEL', ['hoch', 'mittel'])).toBe(2)
    expect(() => matchExact(0.75, [0.6, 0.7])).toThrow(FormulaError)
    expect(() => matchExact(null, [null])).toThrow(FormulaError)
    expect(indexOf([[1, 2], [3, 4]], 2, 1)).toBe(3)
    expect(() => indexOf([[1]], 2, 1)).toThrow(FormulaError)
  })

  it('Prüfhinweise werden nach dem führenden Zeichen eingestuft', () => {
    expect([toneOf('✔ ok'), toneOf('⚠ prüfen'), toneOf('✖ nein'), toneOf('Nicht angewandt'), toneOf(null)]).toEqual(['success', 'warning', 'danger', 'neutral', 'neutral'])
  })
})
