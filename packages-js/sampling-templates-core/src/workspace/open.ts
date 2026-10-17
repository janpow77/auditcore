/**
 * Arbeitsstandsdatei öffnen: prüfen, anheben, mit den Methodendefinitionen
 * abgleichen und immer neu rechnen. Abweichungen werden als Hinweise gemeldet.
 */
import { isBlank, isNumber } from '../excel/index'
import { fieldOptions } from '../format/numbers'
import { cellsOf, inputFields, type FieldDefinition } from '../model/definition'
import { createContext, type AvailableSheet, type SheetModule } from '../model/sheet'
import type { CellMap, CellValue, Parameters, SheetId } from '../model/types'
import { SHEETS, findSheet } from '../sheets/registry'
import { canonicalInputs, checksumOf } from './canonical'
import { computeWorkspace, labelOf } from './compute'
import { MIGRATIONS, migrate, type Migrations } from './migrate'
import {
  ENGINE_VERSION,
  MAX_WORKSPACE_SIZE,
  WORKSPACE_FORMAT_VERSION,
  type OpenNotice,
  type OpenResult,
  type ResultDifference,
  type SheetInputs,
  type WorkspaceState,
} from './types'
import { OpenFailure, formatVersionOf, isRecord, parseJson, validateStructure, type RawWorkspace } from './validate'

export interface OpenOptions {
  sheets?: readonly SheetModule[]
  /** Größte zulässige Datei in Zeichen. */
  maxSize?: number
  migrations?: Migrations
  /** Aktuelle Fassung des Formats (nur für Tests des Migrationsgerüsts). */
  currentVersion?: number
}

const TOLERANCE = 1e-9

function sameResult(stored: CellValue, computed: CellValue): boolean {
  if (isNumber(stored) && isNumber(computed)) return Math.abs(stored - computed) <= TOLERANCE * Math.max(1, Math.abs(stored))
  return (isBlank(stored) ? null : stored) === (isBlank(computed) ? null : computed)
}

/** Passt der Wert zum Feld? Zahlenfelder nehmen nur Zahlen, Auswahlfelder nur Einträge ihrer Liste. */
function accepts(field: FieldDefinition, value: CellValue, parameters: Parameters): boolean {
  if (value === null) return true
  if (field.list || field.options) return fieldOptions(field, parameters).some((option) => option.value === value)
  return field.type === 'text' ? typeof value === 'string' : isNumber(value)
}

/** Eingabezellen eines Blatts mit ihrem Feld (Schichtzeilen aufgelöst). */
function inputMap(sheet: AvailableSheet): Map<string, FieldDefinition> {
  return new Map(inputFields(sheet.definition).flatMap((field) => cellsOf(field).map((cell) => [cell, field] as const)))
}

function sanitizeCells(fields: Map<string, FieldDefinition>, inputs: CellMap, parameters: Parameters, path: string, unknown: string[]): CellMap {
  const cells: Record<string, CellValue> = {}
  for (const [cell, value] of Object.entries(inputs)) {
    const field = fields.get(cell)
    if (field && accepts(field, value, parameters)) cells[cell] = value
    else unknown.push(`${path}.${cell}`)
  }
  return cells
}

/**
 * Eingaben eines Blatts auf die Eingabezellen der Definition beschränken; alles
 * andere wird gemeldet. Listenblätter tragen je Einheit einen Satz Zellen.
 */
function sanitize(sheet: AvailableSheet, inputs: SheetInputs, parameters: Parameters, unknown: string[]): SheetInputs {
  const fields = inputMap(sheet)
  const path = `blaetter.${sheet.id}`
  const isList = sheet.definition.layout === 'list'
  if (Array.isArray(inputs) !== isList) {
    unknown.push(path)
    return isList ? [] : {}
  }
  if (!isList) return sanitizeCells(fields, inputs as CellMap, parameters, path, unknown)
  return (inputs as readonly CellMap[]).map((row, index) => sanitizeCells(fields, row, parameters, `${path}[${index}]`, unknown))
}

