<script setup lang="ts">
import { computed } from 'vue'
import FaBadge from '../../base/FaBadge.vue'
import { useI18n } from '../../i18n'
import { screeningMessages } from '../core'
import type { Breakdown } from '../core'
import { breakdownRows, formatScore } from '../core'

const props = defineProps<{ breakdown: Breakdown }>()
const { t, locale } = useI18n(screeningMessages)
const rows = computed(() => breakdownRows(props.breakdown, locale.value))
const scale = computed(() => props.breakdown.scale)
const score = (value: number): string => formatScore(value, scale.value, locale.value)
</script>

<template>
  <section class="fa-screening__panel" aria-labelledby="fa-screening-breakdown-title">
    <h3 id="fa-screening-breakdown-title">
      {{ t('breakdown') }}
      <span class="fa-screening__muted">{{ t('method', { method: breakdown.method, min: scale.min, max: scale.max }) }}</span>
    </h3>
    <p v-if="!breakdown.consistent" class="fa-screening__alert fa-screening__alert--warning" role="status">{{ t('inconsistent') }}</p>
    <table class="fa-screening__table fa-screening__steps">
      <tbody>
        <tr v-for="(row, index) in rows" :key="index" :class="`fa-screening__steps--${row.tone}`">
          <td>
            {{ row.label }}
            <div v-if="row.value" class="fa-screening__muted">{{ row.value }}</div>
          </td>
          <td class="fa-screening__points">{{ row.points }}</td>
        </tr>
      </tbody>
    </table>
    <div class="fa-screening__classes">
      <FaBadge tone="accent">{{ t('level', { label: breakdown.class_label }) }}</FaBadge>
      <FaBadge>{{ t('minScoreBadge', { value: score(breakdown.min_score) }) }}</FaBadge>
      <FaBadge v-for="c in breakdown.classes" :key="c.class">{{ t('classFrom', { label: c.label, value: score(c.from) }) }}</FaBadge>
    </div>
  </section>
</template>
