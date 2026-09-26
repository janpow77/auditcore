/**
 * Exporte des Verzeichnisses aus dem angezeigten Stand, ohne Vue: CSV mit
 * Formelschutz (`toCsv` aus @flowaudit/common, Verträge `csv-cell`/`csv-document`),
 * Markdown und eigenständiges HTML als Druckansicht („Als PDF speichern“).
 */
import { escapeHtml, toCsv } from '@flowaudit/common'
import { escapeMarkdown, exportFilename } from '../synopsis/exporters'
import { displayValue, groupByDepartment } from './registerView'
import type { RegisterColumn, FieldValue, Issue, RegisterContent } from './types'

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
  return toCsv([titles, ...rows])
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

const escape = (value: string): string => escapeHtml(value)

function coverHtml(input: RegisterExportInput): string[] {
  const { content, texts } = input
  return [
    `<h1>${escape(texts.title)}</h1>`, `<p>${escape(input.versionLabel)}</p>`, '<table>',
    `<tr><th scope="row">${escape(texts.controller)}</th><td>${escape(content.deckblatt.verantwortlicher?.name || texts.empty)}</td></tr>`,
    `<tr><th scope="row">${escape(texts.dpo)}</th><td>${escape(content.deckblatt.dsb?.name || texts.empty)}</td></tr></table>`,
  ]
}

function activitiesHtml(input: RegisterExportInput): string[] {
  const { content, columns, texts } = input
  const parts: string[] = []
  for (const group of groupByDepartment(content)) {
    parts.push(`<h2>${escape(group.department || texts.withoutDepartment)}</h2>`)
    for (const { activity } of group.items) {
      parts.push(`<h3>${escape(cell(activity.name, texts))}</h3><table>`)
      for (const column of columns) {
        parts.push(`<tr><th scope="row">${escape(column.title)}</th><td>${escape(cell(activity[column.key], texts))}</td></tr>`)
      }
      parts.push('</table>')
    }
  }
  return parts
}

function issuesHtml({ issues, texts }: RegisterExportInput): string[] {
  const items = issues.length
    ? issues.map((issue) => `<li class="${issue.blocking ? 'required' : 'hint'}">${escape(issueLine(issue, texts))}</li>`)
    : [`<li>${escape(texts.noIssues)}</li>`]
  return [`<h2>${escape(texts.issues)}</h2><ul class="issues">`, ...items, '</ul>']
}

export function registerHtml(input: RegisterExportInput): string {
  const { texts } = input
  const parts = [...coverHtml(input), ...activitiesHtml(input), ...issuesHtml(input)]
  if (input.generatedAt) parts.push(`<footer>${escape(texts.generated)} ${escape(input.generatedAt)}</footer>`)
  return `<!DOCTYPE html><html lang="${escape(input.lang ?? 'de')}"><head><meta charset="utf-8"><title>${escape(texts.title)}</title>` +
    `<style>${PRINT_CSS}</style></head><body>${parts.join('')}</body></html>`
}

export function registerFilename(version: number | null, extension: string): string {
  return exportFilename(`Verarbeitungsverzeichnis${version ? `_Fassung_${version}` : ''}`, extension)
}
