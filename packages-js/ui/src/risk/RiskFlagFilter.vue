<script setup lang="ts">
import { useI18n, type Locale } from '../i18n'
import { useId } from '../composables/useId'
import { riskMessages } from './messages'
import type { RuleView } from './types'
import { STATE_FILTER_KEYS } from './view/labels'
import type { RiskFilter, StateFilter } from './view/state'

const props = withDefaults(defineProps<{
  rules?: readonly RuleView[]
  shown?: number
  total?: number
  locale?: Locale
}>(), { rules: () => [], shown: 0, total: 0, locale: undefined })

const filter = defineModel<RiskFilter>({ required: true })
const { t } = useI18n(riskMessages, () => props.locale)
const id = useId('fa-risk-filter')
const STATES: readonly StateFilter[] = ['affected', 'hit', 'undetermined', 'clear', 'all']

function update(patch: Partial<RiskFilter>): void {
  filter.value = { ...filter.value, ...patch }
}

function onCode(event: Event): void {
  const value = (event.target as HTMLSelectElement).value
  update({ code: value === '' ? null : value })
}

function onState(event: Event): void {
  update({ state: (event.target as HTMLSelectElement).value as StateFilter })
}

function onQuery(event: Event): void {
  update({ query: (event.target as HTMLInputElement).value })
}
</script>

<template>
  <form class="fa-risk-filter" role="search" :aria-label="t('filterTitle')" @submit.prevent>
    <label :for="`${id}-code`">{{ t('filterCode') }}</label>
    <select :id="`${id}-code`" :value="filter.code ?? ''" data-testid="risk-filter-code" @change="onCode">
      <option value="">{{ t('filterCodeAll') }}</option>
      <option v-for="rule in rules" :key="rule.code" :value="rule.code">{{ rule.code }} – {{ rule.label }}</option>
    </select>
    <label :for="`${id}-state`">{{ t('filterState') }}</label>
    <select :id="`${id}-state`" :value="filter.state" data-testid="risk-filter-state" @change="onState">
      <option v-for="state in STATES" :key="state" :value="state">{{ t(STATE_FILTER_KEYS[state]) }}</option>
    </select>
    <label :for="`${id}-query`">{{ t('filterQuery') }}</label>
    <input :id="`${id}-query`" type="search" :value="filter.query" data-testid="risk-filter-query" @input="onQuery">
    <output class="fa-risk-filter__result" aria-live="polite">{{ t('filterResult', { shown, total }) }}</output>
  </form>
</template>

<style>
.fa-risk-filter { display: grid; grid-template-columns: auto minmax(10rem, 1fr); gap: var(--fa-space-2) var(--fa-space-3); align-items: center; font-size: var(--fa-font-size-sm); color: var(--fa-color-text); }
.fa-risk-filter label { color: var(--fa-color-text-muted); font-weight: 600; }
.fa-risk-filter select, .fa-risk-filter input { min-width: 0; padding: var(--fa-space-1) var(--fa-space-2); border: 1px solid var(--fa-color-border-strong); border-radius: var(--fa-radius-sm); background: var(--fa-color-surface); color: var(--fa-color-text); font: inherit; }
.fa-risk-filter select:focus-visible, .fa-risk-filter input:focus-visible { outline: none; box-shadow: var(--fa-focus-ring); }
.fa-risk-filter__result { grid-column: 1 / -1; color: var(--fa-color-text-muted); }
@media (min-width: 60rem) { .fa-risk-filter { grid-template-columns: auto minmax(12rem, 1fr) auto minmax(10rem, 14rem) auto minmax(10rem, 1fr); } }
</style>
