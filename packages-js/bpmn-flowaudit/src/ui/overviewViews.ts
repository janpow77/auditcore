/**
 * Views of the folder overview: tiles (cards with their diagrams), list
 * (one row per diagram with key facts) and thumbnails (a small picture per
 * diagram). The choice is kept per browser.
 */

import type { CardDiagram } from '../collection/cards'
import type { Translate } from './i18n/translator'
import { browserStorage, readChoice, writePreference, type PreferenceStorage } from './preferences'

export const OVERVIEW_VIEWS = ['tiles', 'list', 'thumbnails'] as const
export type OverviewView = (typeof OVERVIEW_VIEWS)[number]
export const OVERVIEW_VIEW_KEY = 'auditcore.bpmn.overviewView'

/** Views on offer: thumbnails only when the host can render or deliver them. */
export const overviewViews = (thumbnails: boolean): OverviewView[] => OVERVIEW_VIEWS.filter((view) => thumbnails || view !== 'thumbnails')

export function readOverviewView(thumbnails: boolean, storage: PreferenceStorage | null = browserStorage()): OverviewView {
  return readChoice(OVERVIEW_VIEW_KEY, overviewViews(thumbnails), 'tiles', storage)
}

export function writeOverviewView(view: OverviewView, storage: PreferenceStorage | null = browserStorage()): void {
  writePreference(OVERVIEW_VIEW_KEY, view, storage)
}

/** Share of activities with a legal basis, `null` without activities. */
export const legalShare = (diagram: CardDiagram): number | null => (diagram.activities ? Math.round((diagram.withLegalBasis / diagram.activities) * 100) : null)

/** Facts of a list row: activities, legal basis share, date (missing ones dropped). */
export function diagramFacts(diagram: CardDiagram, t: Translate, locale: 'de' | 'en'): string[] {
  const share = legalShare(diagram)
  const facts = [t('collection.overview.activities', { count: diagram.activities })]
  if (share !== null) facts.push(t('collection.overview.legalShare', { percent: share }))
  if (diagram.date) facts.push(formatDate(diagram.date, locale))
  return facts
}

function formatDate(value: string, locale: 'de' | 'en'): string {
  const date = new Date(`${value.slice(0, 10)}T00:00:00Z`)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString(locale === 'de' ? 'de-DE' : 'en-GB', { timeZone: 'UTC' })
}

/** Cards with many diagrams take the whole row so long names stay readable. */
export const isWideCard = (count: number, cards: number): boolean => cards === 1 || count > 3
