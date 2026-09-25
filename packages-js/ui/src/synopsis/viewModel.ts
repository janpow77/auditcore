/**
 * Framework-freie Anzeige-Logik der Synopse: aus einem `ComparisonResult`
 * entsteht ein View-Model mit Beschriftungen, Wortsegmenten je Seite,
 * Filter und Navigation. Vue-Komponenten und Exporte nutzen nur dieses Modell.
 */
import type { MessageParams } from '../i18n/i18n'
import type { SynopsisMessageKey } from './messages'
import { CHANGE_STATUSES, type CompareRow, type ComparisonResult, type ConsolidatedParagraph, type DiffField, type RowStatus } from './types'
import { diffSegments, plainSegments, wholeSegments, type DiffSegment } from './wordDiff'

export type SynopsisTranslate = (key: SynopsisMessageKey, params?: MessageParams) => string

export interface FieldView {
  field: Exclude<DiffField, 'text'>
  label: string
  old: DiffSegment[]
  new: DiffSegment[]
  inline: DiffSegment[]
}

export interface RowView {
  id: string
  status: RowStatus | string
  statusLabel: string
  location: string
  old: DiffSegment[]
  new: DiffSegment[]
  inline: DiffSegment[]
  fields: FieldView[]
  reason: string
  reasonSource: string
  reasonVerified: boolean | null
  reasonWarning: string
  selected: boolean
  isChange: boolean
  /** Suchtext: Fundstelle, beide Fassungen, Nebenfelder und Grund, kleingeschrieben. */
  haystack: string
}

export interface SynopsisView {
  title: string
  oldLabel: string
  newLabel: string
  reasonLabel: string
  isArticleLaw: boolean
  countsText: string
  detectedText: string
  filesText: string
  hashesText: string
  createdAt: string
  notices: string[]
  recognisedCommands: number
  openCommands: string[]
  consolidated: readonly ConsolidatedParagraph[]
  rows: RowView[]
}

export interface ViewOptions {
  title?: string
  oldLabel?: string
  newLabel?: string
  /** Wortweise Hervorhebung; ohne sie bleiben Texte unmarkiert. */
  highlight?: boolean
}

const STATUS_KEYS: Record<RowStatus, SynopsisMessageKey> = {
  changed: 'statusChanged',
  removed: 'statusRemoved',
  added: 'statusAdded',
  moved: 'statusMoved',
  unchanged: 'statusUnchanged',
}

const FIELDS: ReadonlyArray<[Exclude<DiffField, 'text'>, SynopsisMessageKey]> = [
  ['answer', 'fieldAnswer'],
  ['comment', 'fieldComment'],
  ['note', 'fieldNote'],
]

export function statusLabel(status: string, t: SynopsisTranslate): string {
  const key = STATUS_KEYS[status as RowStatus]
  return key ? t(key) : status
}

interface Sides {
  old: DiffSegment[]
  new: DiffSegment[]
  inline: DiffSegment[]
}

function sides(oldText: string, newText: string, status: string, ndiff: readonly string[] | undefined, highlight: boolean): Sides {
  if (!highlight || oldText === newText) {
    const inline = oldText === newText ? plainSegments(newText) : wholeSegments(oldText, newText)
    return { old: plainSegments(oldText), new: plainSegments(newText), inline }
  }
  if (status === 'added' || status === 'removed' || !oldText || !newText) {
    return { old: plainSegments(oldText), new: plainSegments(newText), inline: wholeSegments(oldText, newText) }
  }
  return {
    old: diffSegments(oldText, newText, 'old', ndiff),
    new: diffSegments(oldText, newText, 'new', ndiff),
    inline: diffSegments(oldText, newText, 'inline', ndiff),
  }
}

function fieldValue(row: CompareRow, side: 'old' | 'new', field: Exclude<DiffField, 'text'>): string {
  return row[`${side}_${field}`] ?? ''
}

function fieldViews(row: CompareRow, highlight: boolean, t: SynopsisTranslate): FieldView[] {
  const views: FieldView[] = []
  for (const [field, key] of FIELDS) {
    const oldValue = fieldValue(row, 'old', field)
    const newValue = fieldValue(row, 'new', field)
    if (!oldValue && !newValue) continue
    views.push({ field, label: t(key), ...sides(oldValue, newValue, row.status, row.diff?.[field], highlight) })
  }
  return views
}

function haystack(row: CompareRow): string {
  const parts = [row.location, row.old_text, row.new_text, row.reason ?? '']
  for (const [field] of FIELDS) parts.push(fieldValue(row, 'old', field), fieldValue(row, 'new', field))
  return parts.join('\n').toLocaleLowerCase('de')
}

