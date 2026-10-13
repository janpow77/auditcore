/**
 * Rechenkern Blatt 06_MUS_2Z_S: was die Abschnitte eines Laufs teilen, und
 * zwei Formeln, die in beiden Zeiträumen vorkommen.
 */
import { isBlank, required } from '../../excel/index'
import { STRATA_COLUMNS, stratumCell as at, totalRow } from '../../model/strata'
import type { CellValue, Cells, SheetContext } from '../../model/types'
import type { Pending } from '../shared/mus'
import { checkStratumUnits } from '../shared/statistical'

/**
 * Zeilen, die eine Schichtspalte belegen: Buchwerte (8, 9, 51) und die Fehler der
 * hochwertigen Einheiten (47, 81), die die Vorlage ohne Blick auf den Buchwert
 * summiert. Eine Spalte ohne diese Angaben liefert in jeder Zeile denselben Wert.
 */
const OCCUPYING_ROWS = [8, 9, 47, 51, 81]
/**
 * Eingaben, die nur Formeln der eigenen Schicht lesen, und nur, wenn die Schicht
 * belegt ist: die Standardabweichungen (24, 25, 49, 53, 83). Alle übrigen
 * Schichteingaben gehen auch ohne Buchwert in eine Summe der Spalte C ein.
 */
const OWN_ROWS = [24, 25, 49, 53, 83]
/** Spalte, die es in keinem Blatt gibt: steht für jede unbelegte Schichtspalte. */
const IDLE = 'ZZ'

/** Was die Abschnitte eines Laufs teilen: Zellen, offene Zellen (`computeTwice`), Kontext und begrenzter Umfang. */
export interface Run {
  c: Cells
  pending: Pending
  context: SheetContext
  limit: number | null
  /** Belegte Schichtspalten. */
  active: readonly string[]
}

/** Die Schichtspalte ist belegt: mindestens eine Angabe in einer der Zeilen, die eine Schicht belegen. */
const occupied = (c: Cells, column: string): boolean => OCCUPYING_ROWS.some((row) => !isBlank(c[at(column, row)]))

export function createRun(c: Cells, pending: Pending, context: SheetContext): Run {
  return { c, pending, context, limit: null, active: STRATA_COLUMNS.filter((column) => occupied(c, column)) }
}

/**
 * Schlüssel der Eingaben, die ein Ergebnis bestimmen (`remembered`): alle außer
 * den Standardabweichungen unbelegter Schichten. Die Auswertung rechnet für jede
 * dieser Zellen einmal mit 0 nach; das Ergebnis ist dasselbe wie ohne sie.
 */
export function relevantInputs(c: Cells): string {
  const idle = STRATA_COLUMNS.filter((column) => !occupied(c, column))
  if (idle.length === 0) return JSON.stringify(c)
  const relevant: Cells = { ...c }
  for (const column of idle) for (const row of OWN_ROWS) relevant[at(column, row)] = null
  return JSON.stringify(relevant)
}

/** Die Schicht hat in dieser Zeile (8, 9 oder 51) einen Buchwert. */
export function has(run: Run, column: string, row: number): boolean {
  return !isBlank(run.c[at(column, row)])
}

/**
 * Füllt eine Schichtzeile wie `fillRow`, rechnet die Formel aber nur für belegte
 * Spalten; unbelegte erhalten den Wert, den die Formel für eine leere Spalte liefert.
 */
export function fill(run: Run, row: number, formula: (column: string) => CellValue): void {
  const idle = formula(IDLE)
  for (const column of STRATA_COLUMNS) run.c[at(column, row)] = run.active.includes(column) ? formula(column) : idle
}

/**
 * Summe einer berechneten Schichtzeile: offen, solange eine ihrer Zellen offen
 * ist. Trägt keine Schicht einen Wert, zeigt die Vorlage 0 – ein Wert ohne
 * Grundlage (`totalRow`). `used`: Hilfszeile, die für unbelegte Schichten 0
 * trägt; summiert werden dann nur die Schichten mit einem Buchwert in einer
 * dieser Zeilen, damit die Nullen der unbelegten nicht als Summanden zählen.
 */
export function total(run: Run, row: number, used?: readonly number[]): CellValue {
  if (run.active.some((column) => run.pending(at(column, row)))) return null
  const columns = used ? run.active.filter((column) => used.some((entry) => has(run, column, entry))) : STRATA_COLUMNS
  return totalRow(run.c, row, run.context, columns)
}

/** Summen eingegebener Schichtzeilen (`SUM(D<zeile>:J<zeile>)`); ohne jeden Wert bleibt die Summe offen statt 0. */
export function inputTotals(run: Run, rows: readonly number[]): void {
  for (const row of rows) run.c[`C${row}`] = totalRow(run.c, row, run.context)
}

/** `BV · σ²`, wenn die Schicht in der Zeile `bookValue` belegt ist, sonst 0 (`N(D8)*N(D24)^2`). */
export function varianceTerm(run: Run, column: string, bookValue: number, deviation: number): number {
  return has(run, column, bookValue) ? required(run.c[at(column, bookValue)]) * required(run.c[at(column, deviation)]) ** 2 : 0
}

/**
 * Prüfhinweis je Schicht „mindestens drei Einheiten“ (`IF(D8="";"";IF(D44>=3;…))`)
 * für die Schichten mit einem Buchwert in der Zeile `used`. Zeigt die Vorlage für
 * die Einheiten der Zufallsschicht nichts (etwa bei TE ≤ AE oder nicht anwendbarer
 * Standardneuberechnung), lautet ihr Hinweis trotzdem „✔ ≥ 3“ – ein Prüfhinweis
 * ohne Grundlage (`checkStratumUnits`). Fehlt dagegen eine Angabe, bleibt er offen.
 */
export function checkUnits(run: Run, column: string, used: number, units: number): CellValue {
  const cell = at(column, units)
  return has(run, column, used) ? checkStratumUnits(run.c[cell], run.pending(cell), run.context) : null
}
