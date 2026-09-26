<script setup lang="ts">
import { computed } from 'vue'
import {
  conclusionLabel,
  conclusionTone,
  extrapolationMessages,
  extrapolationStepColumns,
  extrapolationStepRows,
  terMetrics,
  type EvaluationResult,
  type ExtrapolationCatalogue,
  type ExtrapolationExportFormat,
} from '@auditcore/ui-core'
import FaBadge from '../base/FaBadge.vue'
import FaButton from '../base/FaButton.vue'
import { useId } from '../composables/useId'
import { useI18n, type Locale } from '../i18n'
import FaTable from '../table/FaTable.vue'

const props = withDefaults(defineProps<{
  result: EvaluationResult
  catalogue: ExtrapolationCatalogue | null
  busy?: boolean
  locale?: Locale
}>(), { busy: false, locale: undefined })
const emit = defineEmits<{ export: [format: ExtrapolationExportFormat] }>()
const { t, locale: active } = useI18n(extrapolationMessages, () => props.locale)
const id = useId('fa-extrapolation-result')
const ter = computed(() => props.result.total_error_rate)
const metrics = computed(() => terMetrics(props.result, t, active.value))
const columns = computed(() => extrapolationStepColumns(t, active.value))
const rows = computed(() => extrapolationStepRows(props.result))
</script>

<template>
  <section class="fa-extrapolation__card fa-extrapolation__card--result" :aria-labelledby="`${id}-title`" aria-live="polite">
    <h3 :id="`${id}-title`" class="fa-extrapolation__heading">{{ t('resultTitle') }}</h3>
    <p class="fa-extrapolation__conclusion">
      <FaBadge :tone="conclusionTone(ter.conclusion)" data-testid="extrapolation-conclusion">{{ conclusionLabel(catalogue, ter.conclusion) }}</FaBadge>
      <span class="fa-extrapolation__muted">{{ result.method.label }}</span>
    </p>
    <p class="fa-extrapolation__hint">{{ t('resultNotice') }}</p>
    <dl class="fa-extrapolation__metrics" data-testid="extrapolation-metrics">
      <div v-for="metric in metrics" :key="metric.id" class="fa-extrapolation__metric" :data-metric="metric.id">
        <dt>{{ metric.label }}</dt>
        <dd class="fa-extrapolation__value">{{ metric.value }}</dd>
        <dd v-if="metric.detail" class="fa-extrapolation__muted">{{ metric.detail }}</dd>
      </div>
    </dl>
    <h4 class="fa-extrapolation__heading">{{ t('explanation') }}</h4>
    <ul class="fa-extrapolation__list">
      <li v-for="line in ter.explanation" :key="line">{{ line }}</li>
    </ul>
    <template v-if="result.projection.warnings.length">
      <h4 class="fa-extrapolation__heading">{{ t('warnings') }}</h4>
      <ul class="fa-extrapolation__warnings">
        <li v-for="line in result.projection.warnings" :key="line">{{ line }}</li>
      </ul>
    </template>
    <details class="fa-extrapolation__derivation">
      <summary>{{ t('derivation') }}</summary>
      <FaTable :columns="columns" :rows="rows" :caption="t('derivation')" :locale="locale" data-testid="extrapolation-steps" />
    </details>
    <p class="fa-extrapolation__fingerprint">{{ t('fingerprint') }}: {{ result.fingerprint }}</p>
    <div class="fa-extrapolation__actions">
      <FaButton :loading="busy" data-testid="extrapolation-export-csv" @click="emit('export', 'csv')">{{ t('exportCsv') }}</FaButton>
      <FaButton :disabled="busy" data-testid="extrapolation-export-json" @click="emit('export', 'json')">{{ t('exportJson') }}</FaButton>
    </div>
  </section>
</template>
