<script setup lang="ts">
import { computed } from 'vue'
import type { DecimalSeparator } from '@flowaudit/common'
import { importDelimiterText, importOptionalColumn, importRejectedLines, tabularMessages, type ImportedColumns } from '@flowaudit/ui-core'
import { useId } from '../composables/useId'
import FaButton from '../base/FaButton.vue'
import { useI18n, type Locale } from '../i18n'
import { useTableImport } from './useTableImport'

const props = withDefaults(defineProps<{
  /** `items`: zusätzlich Kennungs- und Schichtspalte wählbar. */
  mode?: 'values' | 'items'
  locale?: Locale
}>(), { mode: 'values', locale: undefined })

const emit = defineEmits<{ import: [columns: ImportedColumns] }>()
const { t } = useI18n(tabularMessages, () => props.locale)
const { controller, state, preview } = useTableImport()
const id = useId('fa-import')
const delimiterLabel = computed(() => importDelimiterText(state.value.table, t('tab')))
const rejectedLines = computed(() => importRejectedLines(preview.value))

async function onFile(event: Event): Promise<void> {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file) await controller.read(file)
}

function onHeader(event: Event): void {
  controller.setHasHeader((event.target as HTMLInputElement).checked)
  controller.reparse()
}

const selected = (event: Event): string => (event.target as HTMLSelectElement).value

function apply(): void {
  if (preview.value) emit('import', preview.value)
}
</script>

<template>
  <div class="fa-import">
    <label :for="`${id}-file`" class="fa-import__label">{{ t('file') }}</label>
    <input :id="`${id}-file`" class="fa-import__file" type="file" accept=".csv,.tsv,.txt,text/csv,text/plain" @change="onFile" />
    <template v-if="state.table">
      <p class="fa-import__note" aria-live="polite">
        {{ t('summary', { file: state.filename, rows: state.table.rows.length, delimiter: delimiterLabel }) }}
      </p>
      <div class="fa-import__grid">
        <label class="fa-import__check">
          <input type="checkbox" :checked="state.hasHeader" @change="onHeader" />
          {{ t('header') }}
        </label>
        <label class="fa-import__field">
          <span>{{ t('valueColumn') }}</span>
          <select :value="state.valueColumn" @change="controller.setValueColumn(Number(selected($event)))">
            <option v-for="(name, index) in state.table.header" :key="index" :value="index">{{ name }}</option>
          </select>
        </label>
        <template v-if="mode === 'items'">
          <label class="fa-import__field">
            <span>{{ t('idColumn') }}</span>
            <select :value="state.idColumn ?? ''" @change="controller.setIdColumn(importOptionalColumn(selected($event)))">
              <option value="">{{ t('none') }}</option>
              <option v-for="(name, index) in state.table.header" :key="index" :value="index">{{ name }}</option>
            </select>
          </label>
          <label class="fa-import__field">
            <span>{{ t('stratumColumn') }}</span>
            <select :value="state.stratumColumn ?? ''" @change="controller.setStratumColumn(importOptionalColumn(selected($event)))">
              <option value="">{{ t('none') }}</option>
              <option v-for="(name, index) in state.table.header" :key="index" :value="index">{{ name }}</option>
            </select>
          </label>
        </template>
        <label class="fa-import__field">
          <span>{{ t('decimal') }}</span>
          <select :value="state.decimal" @change="controller.setDecimal(selected($event) as DecimalSeparator)">
            <option value=",">{{ t('decimalComma') }}</option>
            <option value=".">{{ t('decimalDot') }}</option>
          </select>
        </label>
      </div>
      <p v-if="preview?.rejected.length" class="fa-import__warning" role="status">
        {{ t('rejected', { count: preview.rejected.length, lines: rejectedLines }) }}
      </p>
      <FaButton variant="secondary" :label="t('apply')" data-testid="import-apply" @click="apply">{{ t('apply') }}</FaButton>
    </template>
  </div>
</template>
