// CSV für Excel (deutsch): Trenner „;“, UTF-8-BOM, Zeilenende CRLF, Zahlen
// mit Dezimalkomma ohne Tausendertrenner, Schutz gegen Formel-Injektion
// (Präfix „'“ vor Texten, die mit = + - @ Tab oder CR beginnen).

/** Zellwert: Zahlen werden mit Dezimalkomma geschrieben, `Date` als ISO 8601, `null`/`undefined` leer. */
export type CsvValue = string | number | bigint | boolean | Date | null | undefined

/** Schreiboptionen; Standard ist Excel-DE. */
export interface CsvOptions {
  /** Feldtrenner (Standard `;`). */
  delimiter?: string
  /** UTF-8-BOM voranstellen (Standard `true`; Excel erkennt sonst keine Umlaute). */
  bom?: boolean
  /** Formelschutz für Texte (Standard `true`). */
  guardFormulas?: boolean
  /** Dezimaltrenner für Zahlen (Standard `,`). */
  decimal?: ',' | '.'
  /** Zeilenende (Standard `\r\n`). */
  lineEnding?: string
}

/** UTF-8-Byte-Order-Mark am Dateianfang. */
export const CSV_BOM = '﻿'
const FORMULA_START = /^[=+\-@\t\r]/

function numberCell(value: number | bigint, decimal: string): string {
  if (typeof value === 'number' && !Number.isFinite(value)) return ''
  const text = String(value)
  return decimal === '.' ? text : text.replace('.', decimal)
}

function plainCell(value: CsvValue, decimal: string): { text: string; isNumber: boolean } {
  if (value === null || value === undefined) return { text: '', isNumber: false }
  if (typeof value === 'number' || typeof value === 'bigint') return { text: numberCell(value, decimal), isNumber: true }
  if (value instanceof Date) return { text: Number.isNaN(value.getTime()) ? '' : value.toISOString(), isNumber: false }
  return { text: String(value), isNumber: false }
}

/** Eine Zelle: Formelschutz für Texte, Anführungszeichen nach RFC 4180 bei Trenner, `"` oder Zeilenumbruch. */
export function escapeCsvCell(value: CsvValue, options: CsvOptions = {}): string {
  const delimiter = options.delimiter ?? ';'
  const { text, isNumber } = plainCell(value, options.decimal ?? ',')
  const guarded = !isNumber && (options.guardFormulas ?? true) && FORMULA_START.test(text) ? `'${text}` : text
  const needsQuotes = guarded.includes(delimiter) || /["\n\r]/.test(guarded)
  return needsQuotes ? `"${guarded.replace(/"/g, '""')}"` : guarded
}

/** Ganze Datei aus Zeilen (erste Zeile = Kopf); jede Zeile endet mit dem Zeilenende. */
export function toCsv(rows: readonly (readonly CsvValue[])[], options: CsvOptions = {}): string {
  const delimiter = options.delimiter ?? ';'
  const lineEnding = options.lineEnding ?? '\r\n'
  const body = rows.map((row) => row.map((cell) => escapeCsvCell(cell, options)).join(delimiter) + lineEnding).join('')
  return (options.bom ?? true) ? CSV_BOM + body : body
}

/** Deklarative Spalte für `recordsToCsv`. */
export interface CsvColumn<R> {
  /** Spaltenüberschrift. */
  label: string
  /** Feldname oder Auswahlfunktion. */
  value: keyof R | ((record: R) => CsvValue)
}

/** CSV aus Datensätzen über deklarative Spalten. */
export function recordsToCsv<R>(records: readonly R[], columns: readonly CsvColumn<R>[], options: CsvOptions = {}): string {
  const pick = (record: R, column: CsvColumn<R>): CsvValue =>
    typeof column.value === 'function' ? column.value(record) : (record[column.value] as CsvValue)
  const rows = [columns.map((column) => column.label), ...records.map((record) => columns.map((column) => pick(record, column)))]
  return toCsv(rows, options)
}

/** CSV-Text als `Blob` (`text/csv;charset=utf-8`) für den Download. */
export function csvBlob(csv: string): Blob {
  return new Blob([csv], { type: 'text/csv;charset=utf-8' })
}

interface CsvReader {
  rows: string[][]
  row: string[]
  cell: string
  quoted: boolean
}

function endCell(state: CsvReader): void {
  state.row.push(state.cell)
  state.cell = ''
}

function endRow(state: CsvReader): void {
  endCell(state)
  state.rows.push(state.row)
  state.row = []
}

function readQuoted(state: CsvReader, char: string, next: string | undefined): number {
  if (char !== '"') {
    state.cell += char
    return 0
  }
  if (next === '"') {
    state.cell += '"'
    return 1
  }
  state.quoted = false
  return 0
}

function readPlain(state: CsvReader, char: string, next: string | undefined, delimiter: string): number {
  if (char === '"' && state.cell === '') state.quoted = true
  else if (char === delimiter) endCell(state)
  else if (char === '\r' && next === '\n') {
    endRow(state)
    return 1
  } else if (char === '\n' || char === '\r') endRow(state)
  else state.cell += char
  return 0
}

/** Liest CSV nach RFC 4180 (Anführungszeichen, `""`, Zeilenumbrüche in Zellen); BOM wird entfernt, Leerzeilen am Ende entfallen. */
export function parseCsv(text: string, options: Pick<CsvOptions, 'delimiter'> = {}): string[][] {
  const source = text.replace(/^\ufeff/, '')
  const delimiter = options.delimiter ?? ';'
  const state: CsvReader = { rows: [], row: [], cell: '', quoted: false }
  for (let index = 0; index < source.length; index += 1) {
    const char = source[index] ?? ''
    const next = source[index + 1]
    index += state.quoted ? readQuoted(state, char, next) : readPlain(state, char, next, delimiter)
  }
  if (state.cell !== '' || state.row.length > 0) endRow(state)
  return state.rows
}
