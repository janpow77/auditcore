/**
 * Gegenprobe nach dem Import der ausgefüllten Vorlage: Die Mappe enthält die
 * zuletzt berechneten Werte ihrer Formelzellen. Verglichen wird jedes Blatt,
 * dessen Rechenwerte übergeben werden – auch Blätter ohne eigene Eingaben
 * (Blatt 18, Bericht) – in beide Richtungen: ein anderer Wert, ein Wert der
 * Mappe, wo die Webfassung keinen zeigt, und ein Wert der Webfassung, wo die
 * Mappe leer ist.
 */
import { isBlank, isNumber } from '../excel/index'
import { defaultInputs, findField } from '../model/definition'
import { isEmptyReference, type AvailableSheet, type SheetModule } from '../model/sheet'
import type { CellAddress, CellMap, CellValue, SheetId } from '../model/types'
import { SHEETS, findAvailableSheet } from '../sheets/registry'
import { computeWorkspace } from '../workspace/compute'
import type { WorkspaceState } from '../workspace/types'

/**
 * Art des Unterschieds: `value` – beide zeigen einen Wert, aber nicht denselben;
 * `webOpen` – die Mappe zeigt einen Wert, die Webfassung keinen; `workbookEmpty` –
 * die Webfassung zeigt einen Wert, die Mappe ist leer.
 */
export type ImportDifferenceKind = 'value' | 'webOpen' | 'workbookEmpty'

/** Ergebnis der Mappe und der Webfassung, die nicht übereinstimmen. */
export interface ImportDifference {
  sheet: SheetId
  cell: CellAddress
  label: string
  /** Wert laut Mappe; `null`: leer. */
  workbook: CellValue
  /** Wert der Webfassung; `null`: kein Wert („Angabe fehlt“). */
  computed: CellValue
  kind: ImportDifferenceKind
  /**
   * Begründeter Unterschied: Die Webfassung zeigt keinen Wert, weil eine Angabe
   * fehlt, während die Vorlage mit 0 weiterrechnet oder einen Wert ohne
   * Grundlage zeigt (begründete Abweichung des Blatts). Kein Rechenunterschied.
   */
  explained: boolean
}

const TOLERANCE = 1e-9

function same(workbook: CellValue, computed: CellValue): boolean {
  if (isNumber(workbook) && isNumber(computed)) return Math.abs(workbook - computed) <= TOLERANCE * Math.max(1, Math.abs(workbook))
  return (isBlank(workbook) ? null : workbook) === (isBlank(computed) ? null : computed)
}

function kindOf(workbook: CellValue, computed: CellValue): ImportDifferenceKind {
  if (isBlank(workbook)) return 'workbookEmpty'
  return isBlank(computed) ? 'webOpen' : 'value'
}

/** Arbeitsstand, in dem jedes verglichene Blatt ohne eigene Eingaben die Vorgaben der Vorlage trägt – wie nach der Übernahme in die Oberfläche. */
function withDefaults(state: WorkspaceState, ids: readonly SheetId[], sheets: readonly SheetModule[]): WorkspaceState {
  const filled = { ...state.sheets }
  for (const id of ids) {
    const sheet = findAvailableSheet(id, sheets)
    if (sheet && !(id in filled) && sheet.definition.layout !== 'list') filled[id] = defaultInputs(sheet.definition)
  }
  return { ...state, sheets: filled }
}

/**
 * Unterschiede eines Blatts. Hat die Mappe für das Blatt keinen einzigen
 * Rechenwert (nie berechnete Datei), gibt es nichts zu vergleichen. Zellen, die
 * die Webfassung bewusst anders bildet (`adapted`), bleiben außen vor.
 */
function sheetDifferences(sheet: AvailableSheet, cells: CellMap, computed: CellMap, results: Readonly<Record<SheetId, CellMap>>): ImportDifference[] {
  if (Object.values(cells).every((value) => isBlank(value))) return []
  const adapted = new Set(sheet.adapted?.map((entry) => entry.cell))
  // Offene Zelle mit begründeter Abweichung: Eine der dort genannten Eingaben ist leer.
  const justified = (cell: CellAddress): boolean => sheet.deviations.some((entry) => entry.cell === cell && entry.whenEmpty.some((reference) => isEmptyReference(reference, computed, results)))
  return Object.entries(cells)
    .filter(([cell, value]) => !adapted.has(cell) && !same(value, computed[cell] ?? null))
    .map(([cell, value]) => {
      const shown = computed[cell] ?? null
      const kind = kindOf(value, shown)
      return { sheet: sheet.id, cell, label: findField(sheet.definition, cell)?.label ?? cell, workbook: isBlank(value) ? null : value, computed: shown, kind, explained: kind === 'webOpen' && justified(cell) }
    })
}

/**
 * Ergebnisse der Webfassung für den importierten Arbeitsstand mit den
 * Rechenwerten der Mappe vergleichen; `cached` nennt je Blatt die Rechenwerte
 * der Mappe (leere Formelzellen als `null`). Listenblätter werden nicht verglichen.
 */
export function compareWithWorkbook(state: WorkspaceState, cached: Readonly<Record<SheetId, CellMap>>, sheets: readonly SheetModule[] = SHEETS): ImportDifference[] {
  const full = withDefaults(state, Object.keys(cached), sheets)
  const results = computeWorkspace(full, sheets)
  return Object.entries(cached).flatMap(([id, cells]) => {
    const sheet = findAvailableSheet(id, sheets)
    const computed = results[id]
    if (!sheet || !computed || sheet.definition.layout === 'list') return []
    return sheetDifferences(sheet, cells, computed, results)
  })
}
