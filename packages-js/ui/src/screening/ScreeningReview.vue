<script setup lang="ts">
import { watch } from 'vue'
import { provideLocale, useI18n, type Locale } from '../i18n'
import ScreeningRunDetail from './components/ScreeningRunDetail.vue'
import ScreeningRunForm from './components/ScreeningRunForm.vue'
import ScreeningRunList from './components/ScreeningRunList.vue'
import ScreeningSources from './components/ScreeningSources.vue'
import { screeningMessages } from './core'
import type { RunView, ScreeningPort } from './core'
import { useScreeningReview, type ScreeningError } from './useScreeningReview'

const props = withDefaults(defineProps<{
  /** Datenzugang (Vertrag screening_review/1), z. B. `createScreeningRestPort({ baseUrl: '/api/screening' })`. */
  port?: ScreeningPort | null
  /** Beim Laden zu öffnender Prüflauf. */
  runId?: string
  locale?: Locale
}>(), { port: null, runId: '', locale: undefined })

const emit = defineEmits<{
  'run-created': [detail: { runId: string }]
  decided: [detail: { runId: string; hitId: string; status: string }]
  error: [detail: ScreeningError]
}>()

const { t, locale: active } = useI18n(screeningMessages, () => props.locale)
provideLocale(active)

const state = useScreeningReview(() => props.port, {
  onRunCreated: (run: RunView) => emit('run-created', { runId: run.run_id }),
  onDecided: (detail) => emit('decided', detail),
  onError: (error) => emit('error', error),
  networkMessage: (message) => t('networkError', { message }),
})
const { settings, sources, runs, run, log, filter, busy, error, selected, visibleSubjects } = state

watch(() => props.port, async (port) => {
  if (!port) return
  await state.load()
  if (props.runId) await state.openRun(props.runId)
}, { immediate: true })
</script>

<template>
  <div class="fa-screening" :aria-busy="busy" data-testid="screening-review">
    <header class="fa-screening__header">
      <h2>{{ t('title') }}</h2>
      <span class="fa-screening__notice">{{ t('notice') }}</span>
    </header>
    <p v-if="!port" class="fa-screening__alert" role="alert">{{ t('noPort') }}</p>
    <p v-if="error" class="fa-screening__alert" role="alert">{{ error.message }}</p>
    <div class="fa-screening__layout">
      <aside>
        <ScreeningRunForm
          v-if="settings && sources"
          :settings="settings"
          :sources="sources.sources"
          :busy="busy"
          @submit="state.createRun"
        />
        <ScreeningRunList :runs="runs" :active-id="run?.run_id ?? null" @open="state.openRun" />
        <ScreeningSources v-if="sources" compact :sources="sources.sources" :checked-at="sources.checked_at" />
      </aside>
      <div>
        <ScreeningRunDetail
          v-if="run"
          :run="run"
          :subjects="visibleSubjects"
          :selected="selected"
          :filter="filter"
          :settings="settings"
          :events="log?.events ?? []"
          :busy="busy"
          @update:filter="state.setFilter"
          @select="state.select"
          @next="state.selectNext"
          @decide="state.decide"
          @second-review="state.secondReview"
        />
        <p v-else class="fa-screening__panel fa-screening__empty">{{ t('selectRun') }}</p>
      </div>
    </div>
  </div>
</template>
