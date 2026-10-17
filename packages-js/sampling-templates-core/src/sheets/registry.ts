/**
 * Register aller Blätter der Vorlage. Jedes Blatt liegt in einem eigenen Verzeichnis
 * und exportiert `sheet`; wer ein Blatt baut, ändert nur dessen Verzeichnis – diese
 * Datei bleibt unverändert (siehe docs/blatt-ergaenzen.md). Blatt 01 enthält nur
 * Parameter und steht deshalb nicht im Register.
 */
import type { AvailableSheet, SheetModule } from '../model/sheet'
import type { DataTable } from '../model/table'
import type { SheetId } from '../model/types'
import { sheet as sheet02 } from './02_Grundgesamtheit/index'
import { sheet as sheet03 } from './03_MUS_1Z/index'
import { sheet as sheet04 } from './04_MUS_1Z_S/index'
import { sheet as sheet05 } from './05_MUS_2Z/index'
import { sheet as sheet06 } from './06_MUS_2Z_S/index'
import { sheet as sheet07 } from './07_MUS_3Z/index'
import { sheet as sheet08 } from './08_SRS_1Z/index'
import { sheet as sheet09 } from './09_SRS_1Z_S/index'
import { sheet as sheet10 } from './10_SRS_2Z/index'
import { sheet as sheet11 } from './11_SRS_2Z_S/index'
import { sheet as sheet12 } from './12_SRS_3Z/index'
import { sheet as sheet13 } from './13_NS_GW/index'
import { sheet as sheet14 } from './14_NS_GW_S/index'
import { sheet as sheet15 } from './15_NS_PPS/index'
import { sheet as sheet16 } from './16_NS_PPS_S/index'
import { sheet as sheet17 } from './17_Unterstichprobe/index'
import { sheet as sheet18 } from './18_GFQ_AnhIII/index'
import { sheet as sheet20 } from './20_Druck_KOM/index'
import { sheet as sheetX1 } from './X1_KonsMUS_2017/index'
import { sheet as sheetX1a } from './X1a_RF_2017/index'
import { sheet as sheetX2 } from './X2_DiffSch_2017/index'
import { sheet as sheetX3 } from './X3_DiffSch_S_2017/index'
import { sheet as sheetX4 } from './X4_DiffSch_2Z_2017/index'

/** Alle Blätter in der Reihenfolge der Vorlage. */
export const SHEETS: readonly SheetModule[] = [
  sheet02,
  sheet03,
  sheet04,
  sheet05,
  sheet06,
  sheet07,
  sheet08,
  sheet09,
  sheet10,
  sheet11,
  sheet12,
  sheet13,
  sheet14,
  sheet15,
  sheet16,
  sheet17,
  sheet18,
  sheet20,
  sheetX1,
  sheetX1a,
  sheetX2,
  sheetX3,
  sheetX4,
]

/** Blatt zu einem Blattnamen der Vorlage. */
export function findSheet(id: SheetId, sheets: readonly SheetModule[] = SHEETS): SheetModule | undefined {
  return sheets.find((sheet) => sheet.id === id)
}

/** Nachschlagetabelle eines Blatts (X1a) oder `undefined`. */
export function tableOf(id: SheetId, sheets: readonly SheetModule[] = SHEETS): DataTable | undefined {
  const sheet = findSheet(id, sheets)
  return sheet && !sheet.available ? sheet.table : undefined
}

/** Blätter mit Rechenkern. */
export function availableSheets(sheets: readonly SheetModule[] = SHEETS): AvailableSheet[] {
  return sheets.filter((sheet): sheet is AvailableSheet => sheet.available)
}

/** Blatt mit Rechenkern oder `undefined`, wenn es fehlt oder noch geplant ist. */
export function findAvailableSheet(id: SheetId, sheets: readonly SheetModule[] = SHEETS): AvailableSheet | undefined {
  const sheet = findSheet(id, sheets)
  return sheet?.available ? sheet : undefined
}
