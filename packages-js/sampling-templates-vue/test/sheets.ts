/**
 * Fester Blattbestand für die Oberflächentests: die vier Blätter des Fundaments
 * mit Rechenkern, alle übrigen als geplant. So bleiben die Tests stabil,
 * während weitere Blätter entstehen.
 */
import { FAMILIES, SHEETS, findVariant, plannedSheet, type Family, type SheetModule } from '@auditcore/sampling-templates-core'
import type { VueWrapper } from '@vue/test-utils'

const FOUNDATION = ['02_Grundgesamtheit', '03_MUS_1Z', '04_MUS_1Z_S', '17_Unterstichprobe']

export const FOUNDATION_SHEETS: readonly SheetModule[] = SHEETS.map((sheet) => (FOUNDATION.includes(sheet.id) ? sheet : plannedSheet(sheet.id)))

/**
 * Verfahren über die Filter der Auswahl einstellen: Familie, Zeiträume und
 * Schichtung, danach „Verfahren verwenden“ bzw. der Listeneintrag der Altvorlage.
 */
export async function pickVariant(wrapper: VueWrapper, sheet: string, families: readonly Family[] = FAMILIES): Promise<void> {
  const index = families.findIndex((entry) => entry.variants.some((variant) => variant.sheet === sheet))
  const variant = findVariant(sheet, families)
  await wrapper.findAll('[role="tab"]')[index]!.trigger('click')
  if (variant?.periods !== undefined) await wrapper.get(`[data-periods="${variant.periods}"]`).trigger('click')
  if (variant?.stratified !== undefined) await wrapper.get(`[data-stratified="${String(variant.stratified)}"]`).trigger('click')
  await wrapper.get(`[data-sheet="${sheet}"]`).trigger('click')
}
