/**
 * Deutsche Zahleneingabe und -ausgabe der Rechenblätter. Gelesen und
 * formatiert wird mit den gemeinsamen Helfern aus `@auditcore/common`; hier
 * steht nur, was vom Feldtyp abhängt (Prozentfelder, Ganzzahlen, Auswahl).
 */
import { EMPTY_VALUE, PARSE_FAILURE_HINTS, formatEur, formatInt, formatNumber, formatPercent, parseDecimalResult } from '@auditcore/common'
import { isBlank, isNumber } from '../excel/index'
import type { FieldDefinition } from '../model/definition'
import type { CellValue, ListKey, Parameters } from '../model/types'

/** Nachkommastellen der Prozentausgabe (Gesamtfehlerquote 0,652 %). */
export const PERCENT_DIGITS = 3
const MAX_DECIMALS = 10

export type InputFailure = 'ambiguous' | 'invalid' | 'negative' | 'integer' | 'cents' | 'decimals'

/** Ergebnis einer Feldeingabe: Wert (leer = `null`) oder Grund der Ablehnung. */
export type InputResult = { ok: true; value: CellValue } | { ok: false; reason: InputFailure }

/** Erklärende Texte zu abgelehnten Eingaben; `integer` ergänzt die gemeinsamen Hinweise. */
export const INPUT_FAILURE_HINTS: Readonly<Record<InputFailure, string>> = {
  ambiguous: PARSE_FAILURE_HINTS.ambiguous,
  invalid: PARSE_FAILURE_HINTS.invalid,
  negative: PARSE_FAILURE_HINTS.negative,
  integer: 'ganze Zahl erwartet',
  cents: 'Beträge mit höchstens zwei Nachkommastellen',
  decimals: `höchstens ${MAX_DECIMALS} Nachkommastellen`,
}

/** „2“ Prozent → 0.02, ohne Gleitkommarauschen (Verschieben des Kommas im Dezimaltext). */
export function percentToFraction(decimal: string): number {
  const negative = decimal.startsWith('-')
  const [integer = '0', fraction = ''] = decimal.replace('-', '').split('.')
  const digits = integer.padStart(3, '0')
  const shifted = `${digits.slice(0, -2)}.${digits.slice(-2)}${fraction}`
  return Number(negative ? `-${shifted}` : shifted)
}

/** In Ganzzahlfeldern ist der Punkt Tausendertrenner („1.200“ = 1200); „0.045“ ist es nicht und wird abgelehnt. */
function groupedInteger(text: string): number | null {
  const compact = text.replace(/\s/g, '')
  return /^-?[1-9]\d{0,2}(\.\d{3})+$/.test(compact) ? Number(compact.replace(/\./g, '')) : null
}

/**
 * In Dezimal- und Prozentfeldern ist das Komma immer Dezimaltrenner: „0,045“ ist
 * dort eindeutig, während die gemeinsame Betragsregel eine einzelne Dreiergruppe
 * hinter dem Komma als mehrdeutig ablehnt.
 */
function decimalComma(text: string): string | null {
  const compact = text.replace(/[\s€]/g, '').replace(/−/g, '-')
  return /^-?\d+,\d{3}$/.test(compact) ? compact.replace(',', '.') : null
}

type DecimalText = { ok: true; value: string | null } | { ok: false; reason: InputFailure }

/** Zu viele Nachkommastellen für den Feldtyp: nennt den Grund, statt „mehrdeutig“ oder „keine gültige Zahl“ zu melden. */
function tooPrecise(type: FieldDefinition['type'], text: string): InputFailure | null {
  const match = /^-?(\d+),(\d+)$/.exec(text.replace(/[\s€%]/g, '').replace(/−/g, '-'))
  if (!match) return null
  const [, integer = '', decimals = ''] = match
  if (type !== 'amount') return decimals.length > MAX_DECIMALS ? 'decimals' : null
  // „1,234“ im Betragsfeld bleibt mehrdeutig (englische Tausendergruppe?); „0,045“ und „1,2345“ sind eindeutig zu genau.
  const grouped = decimals.length === 3 && /^[1-9]\d{0,2}$/.test(integer)
  return decimals.length > 2 && !grouped ? 'cents' : null
}

function readDecimal(type: FieldDefinition['type'], text: string): DecimalText {
  const precise = tooPrecise(type, text)
  if (precise) return { ok: false, reason: precise }
  const cleaned = type === 'percent' ? text.replace(/%/g, ' ') : text
  const plain = type === 'decimal' || type === 'percent' ? decimalComma(cleaned) : null
  if (plain !== null) return { ok: true, value: plain }
  const result = parseDecimalResult(cleaned, { mode: 'strict-de', maxFractionDigits: type === 'amount' ? 2 : MAX_DECIMALS })
  if (result.ok) return result
  return result.reason === 'empty' ? { ok: true, value: null } : { ok: false, reason: result.reason }
}

