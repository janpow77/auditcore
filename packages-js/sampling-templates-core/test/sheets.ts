/**
 * Fester Blattbestand für Tests, die auf „noch nicht verfügbare“ Blätter
 * angewiesen sind: die vier Blätter des Fundaments mit Rechenkern, alle
 * übrigen als geplant. So bleiben diese Tests stabil, während weitere Blätter
 * entstehen.
 */
import { plannedSheet, type SheetModule } from '../src/model/sheet'
import { SHEETS } from '../src/sheets/registry'

export const FOUNDATION = ['02_Grundgesamtheit', '03_MUS_1Z', '04_MUS_1Z_S', '17_Unterstichprobe']

export const FOUNDATION_SHEETS: readonly SheetModule[] = SHEETS.map((sheet) => (FOUNDATION.includes(sheet.id) ? sheet : plannedSheet(sheet.id)))
