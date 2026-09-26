<script setup lang="ts">
import FaBadge from '../../base/FaBadge.vue'
import { useI18n } from '../../i18n'
import { screeningMessages } from '../core'
import type { RunSummary } from '../core'
import { formatDate } from '../core'

defineProps<{ runs: RunSummary[]; activeId: string | null }>()
const emit = defineEmits<{ open: [runId: string] }>()
const { t } = useI18n(screeningMessages)

const openCount = (run: RunSummary): number =>
  run.review_counts.open + run.review_counts.deferred + run.review_counts.pending_second_review
const summary = (run: RunSummary): string => t('runSummary', {
  kind: t(`kind_${run.kind}`),
  names: run.subject_count,
  hits: run.hit_count,
  date: formatDate(run.created_at),
  actor: run.created_by.display_name,
})
</script>

<template>
  <section class="fa-screening__panel" aria-labelledby="fa-screening-runs-title">
    <h3 id="fa-screening-runs-title">{{ t('runs') }}</h3>
    <p v-if="!runs.length" class="fa-screening__empty">{{ t('noRuns') }}</p>
    <ul v-else class="fa-screening__runs">
      <li v-for="run in runs" :key="run.run_id">
        <button type="button" :aria-current="run.run_id === activeId" @click="emit('open', run.run_id)">
          <strong>{{ run.case_reference || t('runDated', { date: formatDate(run.created_at) }) }}</strong>
          <span class="fa-screening__muted">{{ summary(run) }}</span>
          <span>
            <FaBadge v-if="run.review_complete" tone="success">{{ t('complete') }}</FaBadge>
            <FaBadge v-else tone="warning">{{ t('openCount', { count: openCount(run) }) }}</FaBadge>
            <FaBadge v-if="run.subjects_incomplete" tone="danger">{{ t('incompleteCount', { count: run.subjects_incomplete }) }}</FaBadge>
          </span>
        </button>
      </li>
    </ul>
  </section>
</template>