function parseNumber(type: FieldDefinition['type'], text: string): InputResult {
  const grouped = type === 'integer' ? groupedInteger(text) : null
  if (grouped !== null) return { ok: true, value: grouped }
  const decimal = readDecimal(type, text)
  if (!decimal.ok || decimal.value === null) return decimal
  if (type === 'integer' && decimal.value.includes('.')) return { ok: false, reason: 'integer' }
  return { ok: true, value: type === 'percent' ? percentToFraction(decimal.value) : Number(decimal.value) }
}

/** Liest die Texteingabe eines Felds; Prozentfelder werden in Prozent eingegeben und als Anteil gespeichert. */
export function parseFieldInput(field: Pick<FieldDefinition, 'type'>, text: string): InputResult {
  if (field.type === 'text' || field.type === 'choice' || field.type === 'check') {
    const trimmed = text.trim()
    return { ok: true, value: trimmed === '' ? null : trimmed }
  }
  return parseNumber(field.type, text)
}

function decimalsOf(format: string | undefined, fallback: number): number {
  const match = /0\.(0+)/.exec(format ?? '')
  return match?.[1] ? match[1].length : fallback
}

/** Text eines Werts im Eingabefeld (ohne Einheit): `48.500.000,00`, `2`, `0,12`. */
export function formatFieldInput(field: Pick<FieldDefinition, 'type'>, value: CellValue | undefined): string {
  if (isBlank(value)) return ''
  if (!isNumber(value)) return String(value)
  if (field.type === 'amount') return formatNumber(value, { digits: 2 })
  if (field.type === 'integer') return formatInt(value)
  // Prozentfelder zeigen alle eingegebenen Stellen: Gerechnet wird mit allen, also stehen auch alle im Feld.
  if (field.type === 'percent') return formatNumber(value * 100, { maxDigits: MAX_DECIMALS, grouping: false })
  return formatNumber(value, { maxDigits: MAX_DECIMALS, grouping: false })
}

/** Anzeige eines Werts mit Einheit: `480.681,82 €`, `92`, `1,036`, `0,652 %`; Texte der Vorlage bleiben unverändert. */
export function formatFieldValue(field: Pick<FieldDefinition, 'type' | 'format' | 'list'>, value: CellValue | undefined, empty: string = EMPTY_VALUE): string {
  if (isBlank(value)) return empty
  if (!isNumber(value)) return String(value)
  if (field.list === 'confidence') return formatPercent(value, { digits: 0 })
  if (field.type === 'amount') return formatEur(value)
  if (field.type === 'integer') return formatInt(value)
  if (field.type === 'percent') return formatPercent(value, { digits: PERCENT_DIGITS })
  if (field.type === 'decimal') return formatNumber(value, { digits: decimalsOf(field.format, 4) })
  return formatNumber(value, { maxDigits: MAX_DECIMALS })
}

/** Eintrag einer Auswahlliste. */
export interface ChoiceOption {
  value: string | number
  label: string
}

/** Einträge einer Auswahlliste aus Blatt 01; das Konfidenzniveau kommt aus der z-Tabelle. */
export function optionsOf(list: ListKey, parameters: Parameters, outsideAnnex = 'außerhalb Anh. I'): ChoiceOption[] {
  if (list === 'confidence') {
    return parameters.zTable.map((row) => ({
      value: row.confidence,
      label: row.inAnnex ? formatPercent(row.confidence, { digits: 0 }) : `${formatPercent(row.confidence, { digits: 0 })} (${outsideAnnex})`,
    }))
  }
  return parameters.lists[list].map((value) => ({ value, label: String(value) }))
}

/** Auswahl eines Felds: Liste aus Blatt 01 oder eigene Einträge; ohne Auswahl leer. */
export function fieldOptions(field: Pick<FieldDefinition, 'list' | 'options'>, parameters: Parameters, outsideAnnex?: string): ChoiceOption[] {
  if (field.options) return field.options.map((value) => ({ value, label: String(value) }))
  return field.list ? optionsOf(field.list, parameters, outsideAnnex) : []
}

/** Wert einer Auswahl aus dem Text des Auswahlfelds (Zahlen bleiben Zahlen). */
export function choiceValue(options: readonly ChoiceOption[], text: string): CellValue {
  return options.find((option) => String(option.value) === text)?.value ?? null
}
