import { describe, expect, it } from 'vitest'
import { choiceValue, formatFieldInput, formatFieldValue, optionsOf, parseFieldInput, percentToFraction } from '../src/format/numbers'
import { PARAMETERS } from '../src/sheets/01_Parameter/index'

const nbsp = (text: string): string => text.replaceAll(String.fromCharCode(160), ' ')

describe('Deutsche Zahleneingabe', () => {
  it('Beträge mit Tausenderpunkt, Leerzeichen und €', () => {
    expect(parseFieldInput({ type: 'amount' }, '48.500.000,00')).toEqual({ ok: true, value: 48500000 })
    expect(parseFieldInput({ type: 'amount' }, ' 6.200.000,50 € ')).toEqual({ ok: true, value: 6200000.5 })
    expect(parseFieldInput({ type: 'amount' }, '')).toEqual({ ok: true, value: null })
  })

  it('Prozentfelder: Eingabe in Prozent, Wert als Anteil ohne Gleitkommarauschen', () => {
    expect(parseFieldInput({ type: 'percent' }, '0,7')).toEqual({ ok: true, value: 0.007 })
    expect(parseFieldInput({ type: 'percent' }, '2 %')).toEqual({ ok: true, value: 0.02 })
    expect([percentToFraction('2'), percentToFraction('12.5'), percentToFraction('-0.7'), percentToFraction('150')]).toEqual([0.02, 0.125, -0.007, 1.5])
  })

  it('Dezimalfelder nehmen mehr als zwei Nachkommastellen', () => {
    expect(parseFieldInput({ type: 'decimal' }, '0,045')).toEqual({ ok: true, value: 0.045 })
    expect(parseFieldInput({ type: 'decimal' }, '0,0451')).toEqual({ ok: true, value: 0.0451 })
    expect(parseFieldInput({ type: 'percent' }, '0,125 %')).toEqual({ ok: true, value: 0.00125 })
    expect(parseFieldInput({ type: 'amount' }, '1,234')).toEqual({ ok: false, reason: 'ambiguous' })
    // Zu genaue Eingaben nennen den Grund (Abnahme N6): Betrag mit mehr als zwei, Dezimalzahl mit mehr als zehn Nachkommastellen.
    expect(parseFieldInput({ type: 'amount' }, '0,045')).toEqual({ ok: false, reason: 'cents' })
    expect(parseFieldInput({ type: 'amount' }, '12,3456')).toEqual({ ok: false, reason: 'cents' })
    expect(parseFieldInput({ type: 'decimal' }, '0,12345678901')).toEqual({ ok: false, reason: 'decimals' })
    expect(parseFieldInput({ type: 'decimal' }, '0,1234567890')).toEqual({ ok: true, value: 0.123456789 })
  })

  it('Ganzzahlfelder: Punkt ist Tausendertrenner, Nachkommastellen werden abgelehnt', () => {
    expect(parseFieldInput({ type: 'integer' }, '1.200')).toEqual({ ok: true, value: 1200 })
    expect(parseFieldInput({ type: 'integer' }, '420')).toEqual({ ok: true, value: 420 })
    expect(parseFieldInput({ type: 'integer' }, '4,5')).toEqual({ ok: false, reason: 'integer' })
    expect(parseFieldInput({ type: 'integer' }, '0.045')).toEqual({ ok: false, reason: 'ambiguous' })
    expect(parseFieldInput({ type: 'integer' }, '12.345.678')).toEqual({ ok: true, value: 12345678 })
  })

  it('mehrdeutige und ungültige Eingaben werden abgelehnt, nicht geraten', () => {
    expect(parseFieldInput({ type: 'amount' }, '1.5')).toEqual({ ok: false, reason: 'ambiguous' })
    expect(parseFieldInput({ type: 'decimal' }, 'abc')).toEqual({ ok: false, reason: 'invalid' })
  })

  it('Text- und Auswahlfelder', () => {
    expect(parseFieldInput({ type: 'text' }, '  2025/2026 ')).toEqual({ ok: true, value: '2025/2026' })
    expect(parseFieldInput({ type: 'text' }, '  ')).toEqual({ ok: true, value: null })
  })
})

describe('Deutsche Zahlenausgabe', () => {
  it('Eingabefelder ohne Einheit', () => {
    expect(formatFieldInput({ type: 'amount' }, 48500000)).toBe('48.500.000,00')
    expect(formatFieldInput({ type: 'percent' }, 0.007)).toBe('0,7')
    expect(formatFieldInput({ type: 'decimal' }, 0.045)).toBe('0,045')
    expect(formatFieldInput({ type: 'integer' }, 1200)).toBe('1.200')
    expect(formatFieldInput({ type: 'integer' }, null)).toBe('')
  })

  it('jede formatierte Eingabe wird wieder zum selben Wert gelesen', () => {
    for (const [type, value] of [['amount', 6200000], ['percent', 0.007], ['percent', 0.00125], ['decimal', 0.12], ['decimal', 0.045], ['integer', 1200], ['integer', 88]] as const) {
      expect(parseFieldInput({ type }, formatFieldInput({ type }, value))).toEqual({ ok: true, value })
    }
  })

  it('Ergebnisse mit Einheit', () => {
    expect(nbsp(formatFieldValue({ type: 'amount' }, 480681.818181818))).toBe('480.681,82 €')
    expect(nbsp(formatFieldValue({ type: 'percent' }, 0.00652417994376757))).toBe('0,652 %')
    expect(formatFieldValue({ type: 'integer' }, 92)).toBe('92')
    expect(formatFieldValue({ type: 'decimal', format: '0.000' }, 1.036)).toBe('1,036')
    expect(formatFieldValue({ type: 'integer' }, 'TE ≤ AE')).toBe('TE ≤ AE')
    expect(formatFieldValue({ type: 'amount' }, null)).toBe('—')
    expect(nbsp(formatFieldValue({ type: 'choice', list: 'confidence' }, 0.7))).toBe('70 %')
  })

  it('Auswahllisten aus Blatt 01', () => {
    const confidence = optionsOf('confidence', PARAMETERS)
    expect(confidence.map((option) => nbsp(option.label))).toEqual(['60 %', '70 %', '80 %', '90 %', '95 % (außerhalb Anh. I)'])
    expect(choiceValue(confidence, '0.7')).toBe(0.7)
    expect(choiceValue(optionsOf('category', PARAMETERS), '2')).toBe(2)
    expect(choiceValue(optionsOf('yesNo', PARAMETERS), 'Ja')).toBe('Ja')
    expect(choiceValue(optionsOf('yesNo', PARAMETERS), '')).toBeNull()
  })
})
