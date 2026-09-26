// Anzeige des Tabellenexports (Vue und React): Texte, Zellen, Zusammenfassungen.

import { EMPTY_VALUE, formatBytes, intlFormatNumber } from '@auditcore/common'
import type { Locale, Translate } from '../i18n'
import type { ReportingMessageKey } from './messages'
import type { ReportCell, ReportTableInput, TablePreview, WorkbookPreview } from './types'

export type ReportingTranslate = Translate<ReportingMessageKey>

/** Zelle der Vorschau: Werte wie gesendet (Zahlen sprachabhängig), leer als „—“. */
export function reportCellText(value: ReportCell, locale: Locale): string {
  if (value === null || value === '') return EMPTY_VALUE
  if (typeof value === 'number') return intlFormatNumber(value, locale, { maximumFractionDigits: 10 })
  return String(value)
}

export function reportingTablesText(tables: readonly ReportTableInput[], t: ReportingTranslate, locale: Locale): string {
  if (!tables.length) return t('noTables')
  const rows = tables.reduce((sum, table) => sum + table.rows.length, 0)
  return t('tablesSummary', { tables: tables.length, rows: intlFormatNumber(rows, locale) })
}

export function reportingWorkbookText(preview: WorkbookPreview, t: ReportingTranslate, locale: Locale): string {
  if (!preview.workbook) return t('excelMissing')
  return t('workbook', { filename: preview.workbook.filename, size: formatBytes(preview.workbook.bytes, { locale }) })
}

export function reportingSheetHeading(table: TablePreview, t: ReportingTranslate, locale: Locale): string {
  return t('sheetHeading', { name: table.name, rows: intlFormatNumber(table.rows, locale) })
}

/** Hinweis, wenn die Vorschau nur einen Teil der Zeilen zeigt; sonst leer. */
export function reportingSampleNote(table: TablePreview, t: ReportingTranslate, locale: Locale): string {
  if (table.sample.length >= table.rows) return ''
  return t('sampleMore', { shown: table.sample.length, rows: intlFormatNumber(table.rows, locale) })
}

export function reportingErrorKey(error: 'noTables' | 'profile'): ReportingMessageKey {
  return error === 'noTables' ? 'errornoTables' : 'errorprofile'
}