export function buildRowView(row: CompareRow, highlight: boolean, t: SynopsisTranslate): RowView {
  return {
    id: row.row_id,
    status: row.status,
    statusLabel: statusLabel(row.status, t),
    location: row.location,
    ...sides(row.old_text, row.new_text, row.status, row.diff?.text, highlight),
    fields: fieldViews(row, highlight, t),
    reason: row.reason ?? '',
    reasonSource: row.reason_source ?? '',
    reasonVerified: row.reason_verified ?? null,
    reasonWarning: row.reason_warning ?? '',
    selected: row.selected ?? true,
    isChange: (CHANGE_STATUSES as readonly string[]).includes(row.status),
    haystack: haystack(row),
  }
}

function modeLabel(mode: string, t: SynopsisTranslate): string {
  if (mode === 'checklist') return t('modeChecklist')
  if (mode === 'text') return t('modeText')
  return mode
}

function notices(result: ComparisonResult, t: SynopsisTranslate): string[] {
  const meta = result.metadata ?? {}
  const list = [t('workAid')]
  for (const value of [meta.work_aid_notice, meta.pdf_notice]) {
    if (typeof value === 'string' && value) list.push(value)
  }
  return list
}

function countsText(result: ComparisonResult, t: SynopsisTranslate): string {
  return t('counts', {
    changed: result.changed_count,
    removed: result.removed_count,
    added: result.added_count,
    moved: result.moved_count ?? 0,
    matched: result.matched_count,
  })
}

type Labels = Pick<SynopsisView, 'title' | 'oldLabel' | 'newLabel' | 'reasonLabel'>

function labels(result: ComparisonResult, t: SynopsisTranslate, options: ViewOptions): Labels {
  const meta = result.metadata ?? {}
  return {
    title: options.title || t('files', { old: result.old_filename, new: result.new_filename }),
    oldLabel: options.oldLabel || meta.old_label || t('oldLabel'),
    newLabel: options.newLabel || meta.new_label || t('newLabel'),
    reasonLabel: meta.reason_label || t('reasonLabel'),
  }
}

export function buildSynopsisView(result: ComparisonResult, t: SynopsisTranslate, options: ViewOptions = {}): SynopsisView {
  const meta = result.metadata ?? {}
  const highlight = options.highlight ?? meta.highlight_words ?? true
  return {
    ...labels(result, t, options),
    isArticleLaw: meta.comparison_type === 'article_law',
    countsText: countsText(result, t),
    detectedText: t('detected', { mode: modeLabel(result.mode, t), version: result.version }),
    filesText: t('files', { old: result.old_filename, new: result.new_filename }),
    hashesText: t('hashes', { old: result.old_sha256 || '–', new: result.new_sha256 || '–' }),
    createdAt: result.created_at,
    notices: notices(result, t),
    recognisedCommands: meta.recognised_commands ?? 0,
    openCommands: [...(meta.open_commands ?? [])],
    consolidated: meta.consolidated_text ?? [],
    rows: result.rows.map((row) => buildRowView(row, highlight, t)),
  }
}

export interface SynopsisRowFilter {
  statuses: readonly string[]
  query: string
  onlySelected: boolean
}

export const DEFAULT_SYNOPSIS_FILTER: SynopsisRowFilter = { statuses: CHANGE_STATUSES, query: '', onlySelected: false }

export function filterRows(rows: readonly RowView[], filter: SynopsisRowFilter): RowView[] {
  const query = filter.query.trim().toLocaleLowerCase('de')
  return rows.filter(
    (row) =>
      filter.statuses.includes(row.status) &&
      (!filter.onlySelected || row.selected) &&
      (!query || row.haystack.includes(query)),
  )
}

/** Kennungen der Änderungszeilen in Anzeigereihenfolge (Ziel der Navigation). */
export function changeIds(rows: readonly RowView[]): string[] {
  return rows.filter((row) => row.isChange).map((row) => row.id)
}

/**
 * Nächste bzw. vorige Änderung; ohne aktuelle Position beginnt `+1` bei der
 * ersten und `-1` bei der letzten. Am Rand bleibt die Position stehen.
 */
export function stepChange(ids: readonly string[], current: string | null, direction: 1 | -1): string | null {
  if (ids.length === 0) return null
  const index = current === null ? -1 : ids.indexOf(current)
  if (index === -1) return direction === 1 ? (ids[0] ?? null) : (ids[ids.length - 1] ?? null)
  const next = Math.min(ids.length - 1, Math.max(0, index + direction))
  return ids[next] ?? null
}

export function positionText(ids: readonly string[], current: string | null, t: SynopsisTranslate): string {
  const index = current === null ? -1 : ids.indexOf(current)
  if (index === -1) return t('positionNone', { total: ids.length })
  return t('position', { current: index + 1, total: ids.length })
}

/** Zeilen mit lokalen Änderungen (Auswahl, Grund) zusammenführen. */
export function applyRowOverrides(rows: readonly CompareRow[], overrides: ReadonlyMap<string, Partial<CompareRow>>): CompareRow[] {
  if (overrides.size === 0) return [...rows]
  return rows.map((row) => {
    const patch = overrides.get(row.row_id)
    return patch ? { ...row, ...patch } : row
  })
}
