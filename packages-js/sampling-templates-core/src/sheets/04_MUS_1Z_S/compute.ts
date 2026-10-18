/**
 * Rechenkern Blatt 04_MUS_1Z_S: MUS-Standardansatz, ein Stichprobenzeitraum,
 * geschichtet (Anhang II Nr. 1.1 DelVO (EU) 2023/67). Schichtzeilen werden je
 * Schichtspalte gerechnet (`fillRow`), Summen über alle Schichtspalten
 * (`sumRow`); die Vorlage summiert D–J, die Webfassung zusätzlich AA–AM.
 */
import { divide, eq, guard, isBlank, minus, n, required, roundUp, squareRoot } from '../../excel/index'
import { resolveInputs } from '../../model/sheet'
import { unfounded } from '../../model/policy'
import { STRATA_COLUMNS, countRow, fillRow, rowValues, stratumCell as at, sumRow, totalRow } from '../../model/strata'
import type { CellMap, CellValue, Cells, SheetContext } from '../../model/types'
import { zValue } from '../01_Parameter/index'
import { appliedSampleSize, assessment, checkConfidence, checkMateriality, checkTolerableError, checkStratumUnits, computedSampleSize, isSizePending, limitedSampleSize, lowerErrorLimit } from '../shared/statistical'
import { definition } from './definition'

/** Summe einer berechneten Schichtzeile; `helper`: Hilfszeile, die für unbelegte Schichten 0 trägt. */
type Total = (row: number, helper?: boolean) => CellValue

/**
 * Summe einer Hilfszeile (25, 52): Unbelegte Schichten tragen dort wie in der
 * Vorlage 0. Ist keine Schicht belegt, ist die Summe 0 ein Wert ohne Grundlage.
 */
function helperTotal(c: Cells, row: number, context: SheetContext): CellValue {
  return STRATA_COLUMNS.some((column) => !isBlank(c[at(column, 9)])) ? sumRow(c, row) : unfounded(context, 0)
}

/** Abschnitte H und I: Summen der Schichten, z, zulässiger und voraussichtlicher Fehler (C9–C26). */
function parameters(c: Cells, context: SheetContext): void {
  c.C9 = totalRow(c, 9, context)
  c.C10 = totalRow(c, 10, context)
  c.C11 = guard(() => minus(required(c.C9), required(context.sheets['02_Grundgesamtheit']?.C51)))
  c.C15 = guard(() => zValue(context.parameters, c.C13, c.C14))
  c.C16 = checkConfidence(c.C12, c.C13)
  c.C18 = checkMateriality(c.C17)
  c.C19 = guard(() => required(c.C17) * required(c.C9))
  c.C21 = guard(() => required(c.C20) * required(c.C9))
  c.C22 = checkTolerableError(c.C19, c.C21, c.C20)
  // Zeile 25: fehlt σ_rh einer belegten Schicht, rechnet die Vorlage mit 0; die Webfassung zeigt „Angabe fehlt“.
  fillRow(c, 25, (column) => (isBlank(c[at(column, 9)]) ? 0 : guard(() => required(c[at(column, 9)]) * required(c[at(column, 24)]) ** 2)))
  c.C25 = rowValues(c, 25).includes(null) ? null : helperTotal(c, 25, context)
  c.C26 = guard(() => squareRoot(divide(required(c.C25), required(c.C9))))
}

/**
 * Abschnitt J (C27–C33). Rückgabe `true`: Der Umfang ist offen, weil eine
 * Angabe fehlt, mit der die Vorlage als 0 weiterrechnen würde – dann bleiben
 * auch die Summen der davon abhängigen Schichtzeilen offen.
 */
function sampleSize(c: Cells): boolean {
  c.C27 = computedSampleSize({ z: c.C15, bookValue: c.C9, deviation: c.C26, tolerable: c.C19, anticipated: c.C21 })
  const [check, limit] = limitedSampleSize(c.C30, c.C29, c.C28)
  c.C31 = check
  c.C32 = limit
  const pending = isSizePending(c.C27, c.C19, c.C15)
  c.C33 = appliedSampleSize(c.C27, limit, pending)
  return pending
}

/** Abschnitt K: Stichprobenauswahl je Schicht (Zeilen 35–43). */
/*
 * Hochwertige Einheiten (Zeilen 37, 38, 45) und Iteration (Zeile 43) sind freiwillig
 * (Entscheidung des Inhabers vom 17.10.2026): leer heißt keine, ihre Summe ist wie
 * in der Vorlage 0 und kein Wert ohne Grundlage.
 */
