// Framework-freie View-Logik der Screening-Trefferprüfung: Filter, Formatierung,
// Vergleichszeilen, Aufschlüsselung, Entscheidungsregeln. Keine Vue-Abhängigkeit.

import { formatNumber, type Locale, type MessageParams } from '../i18n'
import { codeLabel, type ScreeningKey, type ScreeningTranslate } from './messages'
import type {
  Breakdown,
  FindingView,
  FreshnessStatus,
  HitView,
  Outcome,
  ReviewStatus,
  ReviewView,
  RunView,
  SettingsView,
  SubjectRequest,
  SubjectView,
} from './types'

export interface HitFilter {
  statuses: ReviewStatus[]
  lists: string[]
  subjects: string[]
  confidences: string[]
  minScore: number | null
  text: string
}

export function emptyFilter(): HitFilter {
  return { statuses: [], lists: [], subjects: [], confidences: [], minScore: null, text: '' }
}

function matchesText(hit: HitView, text: string): boolean {
  if (!text) return true
  const needle = text.toLocaleLowerCase('de')
  const haystack = [hit.entry.name, hit.matched_name, ...hit.entry.aliases, hit.list_name]
  return haystack.some((value) => value.toLocaleLowerCase('de').includes(needle))
}

export function acceptsHit(hit: HitView, filter: HitFilter): boolean {
  const checks: [string[], string][] = [
    [filter.statuses, hit.review.status],
    [filter.lists, hit.list_key],
    [filter.subjects, hit.subject_id],
    [filter.confidences, hit.confidence],
  ]
  if (checks.some(([allowed, value]) => allowed.length > 0 && !allowed.includes(value))) return false
  if (filter.minScore !== null && hit.score < filter.minScore) return false
  return matchesText(hit, filter.text.trim())
}

/** Subjects with only the hits passing the filter; subjects themselves stay visible. */
export function filterSubjects(subjects: SubjectView[], filter: HitFilter): SubjectView[] {
  return subjects.map((subject) => ({
    ...subject,
    hits: subject.hits.filter((hit) => acceptsHit(hit, filter)),
  }))
}

export interface FilterOptions {
  lists: { key: string; name: string }[]
  subjects: { id: string; name: string }[]
  confidences: string[]
}

export function filterOptions(run: RunView): FilterOptions {
  const lists = new Map<string, string>()
  const confidences = new Set<string>()
  for (const subject of run.subjects) {
    for (const finding of subject.findings) lists.set(finding.list_key, finding.list_name)
    for (const hit of subject.hits) confidences.add(hit.confidence)
  }
  return {
    lists: [...lists].map(([key, name]) => ({ key, name })),
    subjects: run.subjects.map((s) => ({ id: s.subject_id, name: s.input.name })),
    confidences: [...confidences],
  }
}

const decimals = (scale: { max: number }): number => (scale.max <= 1 ? 2 : 1)

export function formatScore(value: number, scale: { max: number }, locale: Locale = 'de'): string {
  const digits = decimals(scale)
  return formatNumber(value, locale, { minimumFractionDigits: digits, maximumFractionDigits: digits })
}

export function formatPoints(value: number, scale: { max: number }, locale: Locale = 'de'): string {
  const text = formatScore(Math.abs(value), scale, locale)
  if (value > 0) return `+${text}`
  return value < 0 ? `−${text}` : text
}

export function scorePercent(value: number, scale: { min: number; max: number }): number {
  const span = scale.max - scale.min
  if (span <= 0) return 0
  return Math.max(0, Math.min(100, ((value - scale.min) / span) * 100))
}

export type Tone = 'plus' | 'minus' | 'neutral' | 'result'

export interface BreakdownRow {
  label: string
  value: string
  points: string
  tone: Tone
}

function stepTone(step: Breakdown['steps'][number]): Tone {
  if (step.step === 'result') return 'result'
  if (step.points === undefined || step.step === 'base') return 'neutral'
  if (step.points > 0) return 'plus'
  return step.points < 0 ? 'minus' : 'neutral'
}

export function breakdownRows(breakdown: Breakdown, locale: Locale = 'de'): BreakdownRow[] {
  return breakdown.steps.map((step) => {
    const isDelta = step.step === 'adjustment' || step.step === 'clamp'
    const points =
      step.points === undefined
        ? ''
        : isDelta
          ? formatPoints(step.points, breakdown.scale, locale)
          : formatScore(step.points, breakdown.scale, locale)
    const value = step.value !== undefined ? `„${step.value}“` : ''
    return { label: step.label, value: [value, step.detail ?? ''].filter(Boolean).join(' · '), points, tone: stepTone(step) }
  })
}

const DATE = /^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}))?/

export function formatDate(value: string | null | undefined): string {
  if (!value) return '–'
  const match = DATE.exec(value)
  if (!match) return value
  const [, year, month, day, hour, minute] = match
  const date = `${day}.${month}.${year}`
  return hour !== undefined && minute !== undefined ? `${date}, ${hour}:${minute}` : date
}

export function freshnessTone(status: FreshnessStatus): 'ok' | 'warn' | 'muted' {
  if (status === 'current') return 'ok'
  return status === 'not_judged' ? 'muted' : 'warn'
}

export function formatAge(days: number | null, t: ScreeningTranslate): string {
  if (days === null) return t('ageUnknown')
  if (days < 1) return t('ageToday')
  const rounded = Math.round(days)
  return rounded === 1 ? t('ageOne') : t('ageDays', { days: rounded })
}

export type MatchState = 'match' | 'conflict' | 'not_compared' | 'info'

