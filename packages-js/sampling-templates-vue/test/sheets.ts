/**
 * Fester Blattbestand für die Oberflächentests: die vier Blätter des Fundaments
 * mit Rechenkern, alle übrigen als geplant. So bleiben die Tests stabil,
 * während weitere Blätter entstehen.
 */
import { SHEETS, plannedSheet, type SheetModule } from '@auditcore/sampling-templates-core'

const FOUNDATION = ['02_Grundgesamtheit', '03_MUS_1Z', '04_MUS_1Z_S', '17_Unterstichprobe']

export const FOUNDATION_SHEETS: readonly SheetModule[] = SHEETS.map((sheet) => (FOUNDATION.includes(sheet.id) ? sheet : plannedSheet(sheet.id)))
