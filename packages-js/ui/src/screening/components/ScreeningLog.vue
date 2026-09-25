<script setup lang="ts">
import { useI18n } from '../../i18n'
import { screeningMessages } from '../messages'
import type { LogEntry } from '../types'
import { formatDate } from '../view'

defineProps<{ events: LogEntry[] }>()
const { t } = useI18n(screeningMessages)

function reasonOf(entry: LogEntry): string | null {
  const reason = entry.data['reason']
  return typeof reason === 'string' ? reason : null
}

function detail(entry: LogEntry): string {
  if (entry.type === 'second_review_recorded') {
    const result = t(entry.data['approve'] === true ? 'approved' : 'rejected')
    return t('logSecondReview', { result, outcome: entry.outcome_label ?? '–' })
  }
  if (entry.type === 'decision_recorded') {
    return `${entry.outcome_label ?? ''}${entry.data['four_eyes'] === true ? t('logFourEyes') : ''}`
  }
  const count = entry.data['subjects']
  return typeof count === 'number' ? t('logSubjects', { count }) : ''
}
</script>

<template>
  <section class="fa-screening__panel" aria-labelledby="fa-screening-log-title">
    <h3 id="fa-screening-log-title">{{ t('log') }}</h3>
    <p v-if="!events.length" class="fa-screening__empty">{{ t('logEmpty') }}</p>
    <ol class="fa-screening__log">
      <li v-for="entry in events" :key="entry.sequence" :class="`fa-screening__log--${entry.type}`">
        <strong>#{{ entry.sequence }} {{ entry.type_label }}</strong> – {{ detail(entry) }}
        <div class="fa-screening__muted">
          {{ formatDate(entry.at) }} · {{ entry.actor.display_name }}
          <span v-if="entry.hit"> · {{ entry.hit.subject_name }} ↔ {{ entry.hit.entry_name }} ({{ entry.hit.list_name }})</span>
        </div>
        <div v-if="reasonOf(entry)">„{{ reasonOf(entry) }}“</div>
      </li>
    </ol>
  </section>
</template>
