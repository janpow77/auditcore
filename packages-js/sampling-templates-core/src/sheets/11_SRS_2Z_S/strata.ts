/**
 * Bausteine der Schichtzeilen von Blatt 11, die Rechenkern und Hinweise teilen:
 * Belegung einer Schicht je Zeitraum, Standardabweichungen für den Umfang.
 */
import { isBlank, n, required } from '../../excel/index'
import { stratumCell as at } from '../../model/strata'
import type { CellValue, Cells } from '../../model/types'

/** Zeile der Anzahl Einheiten je Schicht: Zeitraum 1, Prognose Zeitraum 2, Zeitraum 2 (Ist). */
export const UNITS = { period1: 11, forecast2: 13, period2: 57 } as const

/** Schicht für den Zeitraum belegt: `D11<>""` bzw. `D13<>""`, `D57<>""`. */
export function used(c: Readonly<Record<string, CellValue | undefined>>, column: string, unitsRow: number): boolean {
  return !isBlank(c[at(column, unitsRow)])
}

/**
 * `N(σ)` einer Standardabweichung für den Stichprobenumfang (Zeilen 29, 30, 59, 65).
 * Ist die Schicht für den Zeitraum belegt, verlangt die Webfassung die Angabe
 * („Angabe fehlt“), wo die Vorlage mit 0 weiterrechnet; für eine nicht belegte
 * Schicht zählt sie wie in der Vorlage 0.
 */
export function sizeDeviation(c: Cells, column: string, unitsRow: number, row: number): number {
  const value = c[at(column, row)]
  return used(c, column, unitsRow) ? required(value) : n(value)
}
