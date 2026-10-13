/** Alle Blätter eines Arbeitsstands in der Reihenfolge der Vorlage berechnen. */
import { cellsOf, findField, inputFields } from '../model/definition'
import { evaluateSheet } from '../model/evaluate'
import { createContext, summaryOf, type AvailableSheet, type SheetModule } from '../model/sheet'
import type { CellMap, CellValue, MethodSummary, MissingPolicy, SheetContext, SheetId } from '../model/types'
import { SHEETS } from '../sheets/registry'
import type { WorkspaceState } from './types'

/** Blätter, deren Kontext die Ergebnisübersicht des gewählten Methodenblatts braucht: Gesamtfehlerquote und Bericht. */
const METHOD_READERS: readonly SheetId[] = ['18_GFQ_AnhIII', '20_Druck_KOM']

/**
 * Berechnet jedes Blatt mit Rechenkern. Die Reihenfolge des Registers ist die
 * der Vorlage, sodass Verknüpfungen (Blatt 02 → Methodenblatt → Blatt 18) auf
 * bereits berechnete Blätter treffen. Listenblätter (Blatt 17) rechnet das
 * jeweilige Blattmodul selbst. Fehlende Angaben behandelt `evaluateSheet` nach
 * der Richtlinie (`model/policy.ts`); `policy` ersetzt sie für Vergleiche.
 */
export function computeWorkspace(state: WorkspaceState, sheets: readonly SheetModule[] = SHEETS, policy?: MissingPolicy): Record<SheetId, CellMap> {
  const results: Record<SheetId, CellMap> = {}
  for (const sheet of sheets) {
    const inputs = state.sheets[sheet.id]
    if (!sheet.available || sheet.definition.layout === 'list' || Array.isArray(inputs)) continue
    results[sheet.id] = evaluateSheet(sheet, (inputs as CellMap | undefined) ?? {}, contextFor(sheet.id, state, results, policy), false).cells
  }
  return results
}

/**
 * Kontext, in dem ein Blatt des Arbeitsstands gerechnet wird: Ergebnisse der
 * anderen Blätter und – für Blatt 18 – die Ergebnisübersicht des gewählten
 * Methodenblatts. Anzeige und Export verwenden denselben Kontext wie die Rechnung.
 */
export function contextFor(sheet: SheetId, state: WorkspaceState, results: Readonly<Record<SheetId, CellMap>>, policy?: MissingPolicy): SheetContext {
  return createContext({ sheets: results, method: methodFor(sheet, state, results), policy })
}

/** Ergebnisübersicht des gewählten Methodenblatts – nur für die Blätter 18 und 20. */
function methodFor(sheet: SheetId, state: WorkspaceState, results: Readonly<Record<SheetId, CellMap>>): MethodSummary | undefined {
  const active = state.activeMethod ? results[state.activeMethod] : undefined
  return METHOD_READERS.includes(sheet) && state.activeMethod && active ? summaryOf(state.activeMethod, active) : undefined
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
