// Einlesen einfacher Tabellendateien (CSV/TSV/Text) ohne Bibliothek.
// Trennzeichen werden erkannt (Semikolon, Tabulator, Komma); Zahlen im
// deutschen (1.234,56) und im englischen Format (1,234.56) werden gelesen.
// Nicht lesbare Zellen werden gezählt, nie still zu 0.

export type Delimiter = ';' | '\t' | ','

export interface ParsedTable {
  delimiter: Delimiter
  header: readonly string[]
  rows: readonly (readonly string[])[]
}

const CANDIDATES: readonly Delimiter[] = [';', '\t', ',']

/** Häufigstes Trennzeichen der ersten Zeile; eine Spalte ohne Trenner ergibt ';'. */
export function detectDelimiter(firstLine: string): Delimiter {
  let best: Delimiter = ';'
  let bestCount = 0
  for (const candidate of CANDIDATES) {
    const count = firstLine.split(candidate).length - 1
    if (count > bestCount) {
      best = candidate
      bestCount = count
    }
  }
  return best
}

/** Eine Zeile mit Anführungszeichen nach RFC 4180 (doppelte "" als Maskierung). */
export function splitLine(line: string, delimiter: Delimiter): string[] {
  const cells: string[] = []
  let current = ''
  let quoted = false
  for (let index = 0; index < line.length; index += 1) {
    const char = line[index]
    if (quoted && char === '"' && line[index + 1] === '"') {
      current += '"'
      index += 1
    } else if (char === '"') {
      quoted = !quoted
    } else if (char === delimiter && !quoted) {
      cells.push(current.trim())
      current = ''
    } else {
      current += char
    }
  }
  cells.push(current.trim())
  return cells
}

/**
 * Text → Tabelle. `hasHeader` legt fest, ob die erste Zeile Spaltennamen
 * enthält; sonst heißen die Spalten „Spalte 1“, „Spalte 2“ …
 */
export function parseTable(text: string, hasHeader: boolean, columnLabel = 'Spalte'): ParsedTable {
  const lines = text.replace(/^\ufeff/, '').split(/\r?\n/).filter((line) => line.trim() !== '')
  const delimiter = detectDelimiter(lines[0] ?? '')
  const cells = lines.map((line) => splitLine(line, delimiter))
  const width = Math.max(0, ...cells.map((row) => row.length))
  const first = hasHeader ? (cells.shift() ?? []) : []
  const header = Array.from({ length: width }, (_, index) => first[index] || `${columnLabel} ${index + 1}`)
  return { delimiter, header, rows: cells }
}

export type DecimalSeparator = ',' | '.'

/**
 * Zelle → Zahl mit ausdrücklichem Dezimaltrenner; der jeweils andere Trenner
 * gilt als Tausenderpunkt. Leer ergibt `null` (fehlend), Unlesbares
 * `undefined`. Währungszeichen, Leerzeichen und Klammern (negativ) werden
 * berücksichtigt.
 */
export function parseNumber(cell: string, decimal: DecimalSeparator): number | null | undefined {
  let text = cell.replace(/[\s\u00a0€$£]|EUR/g, '')
  if (text === '') return null
  const negative = /^\(.*\)$/.test(text)
  if (negative) text = text.slice(1, -1)
  if (!/^[-+]?[\d.,]*\d[\d.,]*(e[-+]?\d+)?$/i.test(text)) return undefined
  const grouping = decimal === ',' ? '.' : ','
  const plain = text.split(grouping).join('')
  if (plain.split(decimal).length > 2) return undefined
  const value = Number(decimal === ',' ? plain.replace(',', '.') : plain)
  if (!Number.isFinite(value)) return undefined
  return negative ? -value : value
}

/**
 * Dezimaltrenner einer Spalte: stehen beide Zeichen in einer Zelle, ist das
 * letzte der Dezimaltrenner; ein Trenner ohne genau drei Folgeziffern ist
 * ebenfalls eindeutig. Sonst entscheidet das Feldtrennzeichen (Semikolon →
 * Komma), die Oberfläche zeigt die Wahl an und lässt sie ändern.
 */
export function detectDecimal(cells: readonly string[], delimiter: Delimiter): DecimalSeparator {
  for (const cell of cells) {
    const comma = cell.lastIndexOf(',')
    const dot = cell.lastIndexOf('.')
    if (comma >= 0 && dot >= 0) return comma > dot ? ',' : '.'
    if (comma >= 0 && !/,\d{3}$/.test(cell)) return ','
    if (dot >= 0 && !/\.\d{3}$/.test(cell)) return '.'
  }
  return delimiter === ',' ? '.' : ','
}

export interface NumberColumn {
  values: (number | null)[]
  /** Zeilennummern (1-basiert, ohne Kopfzeile) mit unlesbarem Inhalt. */
  rejected: number[]
}

/** Eine Spalte als Zahlen; unlesbare Zellen werden verworfen und gemeldet. */
export function numberColumn(table: ParsedTable, column: number, decimal: DecimalSeparator): NumberColumn {
  const values: (number | null)[] = []
  const rejected: number[] = []
  table.rows.forEach((row, index) => {
    const parsed = parseNumber(row[column] ?? '', decimal)
    if (parsed === undefined) rejected.push(index + 1)
    else values.push(parsed)
  })
  return { values, rejected }
}

/** Zellen einer Spalte. */
export function columnCells(table: ParsedTable, column: number): string[] {
  return table.rows.map((row) => row[column] ?? '')
}

/** Index der ersten Spalte, deren nicht leere Zellen überwiegend (≥ 60 %) Zahlen sind; sonst 0. */
export function guessNumberColumn(table: ParsedTable): number {
  const sample = table.rows.slice(0, 50)
  for (let column = 0; column < table.header.length; column += 1) {
    const filled = sample.map((row) => row[column] ?? '').filter((cell) => cell.trim() !== '')
    const numeric = filled.filter((cell) => typeof parseNumber(cell, ',') === 'number').length
    if (filled.length > 0 && numeric / filled.length >= 0.6) return column
  }
  return 0
}
