/**
 * Hochwertige bzw. umfassende Schicht je Methodenblatt: Zellen der Anzahl
 * (n_e bzw. N_e) und des Buchwerts (BV_e), bei Schichten die Summenzellen, bei
 * mehreren Zeiträumen je Zeitraum. Grundlage der Angaben `exhaustiveUnits` und
 * `exhaustiveBookValue` der Ergebnisübersicht (Blatt 18 erkennt daran, ob es eine
 * umfassende Schicht gibt; EE_e liefern die Methodenblätter auch ohne Schicht als 0).
 */
import { isNumber } from '../excel/index'
import type { CellMap, CellValue, SheetId } from './types'

const CELLS: Readonly<Record<SheetId, { units: readonly string[]; bookValue: readonly string[] }>> = {
  '03_MUS_1Z': { units: ['C29'], bookValue: ['C30'] },
  '04_MUS_1Z_S': { units: ['C37'], bookValue: ['C38'] },
  '05_MUS_2Z': { units: ['C37', 'C71'], bookValue: ['C38', 'C72'] },
  '06_MUS_2Z_S': { units: ['C41', 'C75'], bookValue: ['C42', 'C76'] },
  '07_MUS_3Z': { units: ['C40', 'C79', 'C113'], bookValue: ['C41', 'C80', 'C114'] },
  '08_SRS_1Z': { units: ['C10'], bookValue: ['C9'] },
  '09_SRS_1Z_S': { units: ['C9'], bookValue: ['C8'] },
  '10_SRS_2Z': { units: ['C10', 'C52'], bookValue: ['C9', 'C51'] },
  '11_SRS_2Z_S': { units: ['C8', 'C54'], bookValue: ['C7', 'C53'] },
  '12_SRS_3Z': { units: ['C10', 'C56', 'C95'], bookValue: ['C9', 'C55', 'C94'] },
  '13_NS_GW': { units: ['C11'], bookValue: ['C10'] },
  '14_NS_GW_S': { units: ['C9'], bookValue: ['C8'] },
  '15_NS_PPS': { units: ['C14'], bookValue: ['C15'] },
  '16_NS_PPS_S': { units: ['C19'], bookValue: ['C20'] },
}

/** Summe der eingetragenen Werte; ohne Eintrag `null`. */
function total(results: CellMap, cells: readonly string[]): CellValue {
  const values = cells.map((cell) => results[cell]).filter(isNumber)
  return values.length ? values.reduce((sum, value) => sum + value, 0) : null
}

/** Anzahl und Buchwert der umfassenden Schicht eines Methodenblatts (über alle Zeiträume); ohne Schicht `null`. */
export function exhaustiveStratumOf(sheet: SheetId, results: CellMap): { units: CellValue; bookValue: CellValue } {
  const cells = CELLS[sheet]
  return cells ? { units: total(results, cells.units), bookValue: total(results, cells.bookValue) } : { units: null, bookValue: null }
}
