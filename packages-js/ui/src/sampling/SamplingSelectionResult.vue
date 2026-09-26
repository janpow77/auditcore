<script setup lang="ts">
import { computed } from 'vue'
import FaBadge from '../base/FaBadge.vue'
import FaButton from '../base/FaButton.vue'
import {
  excludedLines,
  samplingMessages,
  selectionColumns,
  selectionRows,
  selectionTexts,
  strataColumns as strataColumnsOf,
  strataRows as strataRowsOf,
  type ExportFormat,
  type SelectionResult,
} from '@auditcore/ui-core'
import { useI18n, type Locale } from '../i18n'
import FaTable from '../table/FaTable.vue'

const props = withDefaults(defineProps<{ result: SelectionResult; busy?: boolean; locale?: Locale }>(), {
  busy: false,
  locale: undefined,
})
const emit = defineEmits<{ export: [format: ExportFormat] }>()
const { t, locale: active } = useI18n(samplingMessages, () => props.locale)
const columns = computed(() => selectionColumns(props.result, t, active.value))
const strataColumns = computed(() => strataColumnsOf(props.result, t, active.value))
const strataRows = computed(() => strataRowsOf(props.result))
const rows = computed(() => selectionRows(props.result))
const excluded = computed(() => excludedLines(props.result, t))
const texts = computed(() => selectionTexts(props.result, t, active.value))
</script>

<template>
  <div class="fa-sampling__selection" aria-live="polite">
    <p class="fa-sampling__seed" data-testid="sampling-seed-used">
      <FaBadge tone="accent">{{ texts.seed }}</FaBadge>
      <span class="fa-sampling__muted">{{ texts.origin }}</span>
      <span>{{ texts.summary }}</span>
    </p>
    <p class="fa-sampling__hint">{{ texts.reproducible }}</p>
    <FaTable :columns="strataColumns" :rows="strataRows" :caption="t('allocationTable')" :locale="locale" data-testid="sampling-strata" />
    <ul v-if="excluded.length" class="fa-sampling__warnings">
      <li v-for="line in excluded" :key="line">{{ line }}</li>
    </ul>
    <FaTable :columns="columns" :rows="rows" row-key="order" :caption="t('selection')" :locale="locale" data-testid="sampling-rows" />
    <div class="fa-sampling__actions">
      <FaButton :loading="busy" data-testid="sampling-export-csv" @click="emit('export', 'csv')">{{ t('exportCsv') }}</FaButton>
      <FaButton :disabled="busy" data-testid="sampling-export-json" @click="emit('export', 'json')">{{ t('exportJson') }}</FaButton>
    </div>
  </div>
</template>
