<script setup lang="ts">
import { computed } from 'vue'
import { useI18n, type Locale } from '../i18n'
import RiskFlagCard from './RiskFlagCard.vue'
import { riskMessages, type ProfileReference, type RecordView, formatValue, pairs, recordLabel, type FlagEntry } from '@auditcore/ui-core'

const props = withDefaults(defineProps<{
  record?: RecordView | null
  entries?: readonly FlagEntry[]
  profile?: ProfileReference | null
  locale?: Locale
}>(), { record: null, entries: () => [], profile: null, locale: undefined })

const { t, locale: active } = useI18n(riskMessages, () => props.locale)
const assessment = computed(() => pairs(props.record?.assessment).filter(([, value]) => typeof value !== 'object' || value === null))
</script>

<template>
  <section class="fa-risk-detail" aria-live="polite" data-testid="risk-detail">
    <p v-if="!record" class="fa-risk-detail__empty">{{ t('detailEmpty') }}</p>
    <template v-else>
      <h3>{{ t('detailTitle', { record: recordLabel(record) }) }}</h3>
      <p v-if="entries.length === 0" class="fa-risk-detail__empty">{{ t('detailNone') }}</p>
      <RiskFlagCard v-for="entry in entries" :key="entry.code" :entry="entry" :profile="profile" :locale="locale" />
      <dl v-if="assessment.length" class="fa-risk-detail__assessment" :aria-label="t('assessment')">
        <template v-for="[name, value] in assessment" :key="name">
          <dt>{{ name }}</dt><dd>{{ formatValue(value, active, t('emptyValue')) }}</dd>
        </template>
      </dl>
    </template>
  </section>
</template>