function selection(c: Cells, total: Total, pending: boolean, context: SheetContext): void {
  const used = (column: string): boolean => !isBlank(c[at(column, 9)])
  fillRow(c, 35, (column) => (used(column) ? guard(() => roundUp(divide(required(c[at(column, 9)]), required(c.C9)) * required(c.C33))) : null))
  fillRow(c, 36, (column) => (used(column) ? guard(() => divide(required(c[at(column, 9)]), required(c[at(column, 35)]))) : null))
  fillRow(c, 39, (column) => (used(column) ? guard(() => minus(required(c[at(column, 9)]), n(c[at(column, 38)]))) : null))
  fillRow(c, 40, (column) => (used(column) ? guard(() => minus(required(c[at(column, 35)]), n(c[at(column, 37)]))) : null))
  fillRow(c, 41, (column) => (used(column) ? checkStratumUnits(c[at(column, 40)], pending, context) : null))
  fillRow(c, 42, (column) => (used(column) ? guard(() => divide(required(c[at(column, 39)]), required(c[at(column, 40)]))) : null))
  c.C35 = total(35)
  c.C37 = sumRow(c, 37)
  c.C38 = sumRow(c, 38)
  c.C39 = totalRow(c, 39, context)
  c.C40 = total(40)
  c.C43 = sumRow(c, 43)
}

/** Abschnitte L und M je Schicht: Fehler, Hochrechnung und Hilfszeile der Genauigkeit (Zeilen 45–52). */
function strataProjection(c: Cells, total: Total, context: SheetContext): void {
  const used = (column: string): boolean => !isBlank(c[at(column, 9)])
  c.C45 = sumRow(c, 45)
  c.C46 = totalRow(c, 46, context)
  fillRow(c, 49, (column) => (used(column) ? n(c[at(column, 45)]) : null))
  fillRow(c, 50, (column) => (used(column) ? guard(() => required(c[at(column, 42)]) * n(c[at(column, 46)])) : null))
  fillRow(c, 51, (column) => (used(column) ? guard(() => required(c[at(column, 49)]) + required(c[at(column, 50)])) : null))
  fillRow(c, 52, (column) => {
    if (!used(column) || isBlank(c[at(column, 47)])) return 0
    return guard(() => divide(required(c[at(column, 39)]) ** 2, required(c[at(column, 40)])) * required(c[at(column, 47)]) ** 2)
  })
  c.C49 = totalRow(c, 49, context)
  c.C50 = total(50)
  c.C51 = total(51)
  c.C52 = total(52, true)
}

/** Abschnitt M gesamt: Hochrechnung, Genauigkeit und Fehlergrenzen (C53–C62). */
function projection(c: Cells): void {
  c.C53 = eq(countRow(c, 46), 0) ? null : (c.C51 ?? null)
  c.C54 = guard(() => required(c.C15) * squareRoot(required(c.C52)))
  c.C57 = guard(() => required(c.C53) + required(c.C54) + n(c.C55) + n(c.C56))
  c.C58 = lowerErrorLimit(c.C14, c.C53, c.C54, c.C55, c.C56)
  c.C59 = guard(() => divide(required(c.C54), required(c.C9)))
  c.C60 = guard(() => divide(required(c.C53), required(c.C9)))
  c.C61 = guard(() => divide(required(c.C53) + n(c.C55) + n(c.C56), required(c.C9)))
  c.C62 = guard(() => divide(required(c.C57), required(c.C9)))
}

/** Ergebnisübersicht für Blatt 18 (feste Zellen N3–N11). */
function summary(c: Cells): void {
  c.N3 = 'MUS-Standardansatz, 1 Zeitraum, geschichtet'
  c.N4 = c.C9 ?? null
  c.N5 = c.C53 ?? null
  c.N6 = c.C49 ?? null
  c.N7 = c.C54 ?? null
  c.N8 = n(c.C55)
  c.N9 = n(c.C56)
  c.N10 = c.C35 ?? null
  c.N11 = c.C61 ?? null
}

/** Berechnet alle Formelzellen des Blatts 04. */
export function compute(inputs: CellMap, context: SheetContext): CellMap {
  const c = resolveInputs(definition, inputs, context)
  parameters(c, context)
  const pending = sampleSize(c)
  // Summe einer Schichtzeile, die vom Stichprobenumfang abhängt: offen, solange der Umfang offen ist.
  const total: Total = (row, helper = false) => (pending ? null : helper ? helperTotal(c, row, context) : totalRow(c, row, context))
  selection(c, total, pending, context)
  strataProjection(c, total, context)
  projection(c)
  c.C63 = assessment(c.C61, c.C62, c.C17)
  summary(c)
  return c
}
