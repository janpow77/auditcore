<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from '../../i18n'
import { screeningMessages } from '../messages'
import type { HitView, LogEntry, Outcome, ReviewStatus, RunView, SettingsView, SubjectView } from '../types'
import { filterOptions, formatDate, type HitFilter } from '../view'
import ScreeningComparison from './ScreeningComparison.vue'
import ScreeningDecision from './ScreeningDecision.vue'
import ScreeningFilters from './ScreeningFilters.vue'
import ScreeningHitList from './ScreeningHitList.vue'
import ScreeningLog from './ScreeningLog.vue'
import ScreeningScoreBreakdown from './ScreeningScoreBreakdown.vue'
import ScreeningSources from './ScreeningSources.vue'

const props = defineProps<{
  run: RunView
  subjects: SubjectView[]
  selected: { subject: SubjectView; hit: HitView } | null
  filter: HitFilter
  settings: SettingsView | null
  events: LogEntry[]
  busy: boolean
}>()
const emit = defineEmits<{
  'update:filter': [value: HitFilter]
  select: [hitId: string]
  next: []
  decide: [outcome: Outcome, reason: string, fourEyes: boolean]
  secondReview: [approve: boolean, reason: string]
}>()

const { t } = useI18n(screeningMessages)
const options = computed(() => filterOptions(props.run))
const counts = computed(() => Object.entries(props.run.review_counts) as [ReviewStatus, number][])
</script>

<template>
  <section class="fa-screening__panel" aria-labelledby="fa-screening-run-title">
    <h3 id="fa-screening-run-title">
      {{ run.case_reference || t('run') }}
      <span class="fa-screening__muted">{{ formatDate(run.created_at) }} · {{ run.created_by.display_name }}</span>
    </h3>
    <div class="fa-screening__summary">
      <span>{{ t(`kind_${run.kind}`) }}</span>
      <span>{{ t('profileLine', { id: run.profile.id, version: run.profile.version }) }}</span>
      <span>{{ t('namesHits', { names: run.subject_count, hits: run.hit_count }) }}</span>
      <span v-for="[status, count] in counts" :key="status">{{ t(`status_${status}`) }}: {{ count }}</span>
    </div>
    <p v-if="run.subjects_incomplete" class="fa-screening__alert" role="status">
      {{ t('incompleteRun', { count: run.subjects_incomplete }) }}
    </p>
  </section>
  <ScreeningFilters :model-value="filter" :options="options" @update:model-value="emit('update:filter', $event)" />
  <div class="fa-screening__main">
    <ScreeningHitList :subjects="subjects" :selected-id="selected?.hit.hit_id ?? null" @select="emit('select', $event)" />
    <div v-if="selected">
      <ScreeningComparison :subject="selected.subject" :hit="selected.hit" />
      <ScreeningScoreBreakdown :breakdown="selected.hit.breakdown" />
      <ScreeningDecision
        :review="selected.hit.review"
        :hit-id="selected.hit.hit_id"
        :settings="settings"
        :busy="busy"
        @decide="(o, r, f) => emit('decide', o, r, f)"
        @second-review="(a, r) => emit('secondReview', a, r)"
      />
      <button type="button" class="fa-screening__btn" data-testid="screening-next" @click="emit('next')">{{ t('nextOpen') }}</button>
    </div>
    <p v-else class="fa-screening__panel fa-screening__empty">{{ t('noSelection') }}</p>
  </div>
  <ScreeningLog :events="events" />
  <ScreeningSources :sources="run.sources" :title="t('sourcesOfRun')" />
</template>
