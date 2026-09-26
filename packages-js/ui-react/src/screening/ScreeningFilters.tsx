import type { ReactNode } from 'react'
import { codeLabel, type FilterOptions, type HitFilter, type ReviewStatus } from '@flowaudit/ui-core'
import { codeKey, useScreeningText } from './shared'

const STATUSES: ReviewStatus[] = ['open', 'pending_second_review', 'confirmed', 'dismissed', 'deferred']
type ListKey = 'statuses' | 'lists' | 'subjects' | 'confidences'

export interface ScreeningFiltersProps {
  value: HitFilter
  options: FilterOptions
  /** Gegenstück zu `update:modelValue` der Vue-Fassung. */
  onChange: (value: HitFilter) => void
}

function parseScore(value: string): number | null {
  const parsed = value === '' ? null : Number(value)
  return parsed !== null && Number.isFinite(parsed) ? parsed : null
}

function Choice({ label, value, onChange, children }: { label: string; value: string; onChange: (value: string) => void; children: ReactNode }) {
  const { t } = useScreeningText()
  return (
    <label className="fa-screening__field">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">{t('all')}</option>
        {children}
      </select>
    </label>
  )
}

/** Filter der Trefferliste (Status, Liste, Name, Stufe, Mindestscore, Suche). */
export function ScreeningFilters({ value, options, onChange }: ScreeningFiltersProps) {
  const { t } = useScreeningText()
  const single = (key: ListKey) => ({
    value: value[key][0] ?? '',
    onChange: (next: string) => onChange({ ...value, [key]: next ? [next] : [] }),
  })
  return (
    <section className="fa-screening__panel" aria-labelledby="fa-screening-filter-title">
      <h3 id="fa-screening-filter-title">{t('filters')}</h3>
      <div className="fa-screening__filters">
        <Choice label={t('filterStatus')} {...single('statuses')}>
          {STATUSES.map((key) => <option key={key} value={key}>{t(codeKey('status', key))}</option>)}
        </Choice>
        <Choice label={t('filterList')} {...single('lists')}>
          {options.lists.map((l) => <option key={l.key} value={l.key}>{l.name}</option>)}
        </Choice>
        <Choice label={t('filterSubject')} {...single('subjects')}>
          {options.subjects.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
        </Choice>
        <Choice label={t('filterConfidence')} {...single('confidences')}>
          {options.confidences.map((c) => <option key={c} value={c}>{codeLabel(t, 'class', c)}</option>)}
        </Choice>
        <label className="fa-screening__field">
          <span>{t('filterMinScore')}</span>
          <input
            type="number"
            step="any"
            inputMode="decimal"
            value={value.minScore === null ? '' : String(value.minScore)}
            onChange={(event) => onChange({ ...value, minScore: parseScore(event.target.value) })}
          />
        </label>
        <label className="fa-screening__field">
          <span>{t('filterText')}</span>
          <input type="search" value={value.text} onChange={(event) => onChange({ ...value, text: event.target.value })} />
        </label>
      </div>
    </section>
  )
}
