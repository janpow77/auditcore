/** Blatt 17_Unterstichprobe: Fehler einer Stichprobeneinheit aus einer Unterstichprobe; in der Webfassung eine Liste von Einheiten. */
import { ge, isNumber, sameText } from '../../excel/index'
import type { SubsampleRole } from '../../model/definition'
import { defineSheet, type SubsampleGroup, type SubsampleNeeds, type SubsampleTotals } from '../../model/sheet'
import type { CellMap, SheetContext } from '../../model/types'
import { compute } from './compute'
import { definition } from './definition'
import { deviations } from './deviations'
import { en } from './texts.en'

/** Erfundene Beispieleinheit; sie stammt aus keiner Prüfung. */
const sample: CellMap = { C5: 'Beispiel-Vorhaben 17', C6: 250000, C7: 140, C10: 30, C11: 61000, C12: 915, W5: 'Zufallsschicht', W6: 'Variante 1' }

const ROLES: readonly SubsampleRole[] = ['highValueErrors', 'errorRateSum', 'errorSum', 'bookValueSum']
type Sums = Record<SubsampleRole, number | null>
const emptySums = (): Sums => ({ highValueErrors: null, errorRateSum: null, errorSum: null, bookValueSum: null })
const add = (total: number | null, value: number): number => (total ?? 0) + value

/** Beitrag einer Einheit: Fehler der hochwertigen Einheit oder Fehlerquote, Fehler und Buchwert der Zufallsschicht. */
function contribution(cells: CellMap): Partial<Record<SubsampleRole, number>> | null {
  const { W7: error, W8: rate, C6: bookValue } = cells
  if (!isNumber(error) || !isNumber(rate) || !isNumber(bookValue)) return null
  return sameText(cells.W5, 'hochwertige Einheit') ? { highValueErrors: error } : { errorRateSum: rate, errorSum: error, bookValueSum: bookValue }
}

function addTo(sums: Sums, part: Partial<Record<SubsampleRole, number>>): void {
  for (const role of ROLES) {
    const value = part[role]
    if (value !== undefined) sums[role] = add(sums[role], value)
  }
}

/** Schicht- bzw. Zeitraumnummer der Einheit: ganze Zahl ab 1, sonst `undefined` (nicht zugeordnet). */
const numberOf = (value: unknown): number | undefined => (isNumber(value) && Number.isInteger(value) && ge(value, 1) ? value : undefined)

/** Beitrag der Einheit in die Gruppe ihrer Schicht und ihres Zeitraums; `false`: Die nötige Angabe fehlt. */
function assign(groups: Map<string, SubsampleGroup>, cells: CellMap, needs: SubsampleNeeds, part: Partial<Record<SubsampleRole, number>>): boolean {
  const stratum = needs.stratum ? numberOf(cells.W9) : null
  const period = needs.period ? numberOf(cells.W10) : null
  if (stratum === undefined || period === undefined) return false
  const key = `${stratum}|${period}`
  const group = groups.get(key) ?? { ...emptySums(), stratum, period }
  addTo(group as Sums, part)
  groups.set(key, group)
  return true
}

/**
 * Summen über alle Einheiten: Fehler der hochwertigen Einheiten (ΣE_e) sowie
 * Fehlerquoten, Fehler und Buchwerte der Einheiten der Zufallsschicht.
 * Einheiten ohne bestimmbaren Fehler zählen als unvollständig und gehen nicht ein.
 * `needs`: Unterscheidet das Methodenblatt nach Schicht bzw. Zeitraum, entstehen
 * zusätzlich Summen je Gruppe (W9 Schicht, W10 Zeitraum); Einheiten ohne die
 * nötige Angabe zählen als nicht zugeordnet.
 */
function totals(rows: readonly CellMap[], context: SheetContext, needs: SubsampleNeeds = { stratum: false, period: false }): SubsampleTotals {
  const sums = emptySums()
  const groups = new Map<string, SubsampleGroup>()
  let incomplete = 0
  let unassigned = 0
  for (const row of rows) {
    const cells = compute(row, context)
    const part = contribution(cells)
    if (!part) {
      incomplete += 1
      continue
    }
    addTo(sums, part)
    if (!assign(groups, cells, needs, part)) unassigned += 1
  }
  const grouped = needs.stratum || needs.period
  return { ...sums, units: rows.length, incomplete, ...(grouped ? { groups: [...groups.values()], unassigned } : {}) }
}

export const sheet = defineSheet({ id: '17_Unterstichprobe', definition, compute, sample: { inputs: sample }, deviations, totals, translations: { en } })