function toState(raw: RawWorkspace, sheets: readonly SheetModule[], unknown: string[]): WorkspaceState {
  const parameters = createContext().parameters
  const inputs: Record<SheetId, SheetInputs> = {}
  for (const [id, entry] of Object.entries(raw.blaetter)) {
    const sheet = findSheet(id, sheets)
    if (!sheet) unknown.push(`blaetter.${id}`)
    else inputs[id] = sheet.available ? sanitize(sheet, entry, parameters, unknown) : entry
  }
  const known = raw.aktiveMethode !== null && findSheet(raw.aktiveMethode, sheets) !== undefined
  if (raw.aktiveMethode !== null && !known) unknown.push('aktiveMethode')
  return { header: raw.kopf, activeMethod: known ? raw.aktiveMethode : null, sheets: inputs }
}

function differences(raw: RawWorkspace, state: WorkspaceState, sheets: readonly SheetModule[]): ResultDifference[] {
  const computed = computeWorkspace(state, sheets)
  const found: ResultDifference[] = []
  for (const [id, stored] of Object.entries(raw.ergebnisse)) {
    const sheet = findSheet(id, sheets)
    const current = computed[id]
    if (!sheet?.available || !current) continue
    for (const [cell, value] of Object.entries(stored)) {
      const now = current[cell] ?? null
      if (!sameResult(value, now)) found.push({ sheet: id, cell, label: labelOf(sheet, cell), stored: value, computed: now })
    }
  }
  return found
}

/** Datei lesen, Fassung prüfen und auf die aktuelle Fassung anheben. */
function load(text: string, options: OpenOptions, notices: OpenNotice[]): RawWorkspace {
  const current = options.currentVersion ?? WORKSPACE_FORMAT_VERSION
  const parsed = parseJson(text, options.maxSize ?? MAX_WORKSPACE_SIZE)
  const version = formatVersionOf(parsed)
  if (version > current) throw new OpenFailure('newer-version', String(version))
  const lifted = migrate(parsed as Record<string, unknown>, version, current, options.migrations ?? MIGRATIONS)
  if (!isRecord(lifted)) throw new OpenFailure('invalid-structure')
  if (version < current) notices.push({ kind: 'migrated', from: version, to: current })
  return validateStructure(lifted)
}

async function read(text: string, options: OpenOptions): Promise<OpenResult> {
  const sheets = options.sheets ?? SHEETS
  const notices: OpenNotice[] = []
  const raw = load(text, options, notices)
  const unknown = [...raw.unknown]
  const state = toState(raw, sheets, unknown)
  if (unknown.length) notices.push({ kind: 'unknown-fields', fields: unknown })
  const intact = raw.pruefsumme !== null && raw.pruefsumme === (await checksumOf(canonicalInputs(raw)))
  if (!intact) notices.push({ kind: 'checksum-mismatch' })
  const changed = intact ? differences(raw, state, sheets) : []
  if (changed.length) notices.push({ kind: 'results-differ', differences: changed, storedEngine: raw.rechenkern ?? '?', currentEngine: ENGINE_VERSION })
  return { ok: true, state, savedAt: raw.gespeichertAm, engine: raw.rechenkern, notices }
}

/**
 * Öffnet den Text einer Arbeitsstandsdatei. Ältere Fassungen werden angehoben,
 * neuere abgelehnt; unbekannte Felder werden ignoriert und gemeldet; weicht
 * die Prüfsumme ab, ist die Datei außerhalb der Anwendung verändert worden.
 */
export async function openWorkspace(text: string, options: OpenOptions = {}): Promise<OpenResult> {
  try {
    return await read(text, options)
  } catch (error) {
    if (error instanceof OpenFailure) return { ok: false, error: { code: error.code, detail: error.detail } }
    throw error
  }
}
