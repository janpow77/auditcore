<script setup lang="ts">
import { computed } from 'vue'
import FaBadge from '../../base/FaBadge.vue'
import { useI18n } from '../../i18n'
import { screeningMessages } from '../messages'
import type { FindingView, SubjectView } from '../types'
import { formatDate } from '../view'

const props = defineProps<{ subject: SubjectView }>()
const { t } = useI18n(screeningMessages)

const details = computed(() => {
  const input = props.subject.input
  const parts = [
    input.birth_date ? t('born', { date: input.birth_date }) : '',
    input.country ? t('countryOf', { country: input.country }) : '',
    input.reference ?? '',
    t('normalized', { query: props.subject.normalized_query }),
  ]
  return parts.filter(Boolean).join(' · ')
})

function findingText(finding: FindingView): string {
  return finding.searched
    ? t('findingSearched', { list: finding.list_name, count: finding.hit_count, date: formatDate(finding.as_of) })
    : t('findingNotSearched', { list: finding.list_name })
}
</script>

<template>
  <div class="fa-screening__muted">{{ details }}</div>
  <div class="fa-screening__findings" role="group" :aria-label="t('queriedLists')">
    <FaBadge
      v-for="finding in subject.findings"
      :key="finding.list_key"
      :tone="finding.searched ? 'neutral' : 'danger'"
      :title="finding.note ?? undefined"
    >
      {{ findingText(finding) }}
    </FaBadge>
  </div>
</template>
