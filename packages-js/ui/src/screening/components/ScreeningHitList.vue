<script setup lang="ts">
import FaBadge from '../../base/FaBadge.vue'
import type { BadgeTone } from '../../base/types'
import { useI18n } from '../../i18n'
import { codeLabel, screeningMessages } from '../core'
import type { HitView, ReviewStatus, SubjectStatus, SubjectView } from '../core'
import { formatScore, scorePercent } from '../core'
import ScreeningSubjectInfo from './ScreeningSubjectInfo.vue'

defineProps<{ subjects: SubjectView[]; selectedId: string | null }>()
const emit = defineEmits<{ select: [hitId: string] }>()
const { t, locale } = useI18n(screeningMessages)

const statusTone: Record<ReviewStatus, BadgeTone> = {
  open: 'warning',
  pending_second_review: 'warning',
  deferred: 'neutral',
  confirmed: 'danger',
  dismissed: 'success',
}
const subjectTone: Record<SubjectStatus, BadgeTone> = {
  HITS: 'warning',
  NO_HITS: 'success',
  INCOMPLETE: 'danger',
  NOT_SEARCHED: 'danger',
}
const minMarker = (hit: HitView): number => scorePercent(hit.breakdown.min_score, hit.breakdown.scale)
</script>

<template>
  <section class="fa-screening__panel" aria-labelledby="fa-screening-hits-title">
    <h3 id="fa-screening-hits-title">{{ t('hits') }}</h3>
    <article v-for="subject in subjects" :key="subject.subject_id" class="fa-screening__subject">
      <header class="fa-screening__subject-head">
        <strong>{{ subject.input.name }}</strong>
        <FaBadge :tone="subjectTone[subject.status]">{{ t(`subject_${subject.status}`) }}</FaBadge>
      </header>
      <ScreeningSubjectInfo :subject="subject" />
      <p v-if="!subject.hits.length" class="fa-screening__empty">
        {{ subject.hits_before_filter ? t('noHitsFiltered') : t('noHits') }}
      </p>
      <ul class="fa-screening__hits">
        <li v-for="hit in subject.hits" :key="hit.hit_id">
          <button type="button" class="fa-screening__hit" :aria-current="hit.hit_id === selectedId" @click="emit('select', hit.hit_id)">
            <span class="fa-screening__hit-name">{{ hit.entry.name }}</span>
            <span class="fa-screening__bar" aria-hidden="true">
              <span :style="{ width: `${scorePercent(hit.score, hit.breakdown.scale)}%` }" />
              <i :style="{ left: `${minMarker(hit)}%` }" />
            </span>
            <span class="fa-screening__score">{{ formatScore(hit.score, hit.breakdown.scale, locale) }}</span>
            <span class="fa-screening__hit-meta">
              <span>{{ hit.list_name }}</span>
              <span>· {{ codeLabel(t, 'class', hit.confidence) }}</span>
              <span v-if="hit.matched_field === 'alias'">· {{ t('viaAlias', { name: hit.matched_name }) }}</span>
              <FaBadge v-if="hit.dob_conflict" tone="danger">{{ t('dobConflict') }}</FaBadge>
              <FaBadge v-if="hit.country_conflict" tone="danger">{{ t('countryConflict') }}</FaBadge>
              <FaBadge :tone="statusTone[hit.review.status]">{{ t(`status_${hit.review.status}`) }}</FaBadge>
            </span>
          </button>
        </li>
      </ul>
      <p v-if="subject.truncated" class="fa-screening__muted">{{ t('truncated', { total: subject.total_hits }) }}</p>
      <details v-if="subject.limitations.length" class="fa-screening__muted">
        <summary>{{ t('limitations') }}</summary>
        <ul>
          <li v-for="text in subject.limitations" :key="text">{{ text }}</li>
        </ul>
      </details>
    </article>
  </section>
</template>
