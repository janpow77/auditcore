/**
 * Rechenkern Blatt 11, Abschnitt L: Neuberechnung für Zeitraum 2 (Art. 5 Abs. 6
 * und 7 DelVO (EU) 2023/67) – aktualisierte Größen, Standardansatz, globaler
 * Ansatz, Erhöhung bei begrenztem Umfang und endgültige Umfänge je Schicht
 * (C57–C81).
 */
import { divide, guard, isBlank, isNumber, le, minus, n, ne, plus, required, roundUp, squareRoot } from '../../excel/index'
import { unfounded } from '../../model/policy'
import { fillRow, stratumCell as at, totalRow } from '../../model/strata'
import type { CellValue, Cells, SheetContext } from '../../model/types'
import { type Pending, type Recalculation, allocate, appliedRandomSize, checkAnnualMinimum, increasedSize, minimumRandomSize, netLimitedSize, NOT_APPLICABLE, recalculationOf, strataTotal } from '../shared/srs'
import { checkStratumUnits } from '../shared/statistical'
import { UNITS, sizeDeviation, used } from './strata'
import { blockedGlobal, globalSize } from '../shared/periods'

/** Aktualisierte Größen (C57–C65): Buchwert des Geschäftsjahres, TE, AE, Standardabweichung Zeitraum 1. */
function updated(c: Cells, context: SheetContext): void {
  c.C57 = totalRow(c, 57, context)
  c.C58 = totalRow(c, 58, context)
  // =C12+N(C7)+C58+N(C53): ohne Buchwert eines Zeitraums baute der Wert auf einer Summe 0 ohne Grundlage auf.
  c.C61 = guard(() => plus(plus(plus(required(c.C12), n(c.C7)), required(c.C58)), n(c.C53)))
  c.C62 = guard(() => required(c.C22) * required(c.C61))
  // =IF(C60="";C25;C60)*C61 – leer = Wert aus I.
  c.C63 = guard(() => required(isBlank(c.C60) ? c.C25 : c.C60) * required(c.C61))
  // =IF(D11="";"";IF(D51="";D29;D51)) – s, ersatzweise σ; fehlen beide, bleibt die Zelle offen (die Vorlage zeigt 0).
  fillRow(c, 65, (column) => {
    if (!used(c, column, UNITS.period1)) return null
    return (isBlank(c[at(column, 51)]) ? c[at(column, 29)] : c[at(column, 51)]) ?? null
  })
}

/** `=IF(C68<=0;"✖ nicht anwendbar (Nenner ≤ 0)";ROUNDUP(C20^2*C57*C67/C68;0))`; ein leerer Nenner ist ein Fehlerwert. */
function standardSize(c: Cells): CellValue {
  const denominator = c.C68
  if (!isNumber(denominator)) return null
  if (le(denominator, 0)) return NOT_APPLICABLE
  return guard(() => roundUp(divide(required(c.C20) ** 2 * required(c.C57) * required(c.C67), denominator)))
}

/** Standardansatz (Art. 5 Abs. 6 Buchst. a): Hilfszeilen, Nenner und Umfang für Zeitraum 2 (Zeilen 66–69). */
function standard(c: Cells, pending: Pending, context: SheetContext): void {
  // =IF(D11="";0;D11^2/D44*N(D65)^2)
  fillRow(c, 66, (column) => {
    if (!used(c, column, UNITS.period1)) return 0
    return guard(() => divide(required(c[at(column, 11)]) ** 2, required(c[at(column, 44)])) * required(c[at(column, 65)]) ** 2)
  })
  c.C66 = strataTotal(c, 66, pending, context, (column) => used(c, column, UNITS.period1))
  // =IF(D57="";0;D57*N(D59)^2)
  fillRow(c, 67, (column) => (used(c, column, UNITS.period2) ? guard(() => required(c[at(column, 57)]) * required(c[at(column, 59)]) ** 2) : 0))
  c.C67 = strataTotal(c, 67, pending, context, (column) => used(c, column, UNITS.period2))
  c.C68 = guard(() => minus(minus(required(c.C62), required(c.C63)) ** 2, required(c.C20) ** 2 * required(c.C66)))
  c.C69 = standardSize(c)
}

