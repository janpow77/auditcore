/**
 * Exporte des Verzeichnisses aus dem angezeigten Stand, ohne Vue: CSV mit
 * Formelschutz (Verträge `csv-cell`/`csv-document` in contracts/common-cases),
 * Markdown und eigenständiges HTML als Druckansicht („Als PDF speichern“).
 * csvCell/csvDocument wandern nach @flowaudit/common, sobald es veröffentlicht ist.
 */
import { escapeHtml, escapeMarkdown, exportFilename } from '../synopsis/exporters'
import { displayValue, groupByDepartment } from './registerView'
import type { RegisterColumn, FieldValue, Issue, RegisterContent } from './types'

const FORMULA_START = /^[=+\-@\t\r]/
const NEEDS_QUOTES = /[;"\n\r]/

export interface ExportTexts {
  yes: string
  no: string
  empty: string
  title: string
  department: string
  withoutDepartment: string
  controller: string
  dpo: string
  version: string
  issues: string
  noIssues: string
  required: string
  hint: string
  field: string
  content: string
  generated: string
}

export interface RegisterExportInput {
  content: RegisterContent
  columns: readonly RegisterColumn[]
  issues: readonly Issue[]
  /** Zeile unter dem Titel, z. B. „Fassung 2 – Entwurf“. */
  versionLabel: string
  texts: ExportTexts
  lang?: string
  generatedAt?: string
}

/** Eine CSV-Zelle für Excel-DE (Trenner „;“, Formelschutz, Zahlen mit Dezimalkomma). */
export function csvCell(value: string | number | boolean | null | undefined, yes = 'ja', no = 'nein'): string {
  if (value === null || value === undefined) return ''
  if (typeof value === 'boolean') return value ? yes : no
  if (typeof value === 'number') return String(value).replace('.', ',')
  const text = FORMULA_START.test(value) ? `'${value}` : value
  return NEEDS_QUOTES.test(text) ? `"${text.replace(/"/g, '""')}"` : text
}

/** Ganze CSV-Datei: BOM, Zellen nach `csvCell`, Zeilenende CRLF. */
export function csvDocument(rows: readonly (readonly (string | number | boolean | null | undefined)[])[]): string {
  return '﻿' + rows.map((row) => row.map((cell) => csvCell(cell)).join(';') + '\r\n').join('')
}

function cell(value: FieldValue | undefined, texts: ExportTexts): string {
  return displayValue(value, texts)
}

export function registerCsv(input: RegisterExportInput): string {
  const { content, columns, texts } = input
  const keys = ['referat', ...columns.map((column) => column.key).filter((key) => key !== 'referat')]
  const titles = keys.map((key) => columns.find((column) => column.key === key)?.title ?? texts.department)
  const rows = content.taetigkeiten.map((activity) => keys.map((key) => {
    const value = activity[key]
    return typeof value === 'boolean' ? (value ? texts.yes : texts.no) : value
  }))
  return csvDocument([titles, ...rows])
}

function issueLine(issue: Issue, texts: ExportTexts): string {
  return `${issue.blocking ? texts.required : texts.hint}: ${issue.message}`
}

export function registerMarkdown(input: RegisterExportInput): string {
  const { content, columns, issues, texts } = input
  const md = (value: string): string => escapeMarkdown(value.replace(/\s+/g, ' ').trim())
  const lines = [`# ${texts.title}`, '', md(input.versionLabel), '']
  lines.push(`- ${texts.controller}: ${md(content.deckblatt.verantwortlicher?.name || texts.empty)}`)
  lines.push(`- ${texts.dpo}: ${md(content.deckblatt.dsb?.name || texts.empty)}`)
  for (const group of groupByDepartment(content)) {
    lines.push('', `## ${md(group.department || texts.withoutDepartment)}`)
    for (const { activity } of group.items) {
      lines.push('', `### ${md(cell(activity.name, texts))}`, '', `| ${texts.field} | ${texts.content} |`, '|---|---|')
      for (const column of columns) lines.push(`| ${md(column.title)} | ${md(cell(activity[column.key], texts))} |`)
    }
  }
  lines.push('', `## ${texts.issues}`, '')
  lines.push(...(issues.length ? issues.map((issue) => `- ${md(issueLine(issue, texts))}`) : [`- ${texts.noIssues}`]))
  return lines.join('\n') + '\n'
}

const PRINT_CSS = `body{font:11pt/1.4 system-ui,sans-serif;color:#111;margin:2rem}
h1{font-size:16pt}h2{font-size:13pt;margin-top:1.5rem}h3{font-size:11pt;margin:1rem 0 .25rem}
table{border-collapse:collapse;width:100%;margin-bottom:.75rem}th,td{border:1px solid #999;padding:.25rem .4rem;text-align:left;vertical-align:top}
th{width:32%;background:#f0f0f0}.issues li.required{color:#8a1c12}footer{margin-top:2rem;font-size:9pt;color:#555}
@media print{h3{break-after:avoid}table{break-inside:auto}tr{break-inside:avoid}}`

export function registerHtml(input: RegisterExportInput): string {
  const { content, columns, issues, texts } = input
  const e = (value: string): string => escapeHtml(value)
  const parts = [`<h1>${e(texts.title)}</h1>`, `<p>${e(input.versionLabel)}</p>`, '<table>']
  parts.push(`<tr><th scope="row">${e(texts.controller)}</th><td>${e(content.deckblatt.verantwortlicher?.name || texts.empty)}</td></tr>`)
  parts.push(`<tr><th scope="row">${e(texts.dpo)}</th><td>${e(content.deckblatt.dsb?.name || texts.empty)}</td></tr></table>`)
  for (const group of groupByDepartment(content)) {
    parts.push(`<h2>${e(group.department || texts.withoutDepartment)}</h2>`)
    for (const { activity } of group.items) {
      parts.push(`<h3>${e(cell(activity.name, texts))}</h3><table>`)
      for (const column of columns) {
        parts.push(`<tr><th scope="row">${e(column.title)}</th><td>${e(cell(activity[column.key], texts))}</td></tr>`)
      }
      parts.push('</table>')
    }
  }
  parts.push(`<h2>${e(texts.issues)}</h2><ul class="issues">`)
  parts.push(...(issues.length
    ? issues.map((issue) => `<li class="${issue.blocking ? 'required' : 'hint'}">${e(issueLine(issue, texts))}</li>`)
    : [`<li>${e(texts.noIssues)}</li>`]))
  parts.push('</ul>')
  if (input.generatedAt) parts.push(`<footer>${e(texts.generated)} ${e(input.generatedAt)}</footer>`)
  return `<!DOCTYPE html><html lang="${e(input.lang ?? 'de')}"><head><meta charset="utf-8"><title>${e(texts.title)}</title>` +
    `<style>${PRINT_CSS}</style></head><body>${parts.join('')}</body></html>`
}

export function registerFilename(version: number | null, extension: string): string {
  return exportFilename(`Verarbeitungsverzeichnis${version ? `_Fassung_${version}` : ''}`, extension)
}
