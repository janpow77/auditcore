/**
 * Schichtspalten geschichteter Blätter. Die Vorlage sieht sieben Spalten vor
 * (D–I „Schicht 1–6“, J „Schicht k“). Die Webfassung erlaubt bis zu 20
 * Schichten: Die 8. bis 20. Schicht liegt in den Spalten AA–AM, die in keinem
 * Blatt der Vorlage belegt sind. Das ist ein Hinweis der Webfassung, keine
 * Eigenschaft der Vorlage (docs/schichten-und-listen.md).
 */
import { count, sum } from '../excel/index'
import { unfounded } from './policy'
import type { CellAddress, CellValue, Cells, SheetContext } from './types'

/** Schichtspalten der Vorlage. */
export const TEMPLATE_STRATA: readonly string[] = ['D', 'E', 'F', 'G', 'H', 'I', 'J']
/** Zusätzliche Schichtspalten der Webfassung (8. bis 20. Schicht). */
export const EXTRA_STRATA: readonly string[] = ['AA', 'AB', 'AC', 'AD', 'AE', 'AF', 'AG', 'AH', 'AI', 'AJ', 'AK', 'AL', 'AM']
/** Alle Schichtspalten in der Reihenfolge der Schichten. */
export const STRATA_COLUMNS: readonly string[] = [...TEMPLATE_STRATA, ...EXTRA_STRATA]
/** Höchstzahl der Schichten in der Webfassung. */
export const MAX_STRATA = STRATA_COLUMNS.length

/** Zelle einer Schicht in einer Zeile (`stratumCell('D', 9)` → `D9`). */
export function stratumCell(column: string, row: number | string): CellAddress {
  return `${column}${row}`
}

/** Werte einer Schichtzeile über alle Schichtspalten. */
export function rowValues(cells: Readonly<Record<CellAddress, CellValue | undefined>>, row: number, columns: readonly string[] = STRATA_COLUMNS): CellValue[] {
  return columns.map((column) => cells[stratumCell(column, row)] ?? null)
}

/** `SUMME(D<zeile>:J<zeile>)`, in der Webfassung über alle Schichtspalten. */
export function sumRow(cells: Readonly<Record<CellAddress, CellValue | undefined>>, row: number): number {
  return sum(rowValues(cells, row))
}

/**
 * Summe einer Schichtzeile als angezeigter Wert: `SUMME(D<zeile>:J<zeile>)`,
 * solange mindestens eine Schicht einen Wert trägt. Trägt keine einen, zeigt die
 * Vorlage 0 – ein Wert ohne Grundlage (`unfounded`), den die Webfassung nach
 * der geltenden Richtlinie offen lässt. Die Zelle gehört dann mit
 * `kind: 'withoutBasis'` in die Abweichungen des Blatts.
 */
export function totalRow(cells: Readonly<Record<CellAddress, CellValue | undefined>>, row: number, context: Pick<SheetContext, 'policy'> | undefined, columns: readonly string[] = STRATA_COLUMNS): CellValue {
  const values = rowValues(cells, row, columns)
  return count(values) > 0 ? sum(values) : unfounded(context, 0)
}

/** `ANZAHL(D<zeile>:J<zeile>)`, in der Webfassung über alle Schichtspalten. */
export function countRow(cells: Readonly<Record<CellAddress, CellValue | undefined>>, row: number): number {
  return count(rowValues(cells, row))
}

/** Füllt eine Schichtzeile: je Schichtspalte ein Wert aus `formula(spalte)`. */
export function fillRow(cells: Cells, row: number, formula: (column: string) => CellValue): void {
  for (const column of STRATA_COLUMNS) cells[stratumCell(column, row)] = formula(column)
}

/**
 * Anzahl der belegten Schichten: höchste Schicht mit einem Wert in einer der
 * Zeilen. `columns` sind die Schichtspalten des Blatts (`strataColumnsOf`); die
 * Altvorlage X3 führt sie in E–K statt D–J.
 */
export function usedStrata(cells: Readonly<Record<CellAddress, CellValue | undefined>>, rows: readonly (number | string)[], columns: readonly string[] = STRATA_COLUMNS): number {
  for (let index = columns.length - 1; index >= 0; index -= 1) {
    const column = columns[index]!
    if (rows.some((row) => cells[stratumCell(column, row)] !== null && cells[stratumCell(column, row)] !== undefined && cells[stratumCell(column, row)] !== '')) return index + 1
  }
  return 0
}
