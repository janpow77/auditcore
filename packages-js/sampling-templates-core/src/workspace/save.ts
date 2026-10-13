/** Arbeitsstand als Datei schreiben. */
import { isBlank } from '../excel/index'
import { createTranslate, type Translate } from '../i18n/messages'
import { createContext, type SheetModule } from '../model/sheet'
import type { CellMap, CellValue, SheetId } from '../model/types'
import { SHEETS } from '../sheets/registry'
import { buildHints } from '../view/summaryView'
import { canonicalInputs, checksumOf } from './canonical'
import { computeWorkspace, computedCells } from './compute'
import { workspaceFileName } from './filenames'
import {
  ENGINE_VERSION,
  LEGAL_STATE,
  TEMPLATE_NAME,
  WORKSPACE_FORMAT,
  WORKSPACE_FORMAT_VERSION,
  type SheetInputs,
  type WorkspaceFile,
  type WorkspaceState,
} from './types'

export interface SaveOptions {
  /** Zeitpunkt des Speicherns (Standard: jetzt). */
  now?: Date
  sheets?: readonly SheetModule[]
  /** Texte der gespeicherten Hinweise (Standard: deutsch). */
  t?: Translate
  /** Vorsatz des vorgeschlagenen Dateinamens (Standard: „Stichprobe“). */
  filePrefix?: string
}

/** Geschriebene Datei mit Text und vorgeschlagenem Namen. */
export interface SavedWorkspace {
  file: WorkspaceFile
  text: string
  fileName: string
}

function withoutBlanks(cells: CellMap): CellMap {
  const result: Record<string, CellValue> = {}
  for (const [cell, value] of Object.entries(cells)) {
    if (!isBlank(value)) result[cell] = value
  }
  return result
}

/** Eingaben ohne leere Werte; leere Blätter entfallen. */
export function cleanInputs(sheets: WorkspaceState['sheets']): Record<SheetId, SheetInputs> {
  const result: Record<SheetId, SheetInputs> = {}
  for (const [id, inputs] of Object.entries(sheets)) {
    const cleaned = Array.isArray(inputs) ? (inputs as readonly CellMap[]).map(withoutBlanks) : withoutBlanks(inputs as CellMap)
    if (Array.isArray(cleaned) ? cleaned.length > 0 : Object.keys(cleaned).length > 0) result[id] = cleaned
  }
  return result
}

/** Gespeicherte Ergebnisse und Hinweise der Webfassung je bearbeitetem Blatt mit Rechenkern. */
function stored(state: WorkspaceState, sheets: readonly SheetModule[], t: Translate): Pick<WorkspaceFile, 'ergebnisse' | 'hinweise'> {
  const results = computeWorkspace(state, sheets)
  const ergebnisse: WorkspaceFile['ergebnisse'] = {}
  const hinweise: WorkspaceFile['hinweise'] = {}
  for (const sheet of sheets) {
    const computed = results[sheet.id]
    if (!sheet.available || !computed || !(state.sheets[sheet.id] || sheet.id === state.activeMethod)) continue
    ergebnisse[sheet.id] = computedCells(sheet, computed)
    const web = buildHints(sheet, (state.sheets[sheet.id] as CellMap | undefined) ?? {}, computed, createContext({ sheets: results }), t).filter((hint) => hint.source === 'web')
    if (web.length) hinweise[sheet.id] = web.map((hint) => ({ id: hint.id, text: hint.text }))
  }
  return { ergebnisse, hinweise }
}

/** Arbeitsstandsdatei mit Prüfsumme über die kanonisch sortierten Eingaben erzeugen. */
export async function saveWorkspace(state: WorkspaceState, options: SaveOptions = {}): Promise<SavedWorkspace> {
  const sheets = options.sheets ?? SHEETS
  const now = options.now ?? new Date()
  const inputs = { kopf: { ...state.header }, aktiveMethode: state.activeMethod, blaetter: cleanInputs(state.sheets) }
  const file: WorkspaceFile = {
    format: WORKSPACE_FORMAT,
    formatVersion: WORKSPACE_FORMAT_VERSION,
    rechenkern: ENGINE_VERSION,
    vorlage: TEMPLATE_NAME,
    rechtsstand: LEGAL_STATE,
    gespeichertAm: now.toISOString(),
    ...inputs,
    ...stored(state, sheets, options.t ?? createTranslate()),
    pruefsumme: await checksumOf(canonicalInputs(inputs)),
  }
  return { file, text: `${JSON.stringify(file, null, 2)}\n`, fileName: workspaceFileName(state, sheets, now, options.filePrefix) }
}
