import { STATE_FILTER_KEYS, riskMessages, type Locale, type RiskFilter, type RuleView, type StateFilter } from '@flowaudit/ui-core'
import { useTranslation } from '../i18n'
import { useElementId } from '../store'

export interface RiskFlagFilterProps {
  /** Gesteuerter Filter (Gegenstück zu `v-model`). */
  filter: RiskFilter
  onFilterChange: (filter: RiskFilter) => void
  rules?: readonly RuleView[]
  shown?: number
  total?: number
  locale?: Locale
}

const STATES: readonly StateFilter[] = ['affected', 'hit', 'undetermined', 'clear', 'all']

/** Filter nach Merkmal, Zustand und Suchtext, wie `RiskFlagFilter`. */
export function RiskFlagFilter({ filter, onFilterChange, rules = [], shown = 0, total = 0, locale }: RiskFlagFilterProps) {
  const { t } = useTranslation(riskMessages, locale)
  const id = useElementId('fa-risk-filter')
  const update = (patch: Partial<RiskFilter>): void => onFilterChange({ ...filter, ...patch })
  return (
    <form className="fa-risk-filter" role="search" aria-label={t('filterTitle')} onSubmit={(event) => event.preventDefault()}>
      <label htmlFor={`${id}-code`}>{t('filterCode')}</label>
      <select id={`${id}-code`} value={filter.code ?? ''} data-testid="risk-filter-code" onChange={(event) => update({ code: event.target.value === '' ? null : event.target.value })}>
        <option value="">{t('filterCodeAll')}</option>
        {rules.map((rule) => <option key={rule.code} value={rule.code}>{rule.code} – {rule.label}</option>)}
      </select>
      <label htmlFor={`${id}-state`}>{t('filterState')}</label>
      <select id={`${id}-state`} value={filter.state} data-testid="risk-filter-state" onChange={(event) => update({ state: event.target.value as StateFilter })}>
        {STATES.map((state) => <option key={state} value={state}>{t(STATE_FILTER_KEYS[state])}</option>)}
      </select>
      <label htmlFor={`${id}-query`}>{t('filterQuery')}</label>
      <input id={`${id}-query`} type="search" value={filter.query} data-testid="risk-filter-query" onChange={(event) => update({ query: event.target.value })} />
      <output className="fa-risk-filter__result" aria-live="polite">{t('filterResult', { shown, total })}</output>
    </form>
  )
}
