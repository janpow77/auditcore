/**
 * Exporte aus dem View-Model, ohne Vue: eigenständiges HTML (auch als
 * Druckansicht für „Als PDF speichern“) und Markdown. Exportiert werden die
 * angezeigten Zeilen, die für die Ausgabe ausgewählt sind.
 */
import type { SynopsisTranslate, RowView, SynopsisView } from './viewModel'
import type { DiffSegment } from './wordDiff'

export interface ExportInput {
  view: SynopsisView
  rows: readonly RowView[]
  t: SynopsisTranslate
  /** Zeitpunkt der Ausgabe (Standard: jetzt), für reproduzierbare Tests injizierbar. */
  generatedAt?: string
  lang?: string
}

const HTML_ESCAPES: Record<string, string> = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }

export function escapeHtml(text: string): string {
  return text.replace(/[&<>"']/g, (char) => HTML_ESCAPES[char] ?? char)
}

export function escapeMarkdown(text: string): string {
  return text.replace(/([\\`*_[\]<>#|])/g, '\\$1')
}

export function exportFilename(title: string, extension: string): string {
  const stem = title.replace(/[^\p{L}\p{N}._-]+/gu, '_').replace(/^[._]+|[._]+$/g, '') || 'Synopse'
  return `${stem.slice(0, 80)}.${extension}`
}

function outputRows(rows: readonly RowView[]): RowView[] {
  return rows.filter((row) => row.selected)
}

function htmlSegments(segments: readonly DiffSegment[], empty: string): string {
  if (segments.length === 0) return `<span class="empty">${escapeHtml(empty)}</span>`
  return segments
    .map((segment) => {
      const text = escapeHtml(segment.text)
      if (segment.kind === 'removed') return `<del>${text}</del>`
      if (segment.kind === 'added') return `<ins>${text}</ins>`
      return text
    })
    .join('')
}

function htmlFields(row: RowView, side: 'old' | 'new'): string {
  return row.fields
    .filter((field) => field[side].length > 0)
    .map((field) => `<p class="field"><strong>${escapeHtml(field.label)}:</strong> ${htmlSegments(field[side], '')}</p>`)
    .join('')
}

function htmlRow(row: RowView, input: ExportInput, withReason: boolean): string {
  const { t } = input
  const reason = withReason ? `<td>${escapeHtml(row.reason)}</td>` : ''
  return (
    `<tr><th scope="row">${escapeHtml(row.location || '—')}<br><span class="status">${escapeHtml(row.statusLabel)}</span></th>` +
    `<td>${htmlSegments(row.old, t('emptyOld'))}${htmlFields(row, 'old')}</td>` +
    `<td>${htmlSegments(row.new, t('emptyNew'))}${htmlFields(row, 'new')}</td>${reason}</tr>`
  )
}

const HTML_STYLE = `
body{font:11pt/1.45 'IBM Plex Sans',system-ui,sans-serif;color:#1b2230;margin:2rem}
h1{font-size:16pt;margin:0 0 .5rem}p.meta{color:#5b6474;margin:.2rem 0}
.notice{border-left:4px solid #a15c07;background:#fdf1dc;padding:.5rem .75rem;margin:.75rem 0}
table{border-collapse:collapse;width:100%;margin-top:1rem}th,td{border:1px solid #a9aea4;padding:.4rem .5rem;vertical-align:top;text-align:left;white-space:pre-wrap}
thead th{background:#eceee9}.status{font-weight:400;color:#5b6474;font-size:9pt}.field{margin:.35rem 0 0;font-size:9.5pt}
del{background:#fdecea;color:#8a1c12;text-decoration:line-through}ins{background:#e3f4ea;color:#14532d;text-decoration:underline}
.empty{color:#5b6474;font-style:italic}
@media print{body{margin:0}thead{display:table-header-group}tr{break-inside:avoid}.notice{break-inside:avoid}}
`

function htmlCommands(view: SynopsisView, t: SynopsisTranslate): string {
  if (view.openCommands.length === 0) return ''
  const items = view.openCommands.map((command) => `<li>${escapeHtml(command)}</li>`).join('')
  return `<h2>${escapeHtml(t('openCommands'))}</h2><ul>${items}</ul>`
}

/** Eigenständiges HTML-Dokument mit Druck-CSS (keine externen Ressourcen). */
export function toHtml(input: ExportInput): string {
  const { view, t } = input
  const rows = outputRows(input.rows)
  const withReason = view.isArticleLaw || rows.some((row) => row.reason)
  const reasonHead = withReason ? `<th scope="col">${escapeHtml(view.reasonLabel)}</th>` : ''
  const notices = view.notices.map((notice) => `<p class="notice">${escapeHtml(notice)}</p>`).join('')
  const body = rows.length
    ? rows.map((row) => htmlRow(row, input, withReason)).join('')
    : `<tr><td colspan="${withReason ? 4 : 3}">${escapeHtml(t('noMatches'))}</td></tr>`
  const generated = t('generated', { date: input.generatedAt ?? new Date().toISOString() })
  return (
    `<!doctype html><html lang="${escapeHtml(input.lang ?? 'de')}"><head><meta charset="utf-8">` +
    `<title>${escapeHtml(view.title)}</title><style>${HTML_STYLE}</style></head><body>` +
    `<h1>${escapeHtml(view.title)}</h1><p class="meta">${escapeHtml(view.filesText)}</p>` +
    `<p class="meta">${escapeHtml(view.countsText)}</p><p class="meta">${escapeHtml(view.hashesText)}</p>` +
    `<p class="meta">${escapeHtml(generated)}</p>${notices}` +
    `<table><thead><tr><th scope="col">${escapeHtml(t('location'))}</th><th scope="col">${escapeHtml(view.oldLabel)}</th>` +
    `<th scope="col">${escapeHtml(view.newLabel)}</th>${reasonHead}</tr></thead><tbody>${body}</tbody></table>` +
    `${htmlCommands(view, t)}</body></html>`
  )
}

function markdownSegments(segments: readonly DiffSegment[], empty: string): string {
  if (segments.length === 0) return `_${escapeMarkdown(empty)}_`
  return segments
    .map((segment) => {
      const text = escapeMarkdown(segment.text)
      if (!text.trim() || segment.kind === 'same') return text
      return segment.kind === 'removed' ? `~~${text.trim()}~~` : `**${text.trim()}**`
    })
    .join('')
}

function markdownRow(row: RowView, input: ExportInput): string[] {
  const { view, t } = input
  const lines = [`### ${escapeMarkdown(row.location || '—')} (${row.statusLabel})`, '']
  lines.push(`**${view.oldLabel}:** ${markdownSegments(row.old, t('emptyOld'))}`, '')
  lines.push(`**${view.newLabel}:** ${markdownSegments(row.new, t('emptyNew'))}`, '')
  for (const field of row.fields) {
    lines.push(`- ${field.label}: ${markdownSegments(field.inline, '—')}`)
  }
  if (row.fields.length) lines.push('')
  if (row.reason) lines.push(`**${view.reasonLabel}:** ${escapeMarkdown(row.reason)}`, '')
  return lines
}

/** Markdown: gestrichene Wörter als ~~…~~, neue als **…**. */
export function toMarkdown(input: ExportInput): string {
  const { view, t } = input
  const rows = outputRows(input.rows)
  const lines = [`# ${escapeMarkdown(view.title)}`, '', `- ${escapeMarkdown(view.filesText)}`, `- ${view.countsText}`, `- ${view.hashesText}`, '']
  for (const notice of view.notices) lines.push(`> ${escapeMarkdown(notice)}`, '')
  if (rows.length === 0) lines.push(t('noMatches'), '')
  for (const row of rows) lines.push(...markdownRow(row, input))
  if (view.openCommands.length) {
    lines.push(`## ${t('openCommands')}`, '', ...view.openCommands.map((command) => `- ${escapeMarkdown(command)}`), '')
  }
  return `${lines.join('\n').trimEnd()}\n`
}
