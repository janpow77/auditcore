<script setup lang="ts">
import { computed, watch } from 'vue'
import { useI18n, type Locale } from '../i18n'
import RiskFlagFilter from './RiskFlagFilter.vue'
import RiskFlagSummary from './RiskFlagSummary.vue'
import RiskFlagTable from './RiskFlagTable.vue'
import RiskProfileInfo from './RiskProfileInfo.vue'
import RiskRecordDetail from './RiskRecordDetail.vue'
import { riskMessages } from './messages'
import type { RiskPort } from './port'
import type { Evaluation, ProfileDetail } from './types'
import { useRiskFlags } from './useRiskFlags'
import { useRiskProfile } from './useRiskProfile'
import { statusHintKey, statusKey } from './view/labels'
import type { RiskFilter } from './view/state'

const props = withDefaults(defineProps<{
  /** Antwort von `POST /evaluate` (docs/ui/risk-rest.md). */
  evaluation?: Evaluation | null
  /** Antwort von `GET /profiles/{id}/{version}`; ohne sie entfällt die Profilansicht. */
  profile?: ProfileDetail | null
  /** Optional: lädt die Profilbeschreibung nach, wenn `profile` fehlt (`createRiskRestPort`). */
  port?: RiskPort | null
  heading?: string
  locale?: Locale
}>(), { evaluation: null, profile: null, port: null, heading: '', locale: undefined })

const emit = defineEmits<{ 'record-select': [index: number | null]; 'filter-change': [filter: RiskFilter] }>()
const { t } = useI18n(riskMessages, () => props.locale)
const state = useRiskFlags(() => props.evaluation, t('colRecord'))
const reference = computed(() => props.evaluation?.profile ?? null)
const detail = useRiskProfile(() => props.evaluation, () => props.profile, () => props.port)
const status = computed(() => {
  const key = reference.value ? statusKey(reference.value.status) : null
  return key ? t(key) : (reference.value?.status ?? '')
})
const hint = computed(() => {
  const key = reference.value ? statusHintKey(reference.value.status) : null
  return key ? t(key) : ''
})
const codes = computed(() => state.rules.value.map((rule) => rule.code))

watch(state.filter, (filter) => emit('filter-change', filter), { deep: true })

function selectRecord(index: number): void {
  state.select(state.selectedIndex.value === index ? null : index)
  emit('record-select', state.selectedIndex.value)
}

function selectCode(code: string): void {
  state.filter.value = { ...state.filter.value, code, state: 'affected' }
}
</script>

<template>
  <div class="fa-risk">
    <header class="fa-risk__head">
      <h2>{{ heading || t('title') }}</h2>
      <p v-if="reference" class="fa-risk__profile" data-testid="risk-profile">
        {{ t('profile') }} <code>{{ reference.id }}</code> · {{ t('version') }} <code>{{ reference.version }}</code> · {{ status }}
      </p>
      <p v-if="hint" class="fa-risk__hint" role="note">{{ hint }}</p>
    </header>
    <RiskFlagSummary
      :rows="state.rows.value"
      :totals="state.totals.value"
      :dataset="state.dataset.value"
      :missing-columns="evaluation?.missing_columns ?? {}"
      :locale="locale"
      @code-select="selectCode"
    />
    <RiskFlagFilter
      v-model="state.filter.value"
      :rules="state.rules.value"
      :shown="state.records.value.length"
      :total="evaluation?.records.length ?? 0"
      :locale="locale"
    />
    <div class="fa-risk__body">
      <RiskFlagTable
        :columns="state.tableColumns.value"
        :rows="state.tableRows.value"
        :codes="codes"
        :selected="state.selectedIndex.value"
        :locale="locale"
        @record-select="selectRecord"
      />
      <RiskRecordDetail :record="state.selected.value" :entries="state.entries.value" :profile="reference" :locale="locale" />
    </div>
    <p v-if="detail.error.value" class="fa-risk__hint" role="alert">{{ detail.error.value }}</p>
    <details v-if="detail.profile.value" class="fa-risk__profile-info">
      <summary>{{ t('profileInfo') }}</summary>
      <RiskProfileInfo :profile="detail.profile.value" :locale="locale" />
    </details>
  </div>
</template>

<style>
.fa-risk { display: grid; gap: var(--fa-space-4); font-family: var(--fa-font-sans); color: var(--fa-color-text); }
.fa-risk__head h2 { margin: 0; font-size: var(--fa-font-size-lg); }
.fa-risk__profile { margin: var(--fa-space-1) 0 0; font-size: var(--fa-font-size-sm); color: var(--fa-color-text-muted); }
.fa-risk__hint { margin: var(--fa-space-2) 0 0; padding: var(--fa-space-2) var(--fa-space-3); border-radius: var(--fa-radius-sm); background: var(--fa-color-warning-soft); color: var(--fa-color-warning); font-size: var(--fa-font-size-sm); font-weight: 600; }
.fa-risk__body { display: grid; gap: var(--fa-space-4); align-items: start; }
@media (min-width: 72rem) { .fa-risk__body { grid-template-columns: minmax(0, 1fr) minmax(22rem, 30rem); } }
.fa-risk__profile-info summary { cursor: pointer; font-weight: 600; color: var(--fa-color-accent); padding: var(--fa-space-2) 0; }
.fa-risk__profile-info summary:focus-visible { outline: none; box-shadow: var(--fa-focus-ring); border-radius: var(--fa-radius-sm); }
@media (prefers-reduced-motion: reduce) { .fa-risk * { transition: none !important; } }
</style>
