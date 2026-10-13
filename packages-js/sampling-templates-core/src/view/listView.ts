/** Anzeigemodell eines Listenblatts (Blatt 17): Übersicht der Einheiten und Summen für das Methodenblatt. */
import { formatFieldValue } from '../format/numbers'
import type { MessageKey, Translate } from '../i18n/messages'
import { findField, type SubsampleRole } from '../model/definition'
import { subsampleTargets } from '../model/list'
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
  /** Das Methodenblatt hat Felder, die Summen aufnehmen. */
  transferable: boolean
}

const TOTAL_KEYS: Readonly<Record<SubsampleRole, MessageKey>> = {
  highValueErrors: 'totalHighValueErrors',
  errorRateSum: 'totalErrorRateSum',
  errorSum: 'totalErrorSum',
  bookValueSum: 'totalBookValueSum',
}

/** Übersicht der Einheiten und die Summen, die das Methodenblatt `method` übernehmen kann. */
export function buildListView(sheet: AvailableSheet, rows: readonly CellMap[], method: AvailableSheet | null, context: SheetContext, t: Translate): ListView {
  const fields = (sheet.definition.listColumns ?? []).flatMap((cell) => findField(sheet.definition, cell) ?? [])
  const totals: SubsampleTotals | undefined = sheet.totals?.(rows, context)
  const targets = method ? subsampleTargets(method.definition) : []
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
      return [{ role, label: t(TOTAL_KEYS[role]), value: formatFieldValue(field, totals[role]), target: `${field.label} (${field.cell})` }]
    }),
    incomplete: totals?.incomplete ?? 0,
    transferable: targets.length > 0,
  }
}
