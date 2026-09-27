/**
 * Eingabe der Bestandsprüfung (Vue und React, reine Funktionen): JSON-Datei
 * oder Tabelle, Spaltenzuordnung und Anfrage für `POST /runs`.
 */
import { detectDecimal, parseNumber, type DecimalSeparator, type ParsedTable } from '@auditcore/common'
import type { BatchchecksCatalogue, BatchchecksDocument, BatchchecksField, BatchchecksRequest } from './types'

export type BatchchecksError = 'noData' | 'noRows' | 'tooMany' | 'noColumns' | 'json' | 'totalVolume'
export type BatchchecksValidation = { ok: true; request: BatchchecksRequest } | { ok: false; error: BatchchecksError }
/** Feld → Spalte der Tabelle (`null` = nicht zugeordnet). */
export type BatchchecksMapping = Readonly<Record<string, number | null>>

const normalize = (text: string): string => text.trim().toLowerCase()

/** Spalten automatisch zuordnen: Spaltenname gleich Feldkennung oder einem Spaltennamen des Katalogs; jede Spalte höchstens einmal. */
export function batchchecksAutoMapping(fields: readonly BatchchecksField[], header: readonly string[]): Record<string, number | null> {
  const names = header.map(normalize)
  const used = new Set<number>()
  const mapping: Record<string, number | null> = {}
  for (const field of fields) {
    const index = names.findIndex((name, column) => !used.has(column) && (name === field.name || field.aliases.includes(name)))
    mapping[field.name] = index < 0 ? null : index
    if (index >= 0) used.add(index)
  }
  return mapping
}

/** Dezimaltrennzeichen aus den Zellen aller zugeordneten Zahlenspalten. */
export function batchchecksDecimal(table: ParsedTable, fields: readonly BatchchecksField[], mapping: BatchchecksMapping): DecimalSeparator {
  const columns = fields.filter((field) => field.numeric).map((field) => mapping[field.name]).filter((column) => column !== null && column !== undefined)
  const cells = table.rows.flatMap((row) => columns.map((column) => row[column] ?? '')).filter((cell) => /[.,]/.test(cell))
  return detectDecimal(cells, table.delimiter)
}

/** Dateiinhalt als JSON behandeln (Endung `.json` oder beginnt mit `[`/`{`). */
export function batchchecksLooksLikeJson(filename: string, text: string): boolean {
  return /\.json$/i.test(filename) || /^\s*[[{]/.test(text.replace(/^\ufeff/, ''))
}

const isRecord = (value: unknown): value is BatchchecksDocument => typeof value === 'object' && value !== null && !Array.isArray(value)

function jsonItems(data: unknown): unknown[] | null {
  if (Array.isArray(data)) return data
  if (!isRecord(data)) return null
  if (Array.isArray(data.documents)) return data.documents as unknown[]
  return Array.isArray(data.fields) ? [data] : null
}

/**
 * Belege aus einer JSON-Datei: Liste, `{"documents": [...]}` oder ein
 * einzelner Lauf der Belegerkennung; `null`, wenn die Datei das nicht ist.
 */
export function batchchecksJsonDocuments(text: string): BatchchecksDocument[] | null {
  let data: unknown
  try {
    data = JSON.parse(text.replace(/^\ufeff/, ''))
  } catch {
    return null
  }
  const items = jsonItems(data)
  return items && items.every(isRecord) ? (items as BatchchecksDocument[]) : null
}

/** Zelle als Wert: leer → `null`, Zahlenfelder als Zahl (Prozentangaben der OCR-Konfidenz als Anteil), Unlesbares unverändert. */
export function batchchecksCellValue(cell: string, field: BatchchecksField, decimal: DecimalSeparator): string | number | null {
  const text = cell.trim()
  if (text === '') return null
  if (!field.numeric) return text
  const percent = /%$/.test(text)
  const parsed = parseNumber(text.replace(/%$/, ''), decimal)
  if (parsed === null || parsed === undefined) return text
  return percent && field.name === 'ocr_confidence' ? parsed / 100 : parsed
}

/** Tabellenzeilen als Belege (nur zugeordnete Felder). */
export function batchchecksTableDocuments(table: ParsedTable, mapping: BatchchecksMapping, fields: readonly BatchchecksField[], decimal: DecimalSeparator): BatchchecksDocument[] {
  const mapped = fields.filter((field) => mapping[field.name] !== null && mapping[field.name] !== undefined)
  return table.rows.map((row) => Object.fromEntries(mapped.map((field) => [field.name, batchchecksCellValue(row[mapping[field.name] ?? -1] ?? '', field, decimal)])))
}

export interface BatchchecksInput {
  catalogue: BatchchecksCatalogue
  table: ParsedTable | null
  json: readonly BatchchecksDocument[] | null
  mapping: BatchchecksMapping
  decimal: DecimalSeparator
  totalVolume: string
  supplementary: boolean
}

function totalVolume(text: string): number | null | undefined {
  return text.trim() === '' ? null : (parseNumber(text, ',') ?? undefined)
}

function documentsOf(input: BatchchecksInput): readonly BatchchecksDocument[] | BatchchecksError {
  if (input.json) return input.json
  if (!input.table || input.table.header.length === 0) return 'noData'
  const mapped = Object.entries(input.mapping).some(([name, column]) => name !== 'ref' && column !== null)
  return mapped ? batchchecksTableDocuments(input.table, input.mapping, input.catalogue.fields, input.decimal) : 'noColumns'
}

/** Anfrage für `POST /runs` aus Datei, Zuordnung und Optionen. */
export function buildBatchchecksRequest(input: BatchchecksInput): BatchchecksValidation {
  const documents = documentsOf(input)
  if (typeof documents === 'string') return { ok: false, error: documents }
  if (documents.length === 0) return { ok: false, error: 'noRows' }
  if (documents.length > input.catalogue.limits.max_documents) return { ok: false, error: 'tooMany' }
  const total = totalVolume(input.totalVolume)
  if (total === undefined) return { ok: false, error: 'totalVolume' }
  const options = total === null ? { supplementary: input.supplementary } : { supplementary: input.supplementary, total_volume: total }
  return { ok: true, request: { documents, options } }
}
