/**
 * Anzeige von „PDF schwärzen“ für Vue und React (reine Funktionen). Beide
 * Fassungen rendern ausschließlich aus diesen Werten; Texte nur aus
 * `redactionMessages`.
 */
import { intlFormatNumber as formatNumber } from '@auditcore/common'
import type { Locale, Translate } from '../i18n'
import type { RedactionData, RedactionValidation } from './controller'
import type { RedactionMessageKey } from './messages'
import {
  formatRedactionPages,
  normalizeRedactionText,
  redactionBoxStyle,
  redactionGroups,
  redactionGroupState,
  REDACTION_FILTER_FROM,
  REDACTION_PAGE_BUTTONS,
  type RedactionGroup,
  type RedactionGroupState,
} from './model'
import type { RedactionArea, RedactionCatalogue, RedactionPatternInfo, RedactionPlan } from './types'

export type RedactionTranslate = Translate<RedactionMessageKey>
export type RedactionStep = 'form' | 'review' | 'result'
type Style = ReturnType<typeof redactionBoxStyle>

export function redactionStep(state: RedactionData): RedactionStep {
  if (state.result) return 'result'
  return state.plan ? 'review' : 'form'
}

export function redactionSizeText(bytes: number, locale: Locale): string {
  if (bytes < 1024 * 1024) return `${formatNumber(Math.ceil(bytes / 1024), locale)} KiB`
  return `${formatNumber(bytes / (1024 * 1024), locale, { maximumFractionDigits: 1 })} MiB`
}

export function redactionPatternText(pattern: RedactionPatternInfo, t: RedactionTranslate): string {
  if (!pattern.available) return t('patternUnavailable', { label: pattern.label })
  return pattern.ai ? t('patternAi', { label: pattern.label }) : pattern.label
}

export function redactionValidationText(validation: RedactionValidation, catalogue: RedactionCatalogue | null, t: RedactionTranslate, locale: Locale): string {
  if (!validation) return ''
  const limits = catalogue?.limits
  const texts: Record<NonNullable<RedactionValidation>, () => string> = {
    needFile: () => t('errorNeedFile'),
    tooLarge: () => t('errorTooLarge', { size: redactionSizeText(limits?.max_upload_bytes ?? 0, locale) }),
    needCriteria: () => t('errorNeedCriteria'),
    tooManyTerms: () => t('errorTooManyTerms', { count: limits?.max_terms ?? 0 }),
    termTooLong: () => t('errorTermTooLong', { length: limits?.max_term_length ?? 0 }),
  }
  return texts[validation]()
}

/** Markierung einer Fundstelle auf dem Seitenbild. */
export interface RedactionBoxView {
  key: string
  id: string
  on: boolean
  label: string
  style: Style
}

export interface RedactionAreaView {
  id: string
  number: number
  label: string
  resizeLabel: string
  removeLabel: string
  style: Style
}

export interface RedactionSourceView {
  source: string
  text: string
  title: string
  state: RedactionGroupState
}

export interface RedactionItemView {
  id: string
  number: number
  checked: boolean
  label: string
  /** Seite zum Anspringen (nur Fundstellen im Seitentext). */
  page: number | null
  text: string
  extra: string
}

export interface RedactionGroupView {
  key: string
  text: string
  meta: string
  label: string
  state: RedactionGroupState
  expanded: boolean
  items: readonly RedactionItemView[]
}

export interface RedactionReviewView {
  page: number
  pageCount: number
  pageText: string
  /** Seitenverhältnis der gedrehten Seite für den Rahmen des Seitenbilds. */
  aspect: string
  boxes: readonly RedactionBoxView[]
  areas: readonly RedactionAreaView[]
  draft: Style | null
  pageButtons: readonly number[]
  morePages: boolean
  summary: string
  hasCandidates: boolean
  sources: readonly RedactionSourceView[]
  noText: string
  outside: string
  showFilter: boolean
  noMatch: string
  groups: readonly RedactionGroupView[]
  more: string
  hiddenText: string
  areaLimit: string
}

