/** Alle Blätter eines Arbeitsstands in der Reihenfolge der Vorlage berechnen. */
import { cellsOf, findField, inputFields } from '../model/definition'
import { createContext, summaryOf, type AvailableSheet, type SheetModule } from '../model/sheet'
import type { CellMap, CellValue, MethodSummary, SheetId } from '../model/types'
import { SHEETS } from '../sheets/registry'
import type { WorkspaceState } from './types'

/** Blatt, dessen Kontext die Ergebnisübersicht des gewählten Methodenblatts braucht. */
const TOTAL_ERROR_RATE_SHEET = '18_GFQ_AnhIII'

/**
 * Berechnet jedes Blatt mit Rechenkern. Die Reihenfolge des Registers ist die
 * der Vorlage, sodass Verknüpfungen (Blatt 02 → Methodenblatt → Blatt 18) auf
 * bereits berechnete Blätter treffen. Listenblätter (Blatt 17) rechnet das
 * jeweilige Blattmodul selbst.
 */
export function computeWorkspace(state: WorkspaceState, sheets: readonly SheetModule[] = SHEETS): Record<SheetId, CellMap> {
  const results: Record<SheetId, CellMap> = {}
  for (const sheet of sheets) {
    const inputs = state.sheets[sheet.id]
    if (!sheet.available || sheet.definition.layout === 'list' || Array.isArray(inputs)) continue
    results[sheet.id] = sheet.compute((inputs as CellMap | undefined) ?? {}, createContext({ sheets: results, method: methodFor(sheet.id, state, results) }))
  }
  return results
}

/** Ergebnisübersicht des gewählten Methodenblatts – nur für Blatt 18. */
function methodFor(sheet: SheetId, state: WorkspaceState, results: Record<SheetId, CellMap>): MethodSummary | undefined {
  const active = state.activeMethod ? results[state.activeMethod] : undefined
  return sheet === TOTAL_ERROR_RATE_SHEET && state.activeMethod && active ? summaryOf(state.activeMethod, active) : undefined
}

/** Einheiten eines Listenblatts (Blatt 17) aus dem Arbeitsstand. */
export function listRows(state: WorkspaceState, sheet: SheetId): readonly CellMap[] {
  const inputs = state.sheets[sheet]
  return Array.isArray(inputs) ? (inputs as readonly CellMap[]) : []
}

/** Nur die berechneten Zellen eines Blatts (ohne Eingabezellen), wie sie in `ergebnisse` stehen. */
export function computedCells(sheet: AvailableSheet, results: CellMap): CellMap {
  const inputs = new Set(inputFields(sheet.definition).filter((field) => field.kind === 'input').flatMap(cellsOf))
  const computed: Record<string, CellValue> = {}
  for (const [cell, value] of Object.entries(results)) {
    if (!inputs.has(cell)) computed[cell] = value
  }
  return computed
}

/** Bezeichnung einer Zelle für Meldungen; Zellen der Ergebnisübersicht tragen ihre Adresse. */
export function labelOf(sheet: AvailableSheet, cell: string): string {
  return findField(sheet.definition, cell)?.label ?? cell
}
