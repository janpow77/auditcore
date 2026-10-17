/**
 * Strenge Prüfung einer Arbeitsstandsdatei vor jeder Verwendung: Größe,
 * gefährliche Schlüssel, Aufbau, Wertebereiche. Geprüft wird von Hand gegen
 * dieselben Regeln wie `schema/arbeitsstand.schema.json` (Test `schema.spec.ts`),
 * damit zur Laufzeit keine Schemabibliothek nötig ist.
 */
import type { CellMap, CellValue, SheetId } from '../model/types'
import { type OpenErrorCode, type SheetInputs, type WorkspaceHeader, WORKSPACE_FORMAT } from './types'

/** Abbruch beim Öffnen mit Fehlerkennung. */
export class OpenFailure extends Error {
  constructor(
    readonly code: OpenErrorCode,
    readonly detail?: string,
  ) {
    super(detail ? `${code}: ${detail}` : code)
    this.name = 'OpenFailure'
  }
}

const UNSAFE_KEYS = new Set(['__proto__', 'constructor', 'prototype'])
const SHEET_ID = /^[0-9A-Za-z_]{1,40}$/
const CELL = /^[A-Z]{1,3}[1-9][0-9]{0,3}$/
const CHECKSUM = /^sha256:[0-9a-f]{64}$/
const HEADER_KEYS = ['programm', 'cci', 'geschaeftsjahr', 'bearbeitung', 'aktenzeichen'] as const
const KNOWN_FIELDS = new Set(['format', 'formatVersion', 'rechenkern', 'vorlage', 'rechtsstand', 'gespeichertAm', 'kopf', 'aktiveMethode', 'blaetter', 'ergebnisse', 'hinweise', 'pruefsumme'])
const MAX_TEXT = 2000
const MAX_CELLS = 5000
const MAX_ROWS = 2000
const MAX_SHEETS = 100
/** Zusätzlicher Schlüssel je Zeile einer Liste (Blatt 17). */
const ROW_KEYS = new Set(['kennung'])

/** Geprüfter Inhalt einer Datei, noch ohne Abgleich mit den Methodendefinitionen. */
export interface RawWorkspace {
  formatVersion: number
  rechenkern: string | null
  gespeichertAm: string | null
  kopf: WorkspaceHeader
  aktiveMethode: SheetId | null
  blaetter: Record<SheetId, SheetInputs>
  ergebnisse: Record<SheetId, CellMap>
  /** `null`: fehlt oder hat nicht die Form `sha256:<64 Hexziffern>`. */
  pruefsumme: string | null
  /** Unbekannte Felder der Datei (werden ignoriert und gemeldet). */
  unknown: string[]
}

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

/** JSON lesen; Schlüssel, die den Prototyp verändern könnten, führen zum Abbruch. */
export function parseJson(text: string, maxSize: number): unknown {
  if (text.length > maxSize) throw new OpenFailure('too-large', String(text.length))
  try {
    return JSON.parse(text, (key, value: unknown) => {
      if (UNSAFE_KEYS.has(key)) throw new OpenFailure('unsafe-key', key)
      return value
    })
  } catch (error) {
    if (error instanceof OpenFailure) throw error
    throw new OpenFailure('invalid-json')
  }
}

function invalid(path: string): never {
  throw new OpenFailure('invalid-structure', path)
}

function cellValue(value: unknown, path: string): CellValue {
  if (value === null) return null
  if (typeof value === 'number' && Number.isFinite(value)) return value
  if (typeof value === 'string' && value.length <= MAX_TEXT) return value
  return invalid(path)
}

function cellMap(value: unknown, path: string, extraKeys: ReadonlySet<string> = new Set()): CellMap {
  if (!isRecord(value)) return invalid(path)
  const entries = Object.entries(value)
  if (entries.length > MAX_CELLS) return invalid(path)
  const cells: Record<string, CellValue> = {}
  for (const [key, entry] of entries) {
    if (!CELL.test(key) && !extraKeys.has(key)) return invalid(`${path}.${key}`)
    cells[key] = cellValue(entry, `${path}.${key}`)
  }
  return cells
}

function sheetInputs(value: unknown, path: string): SheetInputs {
  if (!Array.isArray(value)) return cellMap(value, path)
  if (value.length > MAX_ROWS) return invalid(path)
  return value.map((row, index) => cellMap(row, `${path}[${index}]`, ROW_KEYS))
}

function sheets<T>(value: unknown, path: string, read: (entry: unknown, path: string) => T): Record<SheetId, T> {
  if (value === undefined) return {}
  if (!isRecord(value) || Object.keys(value).length > MAX_SHEETS) return invalid(path)
  const result: Record<SheetId, T> = {}
  for (const [id, entry] of Object.entries(value)) {
    if (!SHEET_ID.test(id)) return invalid(`${path}.${id}`)
    result[id] = read(entry, `${path}.${id}`)
  }
  return result
}

function header(value: unknown, unknown: string[]): WorkspaceHeader {
  const kopf: WorkspaceHeader = { programm: '', cci: '', geschaeftsjahr: '', bearbeitung: '', aktenzeichen: '' }
  if (value === undefined) return kopf
  if (!isRecord(value)) return invalid('kopf')
  for (const [key, entry] of Object.entries(value)) {
    if (!(HEADER_KEYS as readonly string[]).includes(key)) unknown.push(`kopf.${key}`)
    else if (typeof entry !== 'string' || entry.length > MAX_TEXT) return invalid(`kopf.${key}`)
    else kopf[key as keyof WorkspaceHeader] = entry
  }
  return kopf
}

function optionalText(value: unknown, path: string): string | null {
  if (value === undefined || value === null) return null
  return typeof value === 'string' && value.length <= MAX_TEXT ? value : invalid(path)
}

function activeMethod(value: unknown): SheetId | null {
  if (value === undefined || value === null) return null
  return typeof value === 'string' && SHEET_ID.test(value) ? value : invalid('aktiveMethode')
}

/** Formatkennung und Fassung lesen; alles andere ist kein Arbeitsstand. */
export function formatVersionOf(raw: unknown): number {
  if (!isRecord(raw) || raw.format !== WORKSPACE_FORMAT) throw new OpenFailure('not-a-workspace')
  const version = raw.formatVersion
  if (typeof version !== 'number' || !Number.isInteger(version) || version < 1) return invalid('formatVersion')
  return version
}

/** Aufbau und Wertebereiche prüfen; unbekannte Felder der obersten Ebene werden gesammelt. */
export function validateStructure(raw: Record<string, unknown>): RawWorkspace {
  const unknown = Object.keys(raw).filter((key) => !KNOWN_FIELDS.has(key))
  const checksum = raw.pruefsumme
  return {
    formatVersion: formatVersionOf(raw),
    rechenkern: optionalText(raw.rechenkern, 'rechenkern'),
    gespeichertAm: optionalText(raw.gespeichertAm, 'gespeichertAm'),
    kopf: header(raw.kopf, unknown),
    aktiveMethode: activeMethod(raw.aktiveMethode),
    blaetter: sheets(raw.blaetter, 'blaetter', sheetInputs),
    ergebnisse: sheets(raw.ergebnisse, 'ergebnisse', (entry, path) => cellMap(entry, path)),
    pruefsumme: typeof checksum === 'string' && CHECKSUM.test(checksum) ? checksum : null,
    unknown,
  }
}