function pageAspect(plan: RedactionPlan, page: number): string {
  const info = plan.pages.find((entry) => entry.page === page)
  if (!info) return '1 / 1.414'
  const turned = info.rotation % 180 !== 0
  const [width, height] = turned ? [info.height, info.width] : [info.width, info.height]
  return `${Math.round(width * 100) / 100} / ${Math.round(height * 100) / 100}`
}

function pagesWithFindings(plan: RedactionPlan, areas: readonly RedactionArea[]): number[] {
  const pages = new Set<number>()
  for (const candidate of plan.candidates) if (candidate.kind === 'text' && candidate.page) pages.add(candidate.page)
  for (const area of areas) pages.add(area.page)
  return [...pages].sort((a, b) => a - b)
}

/** Fundorte versteckter Treffer ohne Einzelangaben („Metadaten“, „Kommentar“, …). */
export function redactionHiddenLocations(plan: RedactionPlan): string {
  const names = new Set<string>()
  for (const candidate of plan.candidates) {
    if (candidate.kind === 'hidden') names.add(candidate.location.replace(/ „.*“$/, '').replace(/ \(.*\)$/, ''))
  }
  return [...names].join(', ')
}

function sourceViews(plan: RedactionPlan, selected: ReadonlySet<string>, t: RedactionTranslate): RedactionSourceView[] {
  const counts = new Map<string, { label: string; total: number; selected: number }>()
  for (const candidate of plan.candidates) {
    const entry = counts.get(candidate.source) ?? { label: candidate.label, total: 0, selected: 0 }
    entry.total += 1
    if (selected.has(candidate.id)) entry.selected += 1
    counts.set(candidate.source, entry)
  }
  return [...counts].map(([source, entry]) => ({
    source,
    text: t('source', { label: entry.label, total: entry.total }),
    title: t('sourceTitle', { label: entry.label, selected: entry.selected, total: entry.total }),
    state: entry.selected === entry.total ? 'all' : entry.selected === 0 ? 'none' : 'some',
  }))
}

function groupView(group: RedactionGroup, state: RedactionData, t: RedactionTranslate): RedactionGroupView {
  const expanded = state.expanded.has(group.key)
  let meta = t('groupMeta', { label: group.label, count: group.items.length })
  if (group.pages.length) meta += t('groupPages', { pages: formatRedactionPages(group.pages) })
  if (group.hidden) meta += t('groupHidden')
  return {
    key: group.key,
    text: group.text,
    meta,
    label: t('group', { text: group.text, count: group.items.length }),
    state: redactionGroupState(group, state.selected),
    expanded,
    items: expanded
      ? group.items.map((item, index) => {
          const inText = item.kind === 'text'
          const page = inText && item.page ? item.page : null
          let text = ''
          if (inText && item.text !== group.text) text = item.text
          else if (!inText) text = item.page ? t('itemOnPage', { location: item.location, page: item.page }) : item.location
          return {
            id: item.id,
            number: index + 1,
            checked: state.selected.has(item.id),
            label: t('item', { location: item.location }),
            page,
            text,
            extra: inText && item.location !== 'Seitentext' ? item.location : '',
          }
        })
      : [],
  }
}

function boxViews(plan: RedactionPlan, state: RedactionData, t: RedactionTranslate): RedactionBoxView[] {
  return plan.candidates
    .filter((candidate) => candidate.kind === 'text' && candidate.page === state.page && !candidate.outside_view)
    .flatMap((candidate) => {
      const on = state.selected.has(candidate.id)
      const label = t(on ? 'boxOn' : 'boxOff', { label: candidate.label, text: candidate.text })
      return candidate.rects.map((rect, index) => ({ key: `${candidate.id}-${index}`, id: candidate.id, on, label, style: redactionBoxStyle(rect) }))
    })
}

function areaViews(state: RedactionData, t: RedactionTranslate): RedactionAreaView[] {
  return state.areas
    .filter((area) => area.page === state.page)
    .map((area) => {
      const number = state.areas.indexOf(area) + 1
      return {
        id: area.id,
        number,
        label: t('area', { number, page: area.page }),
        resizeLabel: t('areaResize', { number }),
        removeLabel: t('areaRemove', { number, page: area.page }),
        style: redactionBoxStyle(area.rect),
      }
    })
}

