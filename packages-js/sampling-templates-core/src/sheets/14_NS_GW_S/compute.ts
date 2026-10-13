/**
 * Rechenkern Blatt 14_NS_GW_S: nichtstatistisches Verfahren, Auswahl mit gleicher
 * Wahrscheinlichkeit, geschichtet (Art. 6 Abs. 1 UAbs. 2 und 3; Anhang II Nr. 2.1
 * DelVO (EU) 2023/67, Verhältnisschätzung je Schicht). Schichtzeilen werden je
 * Schichtspalte gerechnet (`fillRow`), Summen über alle Schichtspalten
 * (`totalRow`); die Vorlage summiert D–J, die Webfassung zusätzlich AA–AM.
 * Trägt keine Schicht einen Wert, zeigt die Vorlage die Summe 0 – ein Wert ohne
 * Grundlage, den die Webfassung nach der geltenden Richtlinie offen lässt, samt
 * allem, was darauf aufbaut (N, Zulässigkeit, Mindesterfassung, Gesamtstichprobe).
 */
import { divide, guard, isBlank, isNumber, n, plus, required } from '../../excel/index'
import { resolveInputs } from '../../model/sheet'
import { STRATA_COLUMNS, countRow, fillRow, stratumCell as at, totalRow } from '../../model/strata'
import type { CellMap, Cells, SheetContext } from '../../model/types'
import { assessment, checkAdmissibility, checkCoverage, fillSummary, minimumCoverage, projectedError, projectedErrorRate, stratumSampleSize, totalErrorRate, usedTotal } from '../shared/nonstatistical'
import { definition } from './definition'

/**
 * Abschnitt H: Summen der Schichten, Grundgesamtheit und Zulässigkeit (C11–C15).
 * Ohne jede Angabe zu den Schichten ist die Summe ohne Grundlage; BV, N und die
 * Zulässigkeit bauen darauf auf und bleiben mit ihr offen.
 */
function population(c: Cells, context: SheetContext): void {
  c.C11 = totalRow(c, 11, context)
  c.C12 = totalRow(c, 12, context)
  c.C13 = guard(() => plus(required(c.C12), n(c.C8)))
  c.C14 = guard(() => plus(required(c.C11), n(c.C9)))
  c.C15 = checkAdmissibility(c.C14)
}

/** Abschnitt I: Umfang je Schicht, Gesamtstichprobe und Mindesterfassung (Zeile 18, C19–C21). */
function sample(c: Cells, context: SheetContext): void {
  fillRow(c, 18, (column) => stratumSampleSize(c[at(column, 11)], c.C11, c.C16))
  // Die Summe hängt vom Stichprobenumfang ab: Sie bleibt offen, solange er fehlt (die Vorlage zeigt je Schicht 1).
  c.C18 = isNumber(c.C16) ? totalRow(c, 18, context) : null
  c.C19 = guard(() => plus(required(c.C18), n(c.C9)))
  c.C20 = minimumCoverage(c.C14)
  c.C21 = checkCoverage(c.C19, c.C20)
}

/** Abschnitte J und K je Schicht: Summen der Prüfergebnisse und extrapolierter Fehler (Zeilen 24–27). */
function strataProjection(c: Cells, context: SheetContext): void {
  const used = (column: string): boolean => !isBlank(c[at(column, 11)])
  c.C24 = totalRow(c, 24, context)
  c.C25 = totalRow(c, 25, context)
  // =IF(D11="";0;D12*N(D25)/D24): die leere Spalte liefert 0.
  fillRow(c, 27, (column) => (used(column) ? guard(() => divide(required(c[at(column, 12)]) * n(c[at(column, 25)]), required(c[at(column, 24)]))) : 0))
  // Fehlt der Buchwert einer belegten Schicht, rechnet die Vorlage ihren Fehler mit 0; die Webfassung lässt die Summe offen.
  const lacking = STRATA_COLUMNS.some((column) => used(column) && isBlank(c[at(column, 12)]))
  // Summiert werden die belegten Schichten; ist keine hochrechenbar, wäre die Summe 0 ohne Grundlage.
  c.C27 = lacking ? null : usedTotal(c, 27, 11, context)
}

/** Abschnitt K gesamt: extrapolierter Fehler, Fehlerquoten und Würdigung (C28–C35). */
function projection(c: Cells): void {
  c.C28 = n(c.C22)
  c.C29 = projectedError(countRow(c, 25), c.C28, c.C27)
  c.C32 = projectedErrorRate(c.C29, c.C13)
  c.C33 = totalErrorRate(c.C29, c.C30, c.C31, c.C13)
  c.C35 = assessment(c.C33, c.C34)
}

/** Berechnet alle Formelzellen des Blatts 14. */
export function compute(inputs: CellMap, context: SheetContext): CellMap {
  const c = resolveInputs(definition, inputs, context)
  population(c, context)
  sample(c, context)
  strataProjection(c, context)
  projection(c)
  fillSummary(c, { method: 'Nichtstatistisch, gleiche Wahrscheinlichkeit, geschichtet', bookValue: 'C13', projectedError: 'C29', exhaustiveError: 'C28', systemicErrors: 'C30', anomalousErrors: 'C31', sampleSize: 'C19', totalErrorRate: 'C33' })
  return c
}
