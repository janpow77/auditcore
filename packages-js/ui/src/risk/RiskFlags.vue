<script setup lang="ts">
import { computed, watch } from 'vue'
import { useI18n, type Locale } from '../i18n'
import RiskFlagFilter from './RiskFlagFilter.vue'
import RiskFlagSummary from './RiskFlagSummary.vue'
import RiskFlagTable from './RiskFlagTable.vue'
import RiskProfileInfo from './RiskProfileInfo.vue'
import RiskRecordDetail from './RiskRecordDetail.vue'
import { riskMessages, type RiskPort, type Evaluation, type ProfileDetail, profileHintText, profileStatusText, type RiskFilter } from '@flowaudit/ui-core'
import { useRiskFlags } from './useRiskFlags'
import { useRiskProfile } from './useRiskProfile'

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
const status = computed(() => profileStatusText(reference.value, t))
const hint = computed(() => profileHintText(reference.value, t))
const codes = computed(() => state.rules.value.map((rule) => rule.code))

watch(state.filter, (filter) => emit('filter-change', filter), { deep: true })

function selectRecord(index: number): void {
  emit('record-select', state.controller.toggleRecord(index))
}

function selectCode(code: string): void {
  state.controller.selectCode(code)
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