/** Seite, Seitenbild, Markierungen und Seitensprünge. */
function viewerPart(plan: RedactionPlan, state: RedactionData, t: RedactionTranslate) {
  const pages = pagesWithFindings(plan, state.areas)
  const limits = state.catalogue?.limits
  return {
    page: state.page,
    pageCount: plan.page_count,
    pageText: t('pageOf', { page: state.page, count: plan.page_count }),
    aspect: pageAspect(plan, state.page),
    boxes: boxViews(plan, state, t),
    areas: areaViews(state, t),
    draft: state.gesture?.kind === 'draw' ? redactionBoxStyle(state.gesture.box) : null,
    pageButtons: pages.slice(0, REDACTION_PAGE_BUTTONS),
    morePages: pages.length > REDACTION_PAGE_BUTTONS,
    areaLimit: state.areaLimitHit && limits ? t('areaLimit', { perPage: limits.max_areas_per_page, total: limits.max_areas }) : '',
  }
}

/** Gefilterte und begrenzte Gruppenliste. */
function listPart(plan: RedactionPlan, state: RedactionData, t: RedactionTranslate) {
  const groups = redactionGroups(plan.candidates)
  const needle = normalizeRedactionText(state.filter)
  const filtered = needle
    ? groups.filter((group) => normalizeRedactionText(group.text).includes(needle) || normalizeRedactionText(group.label).includes(needle))
    : groups
  const visible = filtered.slice(0, state.groupLimit)
  const rest = filtered.length - visible.length
  return {
    showFilter: groups.length > REDACTION_FILTER_FROM,
    noMatch: needle && !filtered.length ? t('noMatch', { filter: state.filter }) : '',
    groups: visible.map((group) => groupView(group, state, t)),
    more: rest > 0 ? t('more', { count: Math.min(state.groupLimit, rest) }) : '',
    hiddenText: groups.some((group) => group.hidden) ? t('hiddenText', { locations: redactionHiddenLocations(plan) }) : '',
  }
}

/** Zusammenfassung, Quellen und Hinweise über der Liste. */
function summaryPart(plan: RedactionPlan, state: RedactionData, t: RedactionTranslate) {
  const selected = plan.candidates.reduce((sum, candidate) => sum + (state.selected.has(candidate.id) ? 1 : 0), 0)
  const outside = plan.candidates.filter((candidate) => candidate.outside_view).length
  const params = { selected, total: plan.candidates.length, areas: state.areas.length }
  return {
    summary: t(state.areas.length ? 'summaryAreas' : 'summary', params),
    hasCandidates: plan.candidates.length > 0,
    sources: sourceViews(plan, state.selected, t),
    noText: plan.pages_without_text.length ? t('noText', { pages: formatRedactionPages(plan.pages_without_text) }) : '',
    outside: outside ? t('outside', { count: outside }) : '',
  }
}

/** Alles, was die Prüfansicht zeigt (nur bei vorhandenem Plan). */
export function redactionReview(state: RedactionData, t: RedactionTranslate): RedactionReviewView | null {
  const plan = state.plan
  if (!plan) return null
  return { ...viewerPart(plan, state, t), ...summaryPart(plan, state, t), ...listPart(plan, state, t) }
}

export interface RedactionReportRow {
  key: string
  label: string
  value: string
}

export function redactionReportRows(state: RedactionData, t: RedactionTranslate, locale: Locale): RedactionReportRow[] {
  const report = state.result?.report
  if (!report) return []
  const number = (value: number): string => formatNumber(value, locale)
  return [
    { key: 'redactions', label: t('reportRedactions'), value: number(report.redactions) },
    { key: 'areas', label: t('reportAreas'), value: number(report.areas) },
    { key: 'hidden', label: t('reportHidden'), value: number(report.hidden) },
    { key: 'deselected', label: t('reportDeselected'), value: number(report.deselected) },
    { key: 'pages', label: t('reportPages'), value: number(report.pages) },
    { key: 'sanitized', label: t('reportSanitized'), value: t(report.sanitized ? 'yes' : 'no') },
  ]
}
