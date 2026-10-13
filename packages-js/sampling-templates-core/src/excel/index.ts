/**
 * Excel-Semantik der Vorlage als kleine, reine Funktionen. Die Rechenkerne
 * bilden die Formeln Zelle für Zelle nach; diese Helfer sorgen dafür, dass
 * Leerwerte, Fehlerwerte und Rundung dieselben Ergebnisse liefern wie die
 * Arbeitsmappe. Vorkommende Funktionen: `docs/excel-funktionen.md`.
 *
 * Abbildung der Werte: Zahl bleibt Zahl, Text bleibt Text, eine leere Zelle
 * und `""` (aus `IFERROR(…;"")`) sind `null`.
 */
import type { CellValue } from '../model/types'

/** Fehlerwert einer Formel (`#DIV/0!`, `#WERT!`, `#NV`); `guard` macht daraus `null`. */
export class FormulaError extends Error {
  constructor(message = 'Fehlerwert') {
    super(message)
    this.name = 'FormulaError'
  }
}

/** `ISTZAHL` / `ISNUMBER`. */
export function isNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value)
}

/** Leere Zelle oder `""`. */
export function isBlank(value: unknown): value is null | undefined | '' {
  return value === null || value === undefined || value === ''
}

/** `N(x)`: Zahl bleibt, alles andere (leer, Text) ist 0. */
export function n(value: unknown): number {
  return isNumber(value) ? value : 0
}

/**
 * Pflichtwert in einer Rechnung: liefert die Zahl oder löst einen Fehlerwert
 * aus. Die Vorlage rechnet mit leeren Eingaben als 0 weiter; die Webfassung
 * zeigt stattdessen „Angabe fehlt“ (siehe `docs/abweichungen.md`).
 */
export function required(value: unknown): number {
  if (!isNumber(value)) throw new FormulaError('Angabe fehlt')
  return value
}

/** `IFERROR(formel;"")`: Fehlerwerte und nicht endliche Zahlen werden `null`. */
export function guard<T extends CellValue>(formula: () => T): T | null {
  try {
    const value = formula()
    return typeof value === 'number' && !Number.isFinite(value) ? null : value
  } catch (error) {
    if (error instanceof FormulaError) return null
    throw error
  }
}

/** `IFERROR(formel;ersatz)` mit einem Ersatzwert, z. B. `IFERROR(D51/D9;1)`. */
export function ifError<T extends CellValue, F extends CellValue>(formula: () => T, fallback: F): T | F {
  const value = guard(formula)
  return value === null ? fallback : value
}

/**
 * Toleranz der Tabellenkalkulation bei Vergleichen: Zwei Zahlen gelten als
 * gleich, wenn sie sich um weniger als 2⁻⁴⁸ (rund 3,6 · 10⁻¹⁵) ihres Betrags
 * unterscheiden. Gemessen an LibreOffice 24.2 (`scripts/measure_semantics.py`,
 * `test/fixtures/libreoffice-semantik.json`); Excel vergleicht nach
 * Herstellerangabe mit 15 signifikanten Stellen.
 */
const COMPARE_EPSILON = 2 ** -48

/** Gleichheit zweier Zahlen wie `=` in der Tabellenkalkulation. */
export function eq(a: number, b: number): boolean {
  if (a === b) return true
  const difference = Math.abs(a - b)
  return difference < Math.abs(a) * COMPARE_EPSILON && difference < Math.abs(b) * COMPARE_EPSILON
}

/** `<>` */
export function ne(a: number, b: number): boolean {
  return !eq(a, b)
}

/** `<` */
export function lt(a: number, b: number): boolean {
  return a < b && !eq(a, b)
}

/** `<=` */
export function le(a: number, b: number): boolean {
  return a < b || eq(a, b)
}

/** `>` */
export function gt(a: number, b: number): boolean {
  return a > b && !eq(a, b)
}

/** `>=` */
export function ge(a: number, b: number): boolean {
  return a > b || eq(a, b)
}

/** `a - b`: Ein Ergebnis innerhalb der Vergleichstoleranz ist genau 0 (kein Rest wie 3 · 10⁻⁹). */
export function minus(a: number, b: number): number {
  return eq(a, b) ? 0 : a - b
}

/** `a + b`: Heben sich die Summanden innerhalb der Vergleichstoleranz auf, ist das Ergebnis genau 0. */
export function plus(a: number, b: number): number {
  return eq(a, -b) ? 0 : a + b
}

/** Ganze Zahl, wenn der Wert innerhalb der Vergleichstoleranz an ihr liegt; sonst abgerundet. */
function approxFloor(value: number): number {
  const nearest = Math.round(value)
  return eq(value, nearest) ? nearest : Math.floor(value)
}

/** Signifikante Stellen, auf die die Tabellenkalkulation vor dem Aufrunden kürzt. */
const ROUND_SIGNIFICANT_DIGITS = 12

