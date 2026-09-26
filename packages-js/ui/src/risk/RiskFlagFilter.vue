<script setup lang="ts">
import { useI18n, type Locale } from '../i18n'
import { useId } from '../composables/useId'
import { riskMessages, type RuleView, STATE_FILTER_KEYS, type RiskFilter, type StateFilter } from '@flowaudit/ui-core'

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