export interface ComparisonRow {
  label: string
  input: string
  entry: string
  state: MatchState
}

function compareState(hit: HitView, conflict: boolean, notCompared: string): MatchState {
  if (hit.indicators.includes(notCompared)) return 'not_compared'
  return conflict ? 'conflict' : 'match'
}

const orDash = (value: string | null | undefined): string => (value && value.trim() ? value : '–')

export function comparisonRows(subject: SubjectView, hit: HitView, t: ScreeningTranslate): ComparisonRow[] {
  const entry = hit.entry
  const finding = subject.findings.find((f) => f.list_key === hit.list_key)
  const aliases = entry.aliases.length ? entry.aliases.join('; ') : '–'
  const more = entry.aliases_total > entry.aliases.length ? ` (+${entry.aliases_total - entry.aliases.length})` : ''
  return [
    { label: t('rowName'), input: subject.input.name, entry: entry.name, state: 'info' },
    { label: t('rowMatched'), input: subject.normalized_query, entry: hit.matched_name, state: 'info' },
    { label: t('rowAliases'), input: '–', entry: aliases + more, state: 'info' },
    {
      label: t('rowBirth'),
      input: orDash(subject.input.birth_date),
      entry: orDash(entry.birth_date),
      state: compareState(hit, hit.dob_conflict, 'date_of_birth_not_compared'),
    },
    {
      label: t('rowCountry'),
      input: orDash(subject.input.country),
      entry: orDash(entry.countries),
      state: compareState(hit, hit.country_conflict, 'country_not_compared'),
    },
    { label: t('rowAddress'), input: '–', entry: orDash(entry.addresses), state: 'info' },
    { label: t('rowIdentifiers'), input: '–', entry: orDash(entry.identifiers), state: 'info' },
    { label: t('rowProgram'), input: '–', entry: orDash(entry.sanctions), state: 'info' },
    { label: t('rowList'), input: '–', entry: `${hit.list_name} (${entry.entry_id})`, state: 'info' },
    { label: t('rowAsOf'), input: '–', entry: findingState(finding, t), state: 'info' },
  ]
}

function findingState(finding: FindingView | undefined, t: ScreeningTranslate): string {
  if (!finding) return '–'
  return finding.as_of ? formatDate(finding.as_of) : t('asOfUnknown')
}

export function indicatorLabels(hit: HitView, t: ScreeningTranslate): string[] {
  return hit.indicators.map((code) => codeLabel(t, 'indicator', code))
}

export function requiresFourEyes(outcome: Outcome, settings: SettingsView | null): boolean {
  return settings !== null && settings.four_eyes_outcomes.includes(outcome)
}

export const canDecide = (review: ReviewView): boolean => review.status === 'open' || review.status === 'deferred'
export const awaitsSecondReview = (review: ReviewView): boolean => review.status === 'pending_second_review'

export interface DecisionForm {
  outcome: Outcome | null
  reason: string
  fourEyes: boolean
}

/** Meldung als Katalogschlüssel mit Platzhaltern; die Komponente übersetzt sie. */
export interface ViewMessage {
  key: ScreeningKey
  params?: MessageParams
}

export function validateDecision(form: DecisionForm): ViewMessage[] {
  const errors: ViewMessage[] = []
  if (form.outcome === null) errors.push({ key: 'errorOutcome' })
  if (!form.reason.trim()) errors.push({ key: 'errorReason' })
  if (form.reason.length > 4000) errors.push({ key: 'errorReasonLength' })
  return errors
}

/** The next hit still needing work after ``currentId`` (open, deferred or pending). */
export function nextOpenHit(subjects: SubjectView[], currentId: string | null): string | null {
  const hits = subjects.flatMap((s) => s.hits)
  const start = currentId === null ? 0 : hits.findIndex((h) => h.hit_id === currentId) + 1
  const ordered = [...hits.slice(start), ...hits.slice(0, start)]
  const next = ordered.find((h) => h.hit_id !== currentId && h.review.status !== 'confirmed' && h.review.status !== 'dismissed')
  return next ? next.hit_id : null
}

export function findHit(run: RunView | null, hitId: string | null): { subject: SubjectView; hit: HitView } | null {
  if (!run || !hitId) return null
  for (const subject of run.subjects) {
    const hit = subject.hits.find((h) => h.hit_id === hitId)
    if (hit) return { subject, hit }
  }
  return null
}

/** One subject per line: ``Name; Geburtsdatum; Land; Bezug`` (only the name is required). */
export function parseSubjects(text: string): { subjects: SubjectRequest[]; errors: ViewMessage[] } {
  const subjects: SubjectRequest[] = []
  const errors: ViewMessage[] = []
  text.split(/\r?\n/).forEach((line, index) => {
    if (!line.trim()) return
    const [name = '', birthDate = '', country = '', reference = ''] = line.split(';').map((p) => p.trim())
    if (name.length < 3) {
      errors.push({ key: 'errorLine', params: { line: index + 1 } })
      return
    }
    const subject: SubjectRequest = { name }
    if (birthDate) subject.birth_date = birthDate
    if (country) subject.country = country
    if (reference) subject.reference = reference
    subjects.push(subject)
  })
  if (!subjects.length && !errors.length) errors.push({ key: 'errorNoSubject' })
  return { subjects, errors }
}

/** Replace one hit (after a decision) without reloading the whole run. */
export function replaceHit(run: RunView, updated: HitView): RunView {
  return {
    ...run,
    subjects: run.subjects.map((subject) => ({
      ...subject,
      hits: subject.hits.map((hit) => (hit.hit_id === updated.hit_id ? updated : hit)),
    })),
  }
}
