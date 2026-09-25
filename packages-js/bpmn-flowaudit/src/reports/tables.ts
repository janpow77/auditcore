/**
 * Table output formats: CSV (UTF-8, semicolon) and MyST/Markdown pipe
 * tables, same format as `auditcore_bpmn` reports.
 */

export type Row = Record<string, unknown>
export type Columns = Record<string, string>

function columnsOf(rows: Row[], columns?: Columns): Columns {
  if (columns) return columns
  return Object.fromEntries(Object.keys(rows[0] ?? {}).map((key) => [key, key]))
}

function csvCell(value: unknown, separator: string): string {
  const text = value === null || value === undefined ? '' : String(value)
  return /["\n\r]/.test(text) || text.includes(separator) ? `"${text.replace(/"/g, '""')}"` : text
}

/** CSV with header from `columns` (or the keys); `bom` for Excel. */
export function toCsv(rows: Row[], columns?: Columns, options: { separator?: string; bom?: boolean } = {}): string {
  const separator = options.separator ?? ';'
  const cols = columnsOf(rows, columns)
  const lines = [Object.values(cols).map((title) => csvCell(title, separator)).join(separator)]
  for (const row of rows) lines.push(Object.keys(cols).map((key) => csvCell(row[key], separator)).join(separator))
  return (options.bom ? '﻿' : '') + lines.join('\n') + '\n'
}

function mystCell(value: unknown): string {
  return (value === null || value === undefined ? '' : String(value)).replace(/\|/g, '\\|').replace(/\n/g, ' ')
}

/** Table as MyST Markdown, optionally with heading and target label. */
export function toMyst(rows: Row[], columns?: Columns, options: { title?: string; label?: string } = {}): string {
  const cols = columnsOf(rows, columns)
  const lines: string[] = []
  if (options.label) lines.push(`(${options.label})=`)
  if (options.title) lines.push(`## ${options.title}`, '')
  lines.push(`| ${Object.values(cols).map(mystCell).join(' | ')} |`)
  lines.push(`|${Object.keys(cols).map(() => '---').join('|')}|`)
  for (const row of rows) lines.push(`| ${Object.keys(cols).map((key) => mystCell(row[key])).join(' | ')} |`)
  return lines.join('\n') + '\n'
}
