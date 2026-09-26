import { describe, expect, it } from 'vitest'
import fixture from '../fixtures/screening-contract.json'
import type { LogView, RunView, SettingsView } from '../../src'
import {
  acceptsHit,
  breakdownRows,
  comparisonRows,
  emptyFilter,
  filterOptions,
  filterSubjects,
  findHit,
  formatAge,
  formatDate,
  formatPoints,
  formatScore,
  nextOpenHit,
  parseSubjects,
  replaceHit,
  requiresFourEyes,
  scorePercent,
  validateDecision,
  canDecide,
  awaitsSecondReview,
  freshnessTone,
  indicatorLabels,
} from '../../src/screening/view'
import { translate } from '../../src'
import { screeningMessages, type ScreeningKey } from '../../src'

const t = (key: ScreeningKey, params?: Record<string, string | number>): string => translate(screeningMessages, 'de', key, params)

// Fixture written by the Python service (auditcore_registry_sources.web), synthetic persons only.
const run = fixture.run as unknown as RunView
const pepRun = fixture.pep_run as unknown as RunView
const settings = fixture.settings as unknown as SettingsView
const log = fixture.log as unknown as LogView

describe('contract fixture', () => {
  it('matches the contract version and review state', () => {
    expect(run.contract).toBe('auditcore_registry_sources.screening_review/1')
    expect(run.subjects[0]?.hits[0]?.review.status).toBe('pending_second_review')
    expect(log.events.map((e) => e.type)).toEqual(['run_created', 'decision_recorded'])
  })
})

describe('filters', () => {
  it('filters by status, list, score and text but keeps subjects', () => {
    const filter = { ...emptyFilter(), lists: ['un_sc'] }
    const visible = filterSubjects(run.subjects, filter)
    expect(visible).toHaveLength(run.subjects.length)
    expect(visible[0]?.hits.every((h) => h.list_key === 'un_sc')).toBe(true)
    const pending = { ...emptyFilter(), statuses: ['pending_second_review' as const] }
    expect(filterSubjects(run.subjects, pending)[0]?.hits).toHaveLength(1)
    const hit = run.subjects[0]!.hits[0]!
    expect(acceptsHit(hit, { ...emptyFilter(), minScore: 101 })).toBe(false)
    expect(acceptsHit(hit, { ...emptyFilter(), text: 'max beispiel' })).toBe(true)
    expect(acceptsHit(hit, { ...emptyFilter(), text: 'niemand' })).toBe(false)
  })

  it('offers lists, subjects and classes as options', () => {
    const options = filterOptions(run)
    expect(options.lists.map((l) => l.key)).toEqual(['eu_fsf', 'un_sc', 'us_ofac_sdn'])
    expect(options.subjects.map((s) => s.id)).toEqual(['s1', 's2'])
    expect(options.confidences.length).toBeGreaterThan(0)
  })
})

describe('formatting', () => {
  it('formats scores per scale in German and English notation', () => {
    expect(formatScore(69.8, { max: 100 }, 'en')).toBe('69.8')
    expect(formatScore(69.8, { max: 100 })).toBe('69,8')
    expect(formatScore(0.935, { max: 1 })).toBe('0,94')
    expect(formatPoints(-18, { max: 100 })).toBe('−18,0')
    expect(formatPoints(6, { max: 100 })).toBe('+6,0')
    expect(scorePercent(75, { min: 50, max: 100 })).toBe(50)
    expect(scorePercent(5, { min: 0, max: 0 })).toBe(0)
  })

  it('formats dates and ages', () => {
    expect(formatDate('2026-09-22T18:00:00Z')).toBe('22.09.2026, 18:00')
    expect(formatDate('2026-08-01')).toBe('01.08.2026')
    expect(formatDate(null)).toBe('–')
    expect(formatAge(null, t)).toBe('Alter unbekannt')
    expect(formatAge(0.4, t)).toBe('jünger als ein Tag')
    expect(formatAge(1.2, t)).toBe('vor 1 Tag')
    expect(formatAge(45.3, t)).toBe('vor 45 Tagen')
    expect(freshnessTone('current')).toBe('ok')
    expect(freshnessTone('stale')).toBe('warn')
    expect(freshnessTone('not_judged')).toBe('muted')
  })
})

