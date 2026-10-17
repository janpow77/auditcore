/**
 * Rechenkern Blatt 11, Abschnitt N: Hochrechnung (Verhältnisschätzung) je
 * Schicht über beide Zeiträume und Genauigkeit (Anhang II Nr. 2.2 DelVO (EU)
 * 2023/67), Zeilen 89–93. Fehlergrenzen und Würdigung folgen in `conclusion`.
 */
import { divide, gt, guard, isBlank, n, plus, required, squareRoot } from '../../excel/index'
import { unfounded } from '../../model/policy'
import { countRow, fillRow, stratumCell as at } from '../../model/strata'
import type { Cells, SheetContext } from '../../model/types'
import { type Pending, ratioProjection, strataTotal } from '../shared/srs'
import { UNITS, used } from './strata'

/**
 * Beitrag eines Zeitraums zur Genauigkeit: `IF(OR(N_h="";s_qh="");0;N_h^2/n_h*s_qh^2)`.
 * Fehlt s_qh, setzt die Vorlage den Beitrag ausdrücklich auf 0; die Webfassung
 * ebenso und weist es aus (`zeroAssumed`).
 */
function precisionTerm(c: Cells, column: string, unitsRow: number, sizeRow: number, deviationRow: number): number {
  if (!used(c, column, unitsRow) || isBlank(c[at(column, deviationRow)])) return 0
  return divide(required(c[at(column, unitsRow)]) ** 2, required(c[at(column, sizeRow)])) * required(c[at(column, deviationRow)]) ** 2
}

/**
 * Zeile 89: `=IF(D11="";0;D12*N(D50)/D49)+IF(D57="";0;D58*N(D85)/D84)` – fehlt der
 * Buchwert einer belegten Schicht, bleibt die Zelle offen. Trägt keine Schicht in
 * keinem Zeitraum eine Fehlersumme, ist die Hochrechnung 0 ein Wert ohne
 * Grundlage; fehlt sie nur einzelnen Schichten, zählt sie wie in der Vorlage 0
 * (`zeroAssumed`).
 */
function projectedErrors(c: Cells, anyErrorSum: boolean, context: SheetContext): void {
  fillRow(c, 89, (column) => {
    const [first, second] = [used(c, column, UNITS.period1), used(c, column, UNITS.period2)]
    if (!first && !second) return 0
    const projected = guard(() =>
      plus(first ? ratioProjection(c[at(column, 12)], c[at(column, 50)], c[at(column, 49)]) : 0, second ? ratioProjection(c[at(column, 58)], c[at(column, 85)], c[at(column, 84)]) : 0),
    )
    return anyErrorSum ? projected : unfounded(context, projected)
  })
}

/**
 * Abschnitt N: Hochrechnung und Genauigkeit (Zeilen 89–93). Beide gelten für das
 * Geschäftsjahr: Ist für einen der beiden Zeiträume keine Schicht belegt (C11
 * bzw. C57 ohne Wert), bleiben ihre Summen offen – sie entstünden sonst allein
 * aus dem anderen Zeitraum.
 */
export function projection(c: Cells, pending: Pending, context: SheetContext): void {
  const anyErrorSum = gt(countRow(c, 50) + countRow(c, 85), 0)
  const bothPeriods = !isBlank(c.C11) && !isBlank(c.C57)
  const usedAny = (column: string): boolean => used(c, column, UNITS.period1) || used(c, column, UNITS.period2)
  projectedErrors(c, anyErrorSum, context)
  // Ein Fehlerwert in einem der beiden Summanden (z. B. kein Umfang für Zeitraum 2) leert die ganze Zelle (IFERROR um die Summe).
  fillRow(c, 90, (column) => guard(() => precisionTerm(c, column, UNITS.period1, 78, 52) + precisionTerm(c, column, UNITS.period2, 77, 87)))
  c.C89 = bothPeriods ? strataTotal(c, 89, pending, context, usedAny) : null
  c.C90 = bothPeriods ? strataTotal(c, 90, pending, context, usedAny) : null
  c.C91 = plus(n(c.C47), n(c.C82))
  // =IF(COUNT($D$50:$J$50;$D$85:$J$85)=0;"";C91+C89)
  c.C92 = anyErrorSum ? guard(() => plus(n(c.C91), required(c.C89))) : null
  c.C93 = guard(() => required(c.C20) * squareRoot(required(c.C90)))
}
