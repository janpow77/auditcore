/**
 * Listenblätter (Blatt 17): viele Stichprobeneinheiten, je Einheit ein Satz
 * Zellwerte. Einfügen aus Zwischenablage oder CSV und Übernahme der Summen in
 * die gekennzeichneten Felder eines Methodenblatts.
 */
import { parseTable } from '@auditcore/common'
import { isBlank } from '../excel/index'
import { parseFieldInput } from '../format/numbers'
import { cellsOf, defaultInputs, fieldsOf, inputFields, type FieldDefinition, type MethodDefinition } from './definition'
import type { AvailableSheet, SubsampleNeeds, SubsampleTotals } from './sheet'
import type { CellAddress, CellMap, CellValue } from './types'

/** Höchstzahl der Einheiten einer Liste (wie in der Prüfung der Arbeitsstandsdatei). */
export const MAX_LIST_ROWS = 2000

/** Spalten beim Einfügen ohne Kopfzeile: die Eingabezellen der Vorlage in Blattreihenfolge. */
export function pasteColumns(definition: MethodDefinition): FieldDefinition[] {
  return inputFields(definition).filter((field) => !field.web)
}

export interface PastedRows {
  rows: CellMap[]
  /** Zellen, die nicht gelesen werden konnten (mehrdeutig oder ungültig) und leer bleiben. */
  rejected: number
  /** Zeilen jenseits der Höchstzahl, die nicht übernommen wurden. */
  dropped: number
}

/** Kopfzeile aus Zelladressen (`C5;C6;C11`)? Dann bestimmt sie die Spalten. */
function headerFields(first: readonly string[], fields: readonly FieldDefinition[]): (FieldDefinition | undefined)[] | null {
  const byCell = new Map(fields.map((field) => [field.cell, field]))
  const cells = first.map((cell) => cell.trim().toUpperCase())
  return cells.length > 0 && cells.every((cell) => byCell.has(cell)) ? cells.map((cell) => byCell.get(cell)) : null
}

/**
 * Liest eingefügten Text (Tabulator, Semikolon oder Komma als Trenner) als
 * Liste von Einheiten. Zahlen in deutscher Schreibweise; Prozentfelder in Prozent.
 */
export function parsePastedRows(text: string, definition: MethodDefinition, limit: number = MAX_LIST_ROWS): PastedRows {
  const table = parseTable(text.replace(/\r\n?/g, '\n').trim(), false)
  const fields = pasteColumns(definition)
  const header = table.rows[0] ? headerFields(table.rows[0], inputFields(definition)) : null
  const columns = header ?? fields
  const lines = (header ? table.rows.slice(1) : table.rows).filter((line) => line.some((cell) => cell.trim() !== ''))
  let rejected = 0
  const rows = lines.slice(0, limit).map((line) => {
    const row: Record<CellAddress, CellValue> = { ...defaultInputs(definition) }
    line.forEach((cell, index) => {
      const field = columns[index]
      if (!field) return
      const result = parseFieldInput(field, cell)
      if (!result.ok) rejected += 1
      else if (result.value !== null) row[field.cell] = result.value
    })
    return row
  })
  return { rows, rejected, dropped: Math.max(0, lines.length - limit) }
}

/** Felder eines Methodenblatts, die eine Summe aus den Unterstichproben aufnehmen. */
export function subsampleTargets(definition: MethodDefinition): FieldDefinition[] {
  return fieldsOf(definition).filter((field) => field.subsample !== undefined && (field.kind === 'input' || field.kind === 'link'))
}

/** Unterscheidet das Methodenblatt die Summen nach Schicht (Schichtzeile) bzw. nach Zeitraum (`period`)? */
export function subsampleNeeds(definition: MethodDefinition): SubsampleNeeds {
  const targets = subsampleTargets(definition)
  return { stratum: targets.some((field) => field.columns !== undefined), period: targets.some((field) => field.period !== undefined) }
}

/** Zielzellen eines Felds mit ihren Werten: bei Schichtzeilen je Schicht eine Zelle, sonst die Zelle des Felds. */
function targetValues(field: FieldDefinition, totals: SubsampleTotals): [CellAddress, CellValue][] {
  const role = field.subsample
  if (!role) return []
  const groups = totals.groups
  if (!groups) return [[field.cell, totals[role]]]
  const period = field.period ?? null
  const matching = groups.filter((group) => group.period === period)
  if (!field.columns) return [[field.cell, sumOf(matching.map((group) => group[role]))]]
  const cells = cellsOf(field)
  return matching.flatMap((group): [CellAddress, CellValue][] => {
    const cell = group.stratum === null ? undefined : cells[group.stratum - 1]
    return cell ? [[cell, group[role]]] : []
  })
}

/** Summe über Gruppen; `null`, solange keine Gruppe beiträgt. */
function sumOf(values: readonly (number | null)[]): number | null {
  const present = values.filter((value): value is number => value !== null)
  return present.length ? present.reduce((total, value) => total + value, 0) : null
}

/**
 * Summen der Unterstichproben in die gekennzeichneten Felder eines
 * Methodenblatts schreiben – bei geschichteten Verfahren je Schicht, bei
 * mehreren Zeiträumen je Zeitraum (`totals.groups`). Summen ohne Beitrag
 * (`null`) lassen die Zelle unverändert.
 */
export function applySubsamples(method: AvailableSheet, inputs: CellMap, totals: SubsampleTotals): { inputs: CellMap; applied: readonly FieldDefinition[]; cells: readonly CellAddress[] } {
  const next: Record<CellAddress, CellValue> = { ...inputs }
  const applied: FieldDefinition[] = []
  const cells: CellAddress[] = []
  for (const field of subsampleTargets(method.definition)) {
    const written = targetValues(field, totals).filter(([, value]) => !isBlank(value))
    for (const [cell, value] of written) {
      next[cell] = value
      cells.push(cell)
    }
    if (written.length) applied.push(field)
  }
  return { inputs: next, applied, cells }
}
