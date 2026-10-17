/** Dateinamen: `Stichprobe_<Blatt>_<Geschäftsjahr>_Arbeitsstand.json` bzw. `_Ergebnis.xlsx`. */
import { toIsoDate } from '@auditcore/common'
import { fieldsOf } from '../model/definition'
import type { SheetModule } from '../model/sheet'
import type { CellMap } from '../model/types'
import { SHEETS, findAvailableSheet } from '../sheets/registry'
import type { WorkspaceState } from './types'

/** Geschäftsjahr aus dem Kopf, sonst aus dem Feld `accountingYear` des aktiven Blatts. */
function accountingYear(state: WorkspaceState, sheets: readonly SheetModule[]): string {
  if (state.header.geschaeftsjahr) return state.header.geschaeftsjahr
  const sheet = state.activeMethod ? findAvailableSheet(state.activeMethod, sheets) : undefined
  const cell = sheet ? fieldsOf(sheet.definition).find((field) => field.alias === 'accountingYear')?.cell : undefined
  const inputs = state.activeMethod ? state.sheets[state.activeMethod] : undefined
  const value = cell && inputs && !Array.isArray(inputs) ? (inputs as CellMap)[cell] : null
  return typeof value === 'string' ? value : ''
}

/** Vorsatz der Dateinamen, solange die Anwendung keinen eigenen vorgibt. */
export const DEFAULT_FILE_PREFIX = 'Stichprobe'

function safePart(text: string): string {
  return text.replace(/[^0-9A-Za-zÄÖÜäöüß-]+/g, '_').replace(/^_+|_+$/g, '')
}

/** Namensstamm aus Blatt und Geschäftsjahr; ohne Geschäftsjahr das Tagesdatum. */
export function fileStem(state: WorkspaceState, sheets: readonly SheetModule[] = SHEETS, now: Date = new Date(), prefix = DEFAULT_FILE_PREFIX): string {
  const period = safePart(accountingYear(state, sheets)) || (toIsoDate(now) ?? '')
  return [safePart(prefix) || DEFAULT_FILE_PREFIX, safePart(state.activeMethod ?? ''), period].filter(Boolean).join('_')
}

export function workspaceFileName(state: WorkspaceState, sheets?: readonly SheetModule[], now?: Date, prefix?: string): string {
  return `${fileStem(state, sheets, now, prefix)}_Arbeitsstand.json`
}

export function exportFileName(state: WorkspaceState, sheets?: readonly SheetModule[], now?: Date, prefix?: string): string {
  return `${fileStem(state, sheets, now, prefix)}_Ergebnis.xlsx`
}