describe('breakdown and comparison', () => {
  it('turns steps into rows with signed deltas', () => {
    const un = run.subjects[0]!.hits.find((h) => h.list_key === 'un_sc')!
    const rows = breakdownRows(un.breakdown)
    expect(rows.filter((r) => r.tone === 'minus').map((r) => r.points)).toEqual(['−18,0', '−10,0'])
    expect(rows.at(-1)?.tone).toBe('result')
    expect(rows[0]?.value).toContain('„maximilian beispielmann“')
  })

  it('shows PEP breakdowns on the 0–1 scale', () => {
    const rows = breakdownRows(pepRun.subjects[0]!.hits[0]!.breakdown)
    expect(rows.at(-1)?.points).toBe('1,00')
  })

  it('compares input and entry with match states', () => {
    const subject = run.subjects[0]!
    const un = subject.hits.find((h) => h.list_key === 'un_sc')!
    const rows = comparisonRows(subject, un, t)
    const dob = rows.find((r) => r.label === 'Geburtsdatum')!
    expect(dob).toMatchObject({ input: '1970-03-14', entry: '1971', state: 'conflict' })
    const eu = subject.hits.find((h) => h.list_key === 'eu_fsf')!
    expect(comparisonRows(subject, eu, t).find((r) => r.label === 'Adresse')?.entry).toBe(
      'Musterstraße 1, 12345 Musterstadt',
    )
    expect(comparisonRows(subject, eu, t).find((r) => r.label === 'Stand der Liste')?.entry).toBe('22.09.2026, 18:00')
    const second = run.subjects[1]!
    expect(second.hits).toHaveLength(0)
  })
})

describe('decisions', () => {
  it('requires outcome and reason', () => {
    expect(validateDecision({ outcome: null, reason: ' ', fourEyes: false })).toHaveLength(2)
    expect(validateDecision({ outcome: 'dismissed', reason: 'Kein Bezug.', fourEyes: false })).toEqual([])
    expect(validateDecision({ outcome: 'deferred', reason: 'x'.repeat(4001), fourEyes: false })).toHaveLength(1)
  })

  it('knows the four-eyes policy and decidable states', () => {
    expect(requiresFourEyes('confirmed', settings)).toBe(true)
    expect(requiresFourEyes('dismissed', settings)).toBe(false)
    expect(requiresFourEyes('confirmed', null)).toBe(false)
    const pending = run.subjects[0]!.hits[0]!.review
    expect(canDecide(pending)).toBe(false)
    expect(awaitsSecondReview(pending)).toBe(true)
  })

  it('walks to the next unfinished hit and replaces updated hits', () => {
    const hits = run.subjects[0]!.hits
    expect(nextOpenHit(run.subjects, null)).toBe(hits[0]!.hit_id)
    expect(nextOpenHit(run.subjects, hits[0]!.hit_id)).toBe(hits[1]!.hit_id)
    const updated = { ...hits[1]!, review: { ...hits[1]!.review, status: 'dismissed' as const } }
    const next = replaceHit(run, updated)
    expect(findHit(next, updated.hit_id)?.hit.review.status).toBe('dismissed')
    expect(findHit(next, 'fehlt')).toBeNull()
    expect(findHit(null, 'x')).toBeNull()
  })
})

describe('subject input', () => {
  it('parses one subject per line', () => {
    const parsed = parseSubjects('Erika Beispiel; 1970-01-31; de; Los 1\n\nAb\nBeispiel GmbH')
    expect(parsed.subjects).toEqual([
      { name: 'Erika Beispiel', birth_date: '1970-01-31', country: 'de', reference: 'Los 1' },
      { name: 'Beispiel GmbH' },
    ])
    expect(parsed.errors.map((e) => t(e.key, e.params))).toEqual(['Zeile 3: Name mit mindestens 3 Zeichen angeben.'])
    expect(parseSubjects('  ').errors).toEqual([{ key: 'errorNoSubject' }])
  })
})

describe('indicators', () => {
  it('labels known indicator codes and keeps unknown codes', () => {
    const hit = { ...run.subjects[0]!.hits[0]!, indicators: ['alias_match', 'neu_im_vertrag'] }
    expect(indicatorLabels(hit, t)).toEqual(['Treffer über Alias', 'neu_im_vertrag'])
  })
})
