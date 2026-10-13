/**
 * Rechenkern Blatt 16_NS_PPS_S: nichtstatistisches Verfahren, wertproportionale
 * Auswahl (PPS), geschichtet (Art. 6 Abs. 1 Buchst. a und UAbs. 2–3; Anhang II
 * Nr. 1.1 DelVO (EU) 2023/67). Schichtzeilen werden je Schichtspalte gerechnet
 * (`fillRow`), Summen über alle Schichtspalten (`totalRow`); die Vorlage summiert
 * D–J, die Webfassung zusätzlich AA–AM. Trägt keine Schicht einen Wert, zeigt
 * die Vorlage die Summe 0 – ein Wert ohne Grundlage, den die Webfassung nach der
 * geltenden Richtlinie offen lässt, samt allem, was darauf aufbaut.
 */
import { divide, eq, guard, isBlank, isNumber, minus, n, plus, required } from '../../excel/index'
import { resolveInputs } from '../../model/sheet'
import { countRow, fillRow, stratumCell as at, totalRow } from '../../model/strata'
import type { CellMap, CellValue, Cells, SheetContext } from '../../model/types'
import { assessment, checkAdmissibility, checkCoverage, fillSummary, minimumCoverage, projectedErrorRate, stratumSampleSize, totalErrorRate, usedTotal } from '../shared/nonstatistical'
import { definition } from './definition'

/**
 * Summe einer Schichtzeile, die vom Stichprobenumfang abhängt: offen, solange
 * der Umfang fehlt. `helper`: Zeile, die für unbelegte Schichten 0 trägt.
 */
type Total = (row: number, helper?: boolean) => CellValue

/**
 * Abschnitt H: Summen der Schichten und Zulässigkeit (C9–C12). Ohne jede
 * Anzahl der Einheiten ist die Summe ohne Grundlage; N und die Zulässigkeit
 * bauen darauf auf und bleiben mit ihr offen.
 */
function population(c: Cells, context: SheetContext): void {
  c.C9 = totalRow(c, 9, context)
  c.C10 = totalRow(c, 10, context)
  c.C11 = c.C10 ?? null
  c.C12 = checkAdmissibility(c.C11)
}

/** Abschnitt I: Umfang, Grenzwert, Zufallsschicht und Auswahlintervall je Schicht (Zeilen 15–23). */
function sample(c: Cells, total: Total, context: SheetContext): void {
  const used = (column: string): boolean => !isBlank(c[at(column, 9)])
  fillRow(c, 15, (column) => stratumSampleSize(c[at(column, 9)], c.C9, c.C13))
  c.C15 = total(15)
  c.C16 = minimumCoverage(c.C11)
  c.C17 = checkCoverage(c.C15, c.C16)
  fillRow(c, 18, (column) => (used(column) ? guard(() => divide(required(c[at(column, 9)]), required(c[at(column, 15)]))) : null))
  c.C19 = totalRow(c, 19, context)
  c.C20 = totalRow(c, 20, context)
  fillRow(c, 21, (column) => (used(column) ? guard(() => minus(required(c[at(column, 9)]), n(c[at(column, 20)]))) : null))
  c.C21 = totalRow(c, 21, context)
  fillRow(c, 22, (column) => (used(column) ? guard(() => minus(required(c[at(column, 15)]), n(c[at(column, 19)]))) : null))
  c.C22 = total(22)
  fillRow(c, 23, (column) => (used(column) ? guard(() => divide(required(c[at(column, 21)]), required(c[at(column, 22)]))) : null))
}

/** Abschnitte J und K: Summen der Prüfergebnisse, Hochrechnung je Schicht, Fehlerquoten und Würdigung (C25–C36). */
function projection(c: Cells, total: Total, context: SheetContext): void {
  const used = (column: string): boolean => !isBlank(c[at(column, 9)])
  c.C25 = totalRow(c, 25, context)
  c.C26 = totalRow(c, 26, context)
  // =IF(D9="";0;N(D25)+D23*N(D26)): die leere Spalte liefert 0.
  fillRow(c, 28, (column) => (used(column) ? guard(() => plus(n(c[at(column, 25)]), required(c[at(column, 23)]) * n(c[at(column, 26)]))) : 0))
  // Summiert werden die belegten Schichten; ist keine hochrechenbar, wäre die Summe 0 ohne Grundlage.
  c.C28 = total(28, true)
  c.C29 = c.C25 ?? null
  c.C30 = eq(countRow(c, 26), 0) ? null : (c.C28 ?? null)
  c.C33 = projectedErrorRate(c.C30, c.C9)
  c.C34 = totalErrorRate(c.C30, c.C31, c.C32, c.C9)
  c.C36 = assessment(c.C34, c.C35)
}

/** Berechnet alle Formelzellen des Blatts 16. */
export function compute(inputs: CellMap, context: SheetContext): CellMap {
  const c = resolveInputs(definition, inputs, context)
  const pending = !isNumber(c.C13)
  const total: Total = (row, helper = false) => (pending ? null : helper ? usedTotal(c, row, 9, context) : totalRow(c, row, context))
  population(c, context)
  sample(c, total, context)
  projection(c, total, context)
  fillSummary(c, { method: 'Nichtstatistisch, PPS, geschichtet', bookValue: 'C9', projectedError: 'C30', exhaustiveError: 'C29', systemicErrors: 'C31', anomalousErrors: 'C32', sampleSize: 'C15', totalErrorRate: 'C34' })
  return c
}