/** Globaler Ansatz (Art. 5 Abs. 6 Buchst. b): Gesamtumfang und Zusatzeinheiten für Zeitraum 1 (Zeilen 70–76). */
function global(c: Cells, pending: Pending, limit: number | null, context: SheetContext): void {
  // =N(D11)*N(D65)^2+N(D57)*N(D59)^2
  fillRow(c, 70, (column) =>
    guard(() => n(c[at(column, 11)]) * sizeDeviation(c, column, UNITS.period1, 65) ** 2 + n(c[at(column, 57)]) * sizeDeviation(c, column, UNITS.period2, 59) ** 2),
  )
  c.C70 = strataTotal(c, 70, pending, context, (column) => used(c, column, UNITS.period1) || used(c, column, UNITS.period2))
  c.C71 = guard(() => required(c.C11) + required(c.C57))
  // Nach der DelVO nur bei TE > AE (Entscheidung des Inhabers vom 17.10.2026); die Vorlage prüft das nicht.
  c.C72 = globalSize(c.C62, c.C63, () => roundUp(divide(required(c.C20) * required(c.C71) * squareRoot(divide(required(c.C70), required(c.C71))), minus(required(c.C62), required(c.C63))) ** 2))
  c.C73 = netLimitedSize(limit, c.C9, c.C55)
  c.C74 = appliedRandomSize(c.C72, minimumRandomSize(6, c.C8, c.C54), c.C73, pending('C72'), true)
  // =IF(D11="";"";MAX(0;ROUNDUP(D11/C71*C74;0)-D44))
  fillRow(c, 76, (column) => {
    if (!used(c, column, UNITS.period1)) return null
    return guard(() => Math.max(0, minus(allocate(c[at(column, 11)], c.C71, c.C74), required(c[at(column, 44)]))))
  })
  // Nach der DelVO nicht anwendbar: keine Zusatzeinheiten aus der globalen Neuberechnung (statt der Summe 0).
  c.C76 = blockedGlobal(c, 'C72', pending) ? null : strataTotal(c, 76, pending, context)
}

/**
 * Umfang einer Schicht für Zeitraum 2 nach einem Ansatz der Neuberechnung, vor
 * `MAX(3;…)`. Ein Text oder Leerwert in C69 bzw. C74 ist in der Rechnung ein
 * Fehlerwert (gemessen: negativer Nenner → `""` in Zeile 77).
 */
function recalculatedSize(c: Cells, column: string, approach: Exclude<Recalculation, 'none'>): number {
  const units = c[at(column, 57)]
  if (approach === 'standard') return allocate(units, c.C57, c.C69)
  if (approach === 'global') return allocate(units, c.C71, c.C74)
  return increasedSize(c[at(column, 45)], [[units, c[at(column, 13)]], [c[at(column, 58)], c[at(column, 14)]]])
}

/**
 * Anzuwendender Umfang einer Schicht für Zeitraum 2 (Zeile 77). Ohne
 * Neuberechnung gilt `MAX(3;D45)`: Trägt D45 keinen Umfang, übergeht `MAX` den
 * Bezug, und die Vorlage zeigt 3 (gemessen). Für eine Schicht ohne Prognose, die
 * erst in Zeitraum 2 belegt ist, ist das die Untergrenze nach Art. 5 Abs. 5 –
 * der Gesamtumfang (C42) steht fest. Gibt es keinen Gesamtumfang (leere
 * Parameter, „TE ≤ AE“), ist die 3 ein Wert ohne Grundlage. Ist D45 nur offen,
 * weil eine Angabe fehlt, bleibt auch dieser Umfang offen.
 */
function periodTwoSize(c: Cells, column: string, approach: Recalculation, pending: Pending, context: SheetContext): CellValue {
  if (approach !== 'none') return guard(() => Math.max(3, recalculatedSize(c, column, approach)))
  const planned = c[at(column, 45)]
  if (isNumber(planned)) return Math.max(3, planned)
  if (pending(at(column, 45))) return null
  return isNumber(c.C42) ? 3 : unfounded(context, 3)
}

/** Endgültige Umfänge je Schicht und Gesamtstichprobe (Zeilen 77–81). */
function finalSizes(c: Cells, pending: Pending, context: SheetContext): void {
  const approach = recalculationOf(c.C33)
  fillRow(c, 77, (column) => (used(c, column, UNITS.period2) ? periodTwoSize(c, column, approach, pending, context) : null))
  // =IF(D11="";"";D44+IF(LEFT(C33;6)="Global";D76;0))
  fillRow(c, 78, (column) => {
    if (!used(c, column, UNITS.period1)) return null
    return guard(() => required(c[at(column, 44)]) + (approach === 'global' ? required(c[at(column, 76)]) : 0))
  })
  fillRow(c, 79, (column) => (used(c, column, UNITS.period2) ? checkStratumUnits(c[at(column, 77)], pending(at(column, 77)), context) : null))
  // Globale Neuberechnung nach der DelVO nicht anwendbar: kein Umfang für Zeitraum 2 (statt der Summe 0 leerer Schichten).
  c.C77 = approach === 'global' && blockedGlobal(c, 'C72', pending) ? null : strataTotal(c, 77, pending, context)
  c.C78 = strataTotal(c, 78, pending, context)
  c.C80 = guard(() => required(c.C78) + required(c.C77) + n(c.C8) + n(c.C54))
  // =IF(C77=0;"";IF(C80>=30;…))
  c.C81 = isNumber(c.C77) && ne(c.C77, 0) && isNumber(c.C80) ? checkAnnualMinimum(c.C80) : null
}

/** Abschnitt L in Blattreihenfolge; `limit` ist der begrenzte Umfang (C39). */
export function recalculation(c: Cells, pending: Pending, limit: number | null, context: SheetContext): void {
  updated(c, context)
  standard(c, pending, context)
  global(c, pending, limit, context)
  finalSizes(c, pending, context)
}
