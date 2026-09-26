<script setup lang="ts">
import FaBadge from '../../base/FaBadge.vue'
import type { BadgeTone } from '../../base/types'
import { formatNumber, useI18n } from '../../i18n'
import { screeningMessages } from '../core'
import type { FreshnessStatus, SourceView } from '../core'
import { formatAge, formatDate, freshnessTone } from '../core'

const props = defineProps<{ sources: SourceView[]; checkedAt?: string | null; title?: string; compact?: boolean }>()
const { t, locale } = useI18n(screeningMessages)
const headingId = props.compact ? 'fa-screening-sources-now' : 'fa-screening-sources-run'
const tones: Record<'ok' | 'warn' | 'muted', BadgeTone> = { ok: 'success', warn: 'warning', muted: 'neutral' }
const tone = (status: FreshnessStatus): BadgeTone => tones[freshnessTone(status)]
const count = (value: number): string => formatNumber(value, locale.value)
</script>

<template>
  <section class="fa-screening__panel" :aria-labelledby="headingId">
    <h3 :id="headingId">
      {{ title ?? t('sources') }}
      <span v-if="checkedAt" class="fa-screening__muted">{{ t('checkedAt', { date: formatDate(checkedAt) }) }}</span>
    </h3>
    <p v-if="!sources.length" class="fa-screening__empty">{{ t('noSources') }}</p>
    <ul v-else-if="compact" class="fa-screening__source-list">
      <li v-for="source in sources" :key="source.list.key">
        <strong>{{ source.list.name }}</strong>
        <span>
          <FaBadge :tone="tone(source.freshness.status)">{{ t(`fresh_${source.freshness.status}`) }}</FaBadge>
          <FaBadge v-if="!source.searchable" tone="danger">{{ t('noStock') }}</FaBadge>
        </span>
        <span class="fa-screening__muted">
          {{ t('asOf', { date: source.as_of ? formatDate(source.as_of) : t('unknown') }) }} · {{ formatAge(source.freshness.age_days, t) }}
          · {{ t('entries', { count: count(source.entry_count) }) }}
        </span>
      </li>
    </ul>
    <table v-else class="fa-screening__table">
      <thead>
        <tr>
          <th scope="col">{{ t('columnList') }}</th>
          <th scope="col">{{ t('columnEntries') }}</th>
          <th scope="col">{{ t('columnAsOf') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="source in sources" :key="source.list.key">
          <td>
            <a v-if="source.list.url" :href="source.list.url" target="_blank" rel="noopener noreferrer">{{ source.list.name }}</a>
            <span v-else>{{ source.list.name }}</span>
            <div class="fa-screening__muted">
              {{ t('via', { kind: t(`kind_${source.kind}`), issuer: source.list.issuer, provider: source.list.provider }) }}
            </div>
            <div v-if="source.list.data_licence.status" class="fa-screening__muted" :title="source.list.data_licence.note">
              {{ t('dataLicence', { status: source.list.data_licence.status }) }}
            </div>
          </td>
          <td>
            <span v-if="source.searchable">{{ count(source.entry_count) }}</span>
            <FaBadge v-else tone="danger" :title="t('noStockHint')">{{ t('noStock') }}</FaBadge>
          </td>
          <td>
            <div>{{ source.as_of ? formatDate(source.as_of) : '–' }}</div>
            <FaBadge :tone="tone(source.freshness.status)">{{ t(`fresh_${source.freshness.status}`) }}</FaBadge>
            <div class="fa-screening__muted">{{ formatAge(source.freshness.age_days, t) }}</div>
          </td>
        </tr>
      </tbody>
    </table>
  </section>
</template>
