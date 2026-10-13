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
  const incomplete = new Set<SheetId>()
  // Welche Blätter nicht vollständig ausgefüllt sind, reist mit den Ergebnissen (für `contextFor`), ohne als Blatt zu zählen.
  const results: Record<SheetId, CellMap> = { [INCOMPLETE]: incomplete } as Record<SheetId, CellMap>
  for (const sheet of sheets) {
    const inputs = state.sheets[sheet.id]
    if (!sheet.available || sheet.definition.layout === 'list' || Array.isArray(inputs)) continue
    const evaluation = evaluateSheet(sheet, (inputs as CellMap | undefined) ?? {}, contextFor(sheet.id, state, results, policy), false)
    results[sheet.id] = evaluation.cells
    if (!evaluation.complete) incomplete.add(sheet.id)
  }
  return results
}

/** Schlüssel, unter dem `computeWorkspace` die nicht vollständig ausgefüllten Blätter an die Ergebnisse hängt. */
const INCOMPLETE = Symbol('incomplete')
type IncompleteCarrier = { [INCOMPLETE]?: ReadonlySet<SheetId> }
const ACTIVE_METHOD = '<aktives Verfahren>'
/** Blätter, aus denen ein Blatt Werte bezieht: Fehlt dort eine Pflichteingabe, ist auch das beziehende Blatt nicht vollständig. */
const SOURCES: Readonly<Record<SheetId, readonly string[]>> = {
  '18_GFQ_AnhIII': ['02_Grundgesamtheit', ACTIVE_METHOD],
  '20_Druck_KOM': ['02_Grundgesamtheit', ACTIVE_METHOD, '18_GFQ_AnhIII'],
}

/**
 * Kontext, in dem ein Blatt des Arbeitsstands gerechnet wird: Ergebnisse der
 * anderen Blätter und – für Blatt 18 – die Ergebnisübersicht des gewählten
 * Methodenblatts. Anzeige und Export verwenden denselben Kontext wie die Rechnung.
 */
export function contextFor(sheet: SheetId, state: WorkspaceState, results: Readonly<Record<SheetId, CellMap>>, policy?: MissingPolicy): SheetContext {
  const sources = SOURCES[sheet]?.map((source) => (source === ACTIVE_METHOD ? state.activeMethod : source)) ?? []
  const incomplete = (results as IncompleteCarrier)[INCOMPLETE]
  const sourceIncomplete = sources.some((source) => source !== null && incomplete?.has(source) === true)
  return createContext({ sheets: results, method: methodFor(sheet, state, results), policy, ...(sourceIncomplete ? { sourceIncomplete } : {}) })
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
