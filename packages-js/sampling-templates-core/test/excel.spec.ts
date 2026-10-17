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

  it('AUFRUNDEN rundet wie Excel zuerst auf 15 geltende Stellen', () => {
    expect(Math.ceil((0.1 + 0.2) * 10)).toBe(4)
    expect(roundUp((0.1 + 0.2) * 10)).toBe(3)
    // Abnahme Blatt 03, Fall „R-off 100 · (1 + 1e-14)“: Excel 101 (LibreOffice kürzte auf zwölf Stellen und zeigte 100).
    expect([roundUp(100 * (1 + 1e-14)), roundUp(100 * (1 + 16 * 2 ** -52)), roundUp(99.00000000000009), roundUp(1.000000000005)]).toEqual([101, 100, 100, 2])
    expect([roundUp(123456789012.25), roundUp(1e-9), roundUp(0.5), roundUp(8693697600)]).toEqual([123456789013, 1, 1, 8693697600])
    // Oberhalb von 15 Stellen bleibt die 15-stellige Rundung: Excel zeigt 369.792.900.021.001 auch mit zwei Nachkommastellen.
    expect([roundUp(369792900021000.7, 2), roundUp(36979290002130.2)]).toEqual([369792900021001, 36979290002131])
  })

  it('Vergleiche: beide Seiten auf 15 geltende Stellen gerundet', () => {
    const sum = (411130.9 + 1023471.01 + 353646.09) / 89412400
    expect(sum > 0.02).toBe(true)
    expect([gt(sum, 0.02), eq(sum, 0.02), le(sum, 0.02), ge(sum, 0.02), lt(sum, 0.02), ne(sum, 0.02)]).toEqual([false, true, true, true, false, false])
    expect([eq(0.7000000000000001, 0.7), eq(0.1 + 0.2, 0.3), eq(1, 1 + 1e-14), eq(0, 1e-300), eq(0, 0)]).toEqual([true, true, false, false, true])
    // Das Fenster hängt an den Dezimalstellen: 1,0000000000000036 ist gleich 1, 0,9999999999999993 kleiner.
    expect([eq(1, 1.0000000000000036), lt(0.9999999999999993, 1), gt(1.0000000000000053, 1)]).toEqual([true, true, true])
    expect([gt(2, 1), lt(1, 2), ge(1, 2), le(2, 1)]).toEqual([true, true, false, false])
    expect([minus(0.3, 0.1 + 0.2), minus(5, 3), plus(0.1 + 0.2, -0.3), plus(2, 3)]).toEqual([0, 2, 0, 5])
    expect([minus(1.0000000000000018, 1), minus(1.0000000000000013, 1)]).toEqual([1.0000000000000018 - 1, 0])
    expect([sameNumber(0.1 + 0.2, 0.3), sameNumber('1', 1), sameNumber(null, 0)]).toEqual([true, false, false])
  })

  it('Vergleiche, Subtraktion, Aufrunden und Summen stimmen mit der Messung an Excel 16.0.20326 überein', () => {
    type Comparison = { a: number; b: number; eq: number; lt: number; le: number; gt: number; ge: number; minus: number; minusNull?: number }
    const measured = JSON.parse(readFileSync(new URL('./fixtures/excel-semantik.json', import.meta.url), 'utf8')) as {
      vergleiche: Comparison[]
      vergleicheFormel: Comparison[]
      aufrunden: { x: number; roundUp0: number; roundUp2: number }[]
      summen: { werte: number[]; summe: number; klammern: number }[]
    }
    expect([measured.vergleiche.length, measured.vergleicheFormel.length, measured.aufrunden.length]).toEqual([451, 363, 193])
    const flag = (value: boolean): number => (value ? 1 : 0)
    // Die Messmappe vergleicht B mit A (`=WENN(B<A;1;0)`) und rechnet `=B-A` als ganze Formel.
    for (const row of [...measured.vergleiche, ...measured.vergleicheFormel]) {
      const actual = { eq: flag(eq(row.b, row.a)), lt: flag(lt(row.b, row.a)), le: flag(le(row.b, row.a)), gt: flag(gt(row.b, row.a)), ge: flag(ge(row.b, row.a)) }
      expect(actual, `${row.b} gegen ${row.a}`).toEqual({ eq: row.eq, lt: row.lt, le: row.le, gt: row.gt, ge: row.ge })
      expect(minus(row.b, row.a), `${row.b} − ${row.a}`).toBe(row.minus)
      // `=WENN(B-A=0;…)`: Innerhalb einer Formel bleibt der Rest stehen und ist nur dann 0, wenn er genau 0 ist.
      if (row.minusNull !== undefined) expect(flag(eq(row.b - row.a, 0)), `${row.b} − ${row.a} = 0`).toBe(row.minusNull)
    }
    for (const row of measured.aufrunden) {
      expect(roundUp(row.x), `ROUNDUP(${row.x};0)`).toBe(row.roundUp0)
      expect(roundUp(row.x, 2), `ROUNDUP(${row.x};2)`).toBe(row.roundUp2)
    }
    for (const row of measured.summen) {
      expect(sum(row.werte), `SUMME(${row.werte.join(';')})`).toBe(row.summe)
      const [a = 0, b = 0, c = 0, d = 0] = row.werte
      expect(plus(a + b, c + d), `(${a}+${b})+(${c}+${d})`).toBe(row.klammern)
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
    // VERGLEICH(…;0) sucht Zahlen genau (Excel, Blatt 03 Fall „Konfidenzniveau 0,7000000000000001“), anders als `=`.
    expect(() => matchExact(0.7000000000000001, [0.6, 0.7, 0.8])).toThrow(FormulaError)
    expect(() => matchExact(null, [null])).toThrow(FormulaError)
    expect(indexOf([[1, 2], [3, 4]], 2, 1)).toBe(3)
    expect(() => indexOf([[1]], 2, 1)).toThrow(FormulaError)
  })

  it('Prüfhinweise werden nach dem führenden Zeichen eingestuft', () => {
    expect([toneOf('✔ ok'), toneOf('⚠ prüfen'), toneOf('✖ nein'), toneOf('Nicht angewandt'), toneOf(null)]).toEqual(['success', 'warning', 'danger', 'neutral', 'neutral'])
  })
})