/**
 * `AUFRUNDEN` / `ROUNDUP(x;stellen)`: von null weg. Wie die Tabellenkalkulation
 * kürzt die Funktion den Wert zuerst auf zwölf signifikante Stellen (Richtung
 * −∞) und rundet erst dann auf: 100,0000000009 bleibt 100, 100,000000001 wird
 * 101. Ganzzahlige Stellen bleiben immer erhalten. Verhalten an LibreOffice
 * 24.2 gemessen (`test/fixtures/libreoffice-semantik.json`).
 */
export function roundUp(value: number, digits = 0): number {
  if (value === 0 || !Number.isFinite(value)) return value
  const exponent = Math.floor(Math.log10(Math.abs(value)))
  const kept = Math.max(ROUND_SIGNIFICANT_DIGITS - 1 - exponent, 0)
  const cut = approxFloor(value * 10 ** kept) / 10 ** (kept - digits)
  const magnitude = Math.abs(cut)
  const nearest = Math.round(magnitude)
  const rounded = eq(magnitude, nearest) ? nearest : Math.ceil(magnitude)
  return rounded === 0 ? 0 : (Math.sign(cut) * rounded) / 10 ** digits
}

/** Division mit `#DIV/0!`. */
export function divide(dividend: number, divisor: number): number {
  if (divisor === 0) throw new FormulaError('#DIV/0!')
  return dividend / divisor
}

/** `WURZEL` / `SQRT` mit `#ZAHL!` für negative Werte. */
export function squareRoot(value: number): number {
  if (value < 0) throw new FormulaError('#ZAHL!')
  return Math.sqrt(value)
}

function numbers(values: readonly unknown[]): number[] {
  return values.filter(isNumber)
}

/** `SUMME` / `SUM` über einen Bereich: Text und leere Zellen zählen nicht. */
export function sum(values: readonly unknown[]): number {
  return numbers(values).reduce((total, value) => total + value, 0)
}

/** `ANZAHL` / `COUNT`: Anzahl der Zahlen. */
export function count(values: readonly unknown[]): number {
  return numbers(values).length
}

/** `MAX` über einen Bereich; ohne Zahl 0. */
export function max(values: readonly unknown[]): number {
  const found = numbers(values)
  return found.length ? Math.max(...found) : 0
}

/** `MIN` über einen Bereich; ohne Zahl 0. */
export function min(values: readonly unknown[]): number {
  const found = numbers(values)
  return found.length ? Math.min(...found) : 0
}

/** Textvergleich wie `=` in Excel: ohne Beachtung der Groß- und Kleinschreibung. */
export function sameText(left: unknown, right: string): boolean {
  return typeof left === 'string' && left.toLowerCase() === right.toLowerCase()
}

/** Zahlengleichheit zweier Zellwerte mit der Toleranz der Tabellenkalkulation. */
export function sameNumber(left: unknown, right: unknown): boolean {
  return isNumber(left) && isNumber(right) && eq(left, right)
}

/** Text einer Zelle, wie ihn Textfunktionen sehen. */
function textOf(value: unknown): string {
  return isBlank(value) ? '' : String(value)
}

/** `LINKS` / `LEFT`. */
export function left(value: unknown, length = 1): string {
  return textOf(value).slice(0, length)
}

/** `SUCHEN` / `SEARCH`: Position ab 1, ohne Beachtung der Groß- und Kleinschreibung; sonst `#WERT!`. */
export function search(needle: string, value: unknown): number {
  const position = textOf(value).toLowerCase().indexOf(needle.toLowerCase())
  if (position < 0) throw new FormulaError('#WERT!')
  return position + 1
}

/** `SUMMEWENN` / `SUMIF` mit Gleichheitskriterium. */
export function sumIf(range: readonly unknown[], criterion: CellValue, values: readonly unknown[]): number {
  const matches = (candidate: unknown): boolean =>
    typeof criterion === 'string' ? sameText(candidate, criterion) : sameNumber(candidate, criterion)
  return sum(values.filter((_, index) => matches(range[index])))
}

/** `VERGLEICH(x;bereich;0)` / `MATCH`: Position ab 1 oder `#NV`. */
export function matchExact(value: unknown, range: readonly unknown[]): number {
  const index = range.findIndex((candidate) => (typeof value === 'string' ? sameText(candidate, value) : sameNumber(candidate, value)))
  if (index < 0 || isBlank(value)) throw new FormulaError('#NV')
  return index + 1
}

/** `INDEX(tabelle;zeile;spalte)` mit Positionen ab 1. */
export function indexOf<T>(table: readonly (readonly T[])[], row: number, column: number): T {
  const value = table[row - 1]?.[column - 1]
  if (value === undefined) throw new FormulaError('#BEZUG!')
  return value
}

/** Einstufung eines Prüfhinweises nach dem führenden Zeichen der Vorlage. */
export function toneOf(text: unknown): 'success' | 'warning' | 'danger' | 'neutral' {
  if (typeof text !== 'string') return 'neutral'
  if (text.startsWith('✔')) return 'success'
  if (text.startsWith('⚠')) return 'warning'
  return text.startsWith('✖') ? 'danger' : 'neutral'
}
