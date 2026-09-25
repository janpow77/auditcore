<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from '../../i18n'
import { screeningMessages, type ScreeningKey } from '../messages'
import type { HitView, SubjectView } from '../types'
import { comparisonRows, indicatorLabels, type MatchState } from '../view'

const props = defineProps<{ subject: SubjectView; hit: HitView }>()
const { t } = useI18n(screeningMessages)
const rows = computed(() => comparisonRows(props.subject, props.hit, t))
const hints = computed(() => indicatorLabels(props.hit, t))

const symbols: Record<MatchState, string> = { match: '✓', conflict: '✗', not_compared: '–', info: '' }
const stateKeys: Record<MatchState, ScreeningKey | null> = {
  match: 'stateMatch',
  conflict: 'stateConflict',
  not_compared: 'stateNotCompared',
  info: null,
}
const stateText = (state: MatchState): string => {
  const key = stateKeys[state]
  return key ? t(key) : ''
}
</script>

<template>
  <section class="fa-screening__panel" aria-labelledby="fa-screening-cmp-title">
    <h3 id="fa-screening-cmp-title">{{ t('comparison') }}</h3>
    <table class="fa-screening__table fa-screening__cmp">
      <thead>
        <tr>
          <th scope="col">{{ t('attribute') }}</th>
          <th scope="col">{{ t('input') }}</th>
          <th scope="col">{{ t('listEntry') }}</th>
          <th scope="col"><span class="fa-screening__sr">{{ t('matchColumn') }}</span></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row.label" :class="`fa-screening__cmp--${row.state}`">
          <th scope="row">{{ row.label }}</th>
          <td>{{ row.input }}</td>
          <td>{{ row.entry }}</td>
          <td class="fa-screening__state" :title="stateText(row.state)">
            <span aria-hidden="true">{{ symbols[row.state] }}</span>
            <span class="fa-screening__sr">{{ stateText(row.state) }}</span>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-if="hints.length" class="fa-screening__muted">{{ t('hints', { hints: hints.join(' · ') }) }}</p>
  </section>
</template>
