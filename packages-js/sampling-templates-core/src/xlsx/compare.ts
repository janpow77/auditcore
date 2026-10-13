/**
 * Gegenprobe nach dem Import der ausgefüllten Vorlage: Die Mappe enthält die
 * zuletzt berechneten Werte ihrer Formelzellen. Weicht ein Ergebnis der
 * Webfassung davon ab, wird das vor der Übernahme gemeldet.
 */
import { isBlank, isNumber } from '../excel/index'
import { findField } from '../model/definition'
import type { AvailableSheet, SheetModule } from '../model/sheet'
import type { CellAddress, CellMap, CellValue, SheetId } from '../model/types'
import { SHEETS, findAvailableSheet } from '../sheets/registry'
import { computeWorkspace } from '../workspace/compute'
import type { WorkspaceState } from '../workspace/types'

/** Ergebnis der Mappe und der Webfassung, die nicht übereinstimmen. */
export interface ImportDifference {
  sheet: SheetId
  cell: CellAddress
  label: string
  /** Wert laut Mappe. */
  workbook: CellValue
  /** Wert der Webfassung; `null`: kein Wert („Angabe fehlt“). */
  computed: CellValue
}

const TOLERANCE = 1e-9

function same(workbook: CellValue, computed: CellValue): boolean {
  if (isNumber(workbook) && isNumber(computed)) return Math.abs(workbook - computed) <= TOLERANCE * Math.max(1, Math.abs(workbook))
  return (isBlank(workbook) ? null : workbook) === (isBlank(computed) ? null : computed)
}

/** Abweichungen eines Blatts; ohne Rechenwert in der Mappe (leere Zelle, nie berechnete Datei) gibt es nichts zu vergleichen. */
function sheetDifferences(sheet: AvailableSheet, cells: CellMap, computed: CellMap): ImportDifference[] {
  return Object.entries(cells)
    .filter(([cell, value]) => !isBlank(value) && !same(value, computed[cell] ?? null))
    .map(([cell, value]) => ({ sheet: sheet.id, cell, label: findField(sheet.definition, cell)?.label ?? cell, workbook: value, computed: computed[cell] ?? null }))
}

/** Ergebnisse der Webfassung für den importierten Arbeitsstand mit den Rechenwerten der Mappe vergleichen. */
export function compareWithWorkbook(state: WorkspaceState, cached: Readonly<Record<SheetId, CellMap>>, sheets: readonly SheetModule[] = SHEETS): ImportDifference[] {
  const results = computeWorkspace(state, sheets)
  return Object.entries(cached).flatMap(([id, cells]) => {
    const sheet = findAvailableSheet(id, sheets)
    const computed = results[id]
    return sheet && computed ? sheetDifferences(sheet, cells, computed) : []
  })
}
