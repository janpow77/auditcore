/** Anzeigemodell eines Listenblatts (Blatt 17): Übersicht der Einheiten und Summen für das Methodenblatt. */
import { formatFieldValue } from '../format/numbers'
import type { MessageKey, Translate } from '../i18n/messages'
import { cellsOf, fieldsOf, findField, type FieldDefinition, type SubsampleRole } from '../model/definition'
import { subsampleNeeds, subsampleTargets } from '../model/list'
import type { AvailableSheet, SubsampleTotals } from '../model/sheet'
import { translateValue } from '../model/texts'
import type { CellMap, SheetContext } from '../model/types'

export interface ListView {
  /** Spaltenüberschriften der Übersicht. */
  columns: readonly string[]
  /** Je Einheit die Anzeige der Spalten. */
  rows: readonly (readonly string[])[]
  totals: readonly { role: SubsampleRole; label: string; value: string; target: string }[]
  /** Einheiten ohne bestimmbaren Fehler. */
  incomplete: number
  /** Einheiten ohne die Schicht- bzw. Zeitraumangabe, die das gewählte Methodenblatt braucht. */
  unassigned: number
  /** Das Methodenblatt hat Felder, die Summen aufnehmen. */
  transferable: boolean
}

const TOTAL_KEYS: Readonly<Record<SubsampleRole, MessageKey>> = {
  highValueErrors: 'totalHighValueErrors',
  errorRateSum: 'totalErrorRateSum',
  errorSum: 'totalErrorSum',
  bookValueSum: 'totalBookValueSum',
}

/** Felder des Listenblatts, die die Einheit einer Schicht bzw. einem Zeitraum des Methodenblatts zuordnen. */
const STRATUM_ALIAS = 'methodStratumNumber'
const PERIOD_ALIAS = 'methodPeriod'

/** Zielzelle(n) eines Felds: bei Schichtzeilen der Bereich der Schichtspalten. */
function targetOf(field: FieldDefinition): string {
  const cells = cellsOf(field)
  return cells.length > 1 ? `${cells[0]} ff., je Schicht` : field.cell
}

/** Summe über Gruppen; `null`, solange keine beiträgt. */
function sumOf(values: readonly (number | null)[]): number | null {
  const present = values.filter((value): value is number => value !== null)
  return present.length ? present.reduce((total, value) => total + value, 0) : null
}

/** Übersicht der Einheiten und die Summen, die das Methodenblatt `method` übernehmen kann. */
export function buildListView(sheet: AvailableSheet, rows: readonly CellMap[], method: AvailableSheet | null, context: SheetContext, t: Translate): ListView {
  const targets = method ? subsampleTargets(method.definition) : []
  const needs = method ? subsampleNeeds(method.definition) : undefined
  const totals: SubsampleTotals | undefined = sheet.totals?.(rows, context, needs)
  // Schicht und Zeitraum der Einheit erscheinen in der Übersicht nur, wenn das gewählte Verfahren danach unterscheidet.
  const assignment = fieldsOf(sheet.definition).filter((field) => (needs?.stratum && field.alias === STRATUM_ALIAS) || (needs?.period && field.alias === PERIOD_ALIAS))
  const fields = [...(sheet.definition.listColumns ?? []).flatMap((cell) => findField(sheet.definition, cell) ?? []), ...assignment]
  return {
    columns: fields.map((field) => field.label),
    rows: rows.map((row) => {
      const cells = sheet.compute(row, context)
      return fields.map((field) => {
        const value = cells[field.cell] ?? null
        return typeof value === 'string' ? translateValue(sheet.texts, value) : formatFieldValue(field, value)
      })
    }),
    totals: targets.flatMap((field) => {
      const role = field.subsample
      if (!role || !totals) return []
      const value = totals.groups ? sumOf(totals.groups.filter((group) => group.period === (field.period ?? null)).map((group) => group[role])) : totals[role]
      return [{ role, label: t(TOTAL_KEYS[role]), value: formatFieldValue(field, value), target: `${field.label} (${targetOf(field)})` }]
    }),
    incomplete: totals?.incomplete ?? 0,
    unassigned: totals?.unassigned ?? 0,
    transferable: targets.length > 0,
  }
}
