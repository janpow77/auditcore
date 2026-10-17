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
    // Ein Fehlerwert ist Teil der normalen Rechnung (leere Pflichteingabe); die Aufrufkette braucht niemand, sie zu erfassen kostet aber Zeit.
    const limit = Error.stackTraceLimit
    Error.stackTraceLimit = 0
    super(message)
    Error.stackTraceLimit = limit
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
 * Geltende Dezimalstellen, mit denen Excel Zahlen vergleicht und vor dem
 * Aufrunden rundet. Gemessen an Microsoft Excel 16.0.20326
 * (`test/fixtures/excel-semantik.json`): `=`, `<`, `<=`, `>`, `>=` runden beide
 * Seiten auf 15 geltende Stellen und vergleichen dann genau. Das Fenster, in dem
 * zwei Zahlen als gleich gelten, hängt deshalb von der Lage der Dezimalstellen
 * ab: 1 und 1,0000000000000036 sind gleich, 1 und 0,9999999999999993 nicht.
 */
const SIGNIFICANT_DIGITS = 15

/** Zahl auf 15 geltende Dezimalstellen gerundet, wie Excel sie vergleicht. */
export function toSignificant(value: number, digits = SIGNIFICANT_DIGITS): number {
  return value === 0 || !Number.isFinite(value) ? value : Number(value.toPrecision(digits))
}

/** Gleichheit zweier Zahlen wie `=` in Excel. */
export function eq(a: number, b: number): boolean {
  return a === b || toSignificant(a) === toSignificant(b)
}

/** `<>` */
export function ne(a: number, b: number): boolean {
  return !eq(a, b)
}

/** `<` */
export function lt(a: number, b: number): boolean {
  return a !== b && toSignificant(a) < toSignificant(b)
}

/** `<=` */
export function le(a: number, b: number): boolean {
  return a === b || toSignificant(a) <= toSignificant(b)
}

/** `>` */
export function gt(a: number, b: number): boolean {
  return a !== b && toSignificant(a) > toSignificant(b)
}

/** `>=` */
export function ge(a: number, b: number): boolean {
  return a === b || toSignificant(a) >= toSignificant(b)
}

/** Exponent zur Basis 2 (wie `frexp`, um eins verschoben): 1 ≤ |x| / 2^e < 2. */
function binaryExponent(value: number): number {
  const magnitude = Math.abs(value)
  const exponent = Math.floor(Math.log2(magnitude))
  if (2 ** exponent > magnitude) return exponent - 1
  return 2 ** (exponent + 1) <= magnitude ? exponent + 1 : exponent
}

/** Auslöschung, ab der Excel das Ergebnis der letzten Addition oder Subtraktion einer Formel auf 0 setzt (Binärstellen). */
const CANCELLATION_BITS = 50

/**
 * Ergebnis der letzten Addition oder Subtraktion einer Formel: Liegt es um
 * mindestens 50 Binärstellen unter dem kleineren Summanden, setzt Excel es auf
 * genau 0 (gemessen; 1 − 1,0000000000000013 ergibt 0, 1 − 1,0000000000000018
 * ergibt 1,8 · 10⁻¹⁵). Innerhalb einer Formel rechnet Excel ohne diese Regel.
 */
function settled(result: number, left: number, right: number): number {
  if (result === 0 || !Number.isFinite(result)) return result
  const smaller = Math.min(Math.abs(left), Math.abs(right))
  if (smaller === 0) return result
  return binaryExponent(smaller) - binaryExponent(result) >= CANCELLATION_BITS ? 0 : result
}

/** `a - b` als letzte Rechenoperation einer Formel (Auslöschung ergibt genau 0, siehe `settled`). */
export function minus(a: number, b: number): number {
  return settled(a - b, a, b)
}

/** `a + b` als letzte Rechenoperation einer Formel (Auslöschung ergibt genau 0, siehe `settled`). */
export function plus(a: number, b: number): number {
  return settled(a + b, a, b)
}

/** Ganze Zahl bzw. Dezimalzahl `value · 10^digits` ohne Rundungsfehler der Multiplikation. */
function shiftDecimal(value: number, digits: number): number {
  const text = String(value)
  return digits === 0 || text.includes('e') ? value / 10 ** -digits : Number(`${text}e${digits}`)
}

/**
 * `AUFRUNDEN` / `ROUNDUP(x;stellen)`: von null weg. Wie Excel rundet die
 * Funktion den Wert zuerst auf 15 geltende Stellen und rundet erst dann auf:
 * 100,000000000001 wird 101, 100 · (1 + 16 · 2⁻⁵²) bleibt 100. Gemessen an
 * Excel 16.0.20326 (`test/fixtures/excel-semantik.json`).
 */
export function roundUp(value: number, digits = 0): number {
  if (value === 0 || !Number.isFinite(value)) return value
  const scaled = toSignificant(toSignificant(value) * 10 ** digits)
  return Math.sign(scaled) * shiftDecimal(Math.ceil(Math.abs(scaled)), -digits)
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

/**
 * `SUMME` / `SUM` über einen Bereich: Text und leere Zellen zählen nicht. Wie
 * Excel addiert die Funktion der Reihe nach ohne Fehlerausgleich; nur die
 * letzte Addition folgt der Auslöschungsregel (`plus`): `SUMME(0,1;0,7;0,2;−1)`
 * ergibt 0, `SUMME(0,1;0,2;−0,3;0)` 5,55 · 10⁻¹⁷ (gemessen).
 */
export function sum(values: readonly unknown[]): number {
  const found = numbers(values)
  const last = found.pop()
  if (last === undefined) return 0
  return found.length === 0 ? last : plus(found.reduce((total, value) => total + value), last)
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

/** Zahlengleichheit zweier Zellwerte wie `=` in Excel (15 geltende Stellen). */
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

/**
 * `VERGLEICH(x;bereich;0)` / `MATCH`: Position ab 1 oder `#NV`. Zahlen sucht
 * Excel genau, ohne die 15-Stellen-Regel von `=`: 0,7000000000000001 steht
 * nicht in der Liste 0,6; 0,7; … (gemessen, Blatt 03 C12).
 */
export function matchExact(value: unknown, range: readonly unknown[]): number {
  const index = range.findIndex((candidate) => (typeof value === 'string' ? sameText(candidate, value) : isNumber(value) && candidate === value))
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
