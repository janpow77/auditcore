/**
 * Grouping of the diagram list into a collapsible tree, ported from
 * `diagrammBaum.ts` of the audit_designer (`baueGruppen` → `buildGroups`).
 * Groups by fields maintained anyway at the diagram: process type or
 * responsibility. „Ohne Zuordnung“ is always last.
 */

export type Grouping = 'prozesstyp' | 'verantwortlich' | 'keine'
export type ListFilter = 'alle' | 'eigene' | 'geteilt' | 'oeffentlich'

/** Fields of a list item as delivered by the audit_designer API. */
export interface LegacyListItem {
  id: number | string
  name: string
  description?: string | null
  process_type?: string | null
  process_owner?: string | null
  owner?: string | null
  is_public?: boolean
}

export interface Group<T extends LegacyListItem = LegacyListItem> {
  key: string
  label: string
  entries: T[]
}

export interface TreeOptions<T extends LegacyListItem> {
  search: string
  filter: ListFilter
  grouping: Grouping
  isOwn: (item: T) => boolean
}

export const WITHOUT_ASSIGNMENT = 'Ohne Zuordnung'

function groupLabel(item: LegacyListItem, grouping: Grouping): string {
  if (grouping === 'prozesstyp') return (item.process_type ?? '').trim() || WITHOUT_ASSIGNMENT
  if (grouping === 'verantwortlich') return (item.process_owner ?? '').trim() || (item.owner ?? '').trim() || WITHOUT_ASSIGNMENT
  return ''
}

const FILTERS: Record<ListFilter, <T extends LegacyListItem>(item: T, isOwn: (item: T) => boolean) => boolean> = {
  alle: () => true,
  eigene: (item, isOwn) => isOwn(item),
  oeffentlich: (item) => Boolean(item.is_public),
  geteilt: (item, isOwn) => !isOwn(item) && !item.is_public,
}

/** Filters, searches and groups in one pass. */
export function buildGroups<T extends LegacyListItem>(items: T[], options: TreeOptions<T>): Group<T>[] {
  const term = options.search.trim().toLowerCase()
  const list = items
    .filter((item) => FILTERS[options.filter](item, options.isOwn))
    .filter((item) => !term || item.name.toLowerCase().includes(term) || (item.description ?? '').toLowerCase().includes(term))
  if (options.grouping === 'keine') return list.length ? [{ key: 'alle', label: 'Alle Diagramme', entries: list }] : []
  const byLabel = new Map<string, T[]>()
  for (const item of list) {
    const labelText = groupLabel(item, options.grouping)
    byLabel.set(labelText, [...(byLabel.get(labelText) ?? []), item])
  }
  return [...byLabel.entries()]
    .map(([labelText, entries]) => ({ key: `${options.grouping}:${labelText}`, label: labelText, entries }))
    .sort((a, b) => {
      if (a.label === WITHOUT_ASSIGNMENT) return 1
      if (b.label === WITHOUT_ASSIGNMENT) return -1
      return a.label.localeCompare(b.label, 'de')
    })
}
