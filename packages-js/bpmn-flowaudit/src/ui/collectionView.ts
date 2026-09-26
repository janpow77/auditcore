/** Display logic of the collection: status badges and texts, info rows, tags. */

import { DIAGRAM_STATUS, FUND_SHORT, label, type DiagramEntry } from '../index'
import type { Translate } from './i18n/translator'

type Locale = 'de' | 'en'

export function statusBadge(entry: DiagramEntry): string {
  const status = entry.info?.status
  return status === 'freigegeben' ? 'fa-badge--success' : status === 'in_pruefung' ? 'fa-badge--info' : status === 'archiviert' ? '' : 'fa-badge--warning'
}

export function statusText(entry: DiagramEntry, t: Translate, locale: Locale): string {
  const status = entry.info?.status
  return status ? label(DIAGRAM_STATUS[status], locale) || status : t('collection.status.ohne_status')
}

export const statusLabel = (code: string, t: Translate, locale: Locale): string => (DIAGRAM_STATUS[code] ? label(DIAGRAM_STATUS[code], locale) : t(`collection.status.${code}`))

/** Key info of a diagram as term/value rows (empty values dropped). */
export function infoRows(entry: DiagramEntry, t: Translate, locale: Locale): [string, string][] {
  const info = entry.info ?? {}
  const rows: [string, string | undefined][] = [
    [t('info.field.title'), info.title],
    [t('info.field.status'), info.status ? label(DIAGRAM_STATUS[info.status], locale) : undefined],
    [t('info.field.version'), info.version],
    [t('info.field.processOwner'), info.processOwner],
    [t('info.field.programmingPeriod'), info.programmingPeriod],
    [t('info.field.funds'), (info.funds ?? []).map((code) => FUND_SHORT[code] ?? code).join(', ')],
    [t('info.field.validFrom'), [info.validFrom, info.validUntil].filter(Boolean).join(' – ')],
    [t('info.field.profile'), info.profile],
    [t('collection.overview.legal'), `${entry.excerpt.activitiesWithLegalBasis}/${entry.excerpt.activities}`],
  ]
  return rows.filter((row): row is [string, string] => Boolean(row[1]))
}

export const toggledTags = (entry: DiagramEntry, id: string): string[] => (entry.tags.includes(id) ? entry.tags.filter((tag) => tag !== id) : [...entry.tags, id])
