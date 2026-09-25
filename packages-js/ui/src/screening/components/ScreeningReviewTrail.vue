<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from '../../i18n'
import { screeningMessages } from '../messages'
import type { ReviewView } from '../types'

const props = defineProps<{ review: ReviewView; formatDate: (value: string | null | undefined) => string }>()
const { t } = useI18n(screeningMessages)

const decision = computed(() => {
  const entry = props.review.decision
  if (!entry) return ''
  const line = t('lastDecision', { outcome: t(`status_${entry.outcome}`), actor: entry.actor.display_name, date: props.formatDate(entry.at) })
  const marker = entry.four_eyes ? ` ${t(entry.four_eyes_source === 'policy' ? 'fourEyesMarkerPolicy' : 'fourEyesMarker')}` : ''
  return `${line}${marker} – „${entry.reason}“`
})

const second = computed(() => {
  const entry = props.review.second_review
  if (!entry) return ''
  const result = t(entry.approve ? 'approved' : 'rejected')
  return `${t('secondReviewDone', { result, actor: entry.actor.display_name, date: props.formatDate(entry.at) })} – „${entry.reason}“`
})
</script>

<template>
  <div v-if="decision" class="fa-screening__muted">{{ decision }}</div>
  <div v-if="second" class="fa-screening__muted">{{ second }}</div>
</template>
