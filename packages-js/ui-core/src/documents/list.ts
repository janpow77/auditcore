/** Liste der gespeicherten Vergleiche (`GET /comparisons`) als reine View-Funktionen. */
import type { Comparison, ComparisonSummary } from '../synopsis/types'
import type { ComparisonsMessageKey, ComparisonsTranslate } from './messages'

export interface SummaryView {
  id: string
  title: string
  kind: string
  kindLabel: string
  files: string
  counts: string
  /** Summe der Änderungen (für Badges). */
  changes: number
  created: string
  createdIso: string
}

function kindLabel(kind: string, t: ComparisonsTranslate): string {
  const key = `kind_${kind}` as ComparisonsMessageKey
  return kind === 'standard' || kind === 'article_law' ? t(key) : kind
}

/** Datum und Uhrzeit in der Sprache der Oberfläche; ungültige Angaben bleiben stehen. */
export function formatDateTime(iso: string, lang: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  return new Intl.DateTimeFormat(lang, { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

export function summaryView(summary: ComparisonSummary, t: ComparisonsTranslate, lang: string): SummaryView {
  const counts = summary.counts
  return {
    id: summary.id,
    title: summary.title,
    kind: summary.comparison_type,
    kindLabel: kindLabel(summary.comparison_type, t),
    files: t('files', { old: summary.old_filename, new: summary.new_filename }),
    counts: t('counts', { changed: counts.changed, removed: counts.removed, added: counts.added, moved: counts.moved }),
    changes: counts.changed + counts.removed + counts.added + counts.moved,
    created: formatDateTime(summary.created_at, lang),
    createdIso: summary.created_at,
  }
}

/** Suche in Titel und Dateinamen, ohne Groß-/Kleinschreibung; neueste zuerst wie der Server. */
export function filterSummaries(items: readonly ComparisonSummary[], query: string): ComparisonSummary[] {
  const needle = query.trim().toLowerCase()
  const sorted = [...items].sort((a, b) => b.created_at.localeCompare(a.created_at))
  if (!needle) return sorted
  return sorted.filter((item) => [item.title, item.old_filename, item.new_filename].some((text) => text.toLowerCase().includes(needle)))
}

/** Eintrag der Liste aus einem gespeicherten Vergleich (nach Anlegen oder Import). */
export function summaryOf(comparison: Comparison): ComparisonSummary {
  const result = comparison.result
  return {
    id: comparison.id,
    title: comparison.title,
    created_at: comparison.created_at,
    old_filename: result.old_filename,
    new_filename: result.new_filename,
    comparison_type: result.metadata?.comparison_type ?? 'standard',
    counts: { changed: result.changed_count, removed: result.removed_count, added: result.added_count, moved: result.moved_count ?? 0 },
  }
}
