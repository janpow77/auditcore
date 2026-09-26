<script setup lang="ts">
import { computed } from 'vue'
import { useId } from '../composables/useId'
import FaButton from '../base/FaButton.vue'
import { useI18n, type Locale } from '../i18n'
import { tabularMessages } from './messages'
import { useTableImport, type ImportedColumns } from './useTableImport'

const props = withDefaults(defineProps<{
  /** `items`: zusätzlich Kennungs- und Schichtspalte wählbar. */
  mode?: 'values' | 'items'
  locale?: Locale
}>(), { mode: 'values', locale: undefined })

const emit = defineEmits<{ import: [columns: ImportedColumns] }>()
const { t } = useI18n(tabularMessages, () => props.locale)
const state = useTableImport()
const id = useId('fa-import')
const delimiterLabel = computed(() => (state.table.value?.delimiter === '\t' ? t('tab') : state.table.value?.delimiter ?? ''))
const rejectedLines = computed(() => (state.preview.value?.rejected ?? []).slice(0, 10).join(', '))

async function onFile(event: Event): Promise<void> {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file) await state.read(file)
}

function optionalColumn(value: string): number | null {
  return value === '' ? null : Number(value)
}

function apply(): void {
  if (state.preview.value) emit('import', state.preview.value)
}
</script>

<template>
  <div class="fa-import">
    <label :for="`${id}-file`" class="fa-import__label">{{ t('file') }}</label>
    <input :id="`${id}-file`" class="fa-import__file" type="file" accept=".csv,.tsv,.txt,text/csv,text/plain" @change="onFile" />
    <template v-if="state.table.value">
      <p class="fa-import__note" aria-live="polite">
        {{ t('summary', { file: state.filename.value, rows: state.table.value.rows.length, delimiter: delimiterLabel }) }}
      </p>
      <div class="fa-import__grid">
        <label class="fa-import__check">
          <input v-model="state.hasHeader.value" type="checkbox" @change="state.reparse()" />
          {{ t('header') }}
        </label>
        <label class="fa-import__field">
          <span>{{ t('valueColumn') }}</span>
          <select v-model.number="state.valueColumn.value">
            <option v-for="(name, index) in state.table.value.header" :key="index" :value="index">{{ name }}</option>
          </select>
        </label>
        <template v-if="mode === 'items'">
          <label class="fa-import__field">
            <span>{{ t('idColumn') }}</span>
            <select :value="state.idColumn.value ?? ''" @change="state.idColumn.value = optionalColumn(($event.target as HTMLSelectElement).value)">
              <option value="">{{ t('none') }}</option>
              <option v-for="(name, index) in state.table.value.header" :key="index" :value="index">{{ name }}</option>
            </select>
          </label>
          <label class="fa-import__field">
            <span>{{ t('stratumColumn') }}</span>
            <select :value="state.stratumColumn.value ?? ''" @change="state.stratumColumn.value = optionalColumn(($event.target as HTMLSelectElement).value)">
              <option value="">{{ t('none') }}</option>
              <option v-for="(name, index) in state.table.value.header" :key="index" :value="index">{{ name }}</option>
            </select>
          </label>
        </template>
        <label class="fa-import__field">
          <span>{{ t('decimal') }}</span>
          <select v-model="state.decimal.value">
            <option value=",">{{ t('decimalComma') }}</option>
            <option value=".">{{ t('decimalDot') }}</option>
          </select>
        </label>
      </div>
      <p v-if="state.preview.value?.rejected.length" class="fa-import__warning" role="status">
        {{ t('rejected', { count: state.preview.value.rejected.length, lines: rejectedLines }) }}
      </p>
      <FaButton variant="secondary" :label="t('apply')" data-testid="import-apply" @click="apply">{{ t('apply') }}</FaButton>
    </template>
  </div>
</template>

<style>
.fa-import { display: flex; flex-direction: column; gap: var(--fa-space-2); font: var(--fa-font-size-sm) / var(--fa-line-height) var(--fa-font-sans); color: var(--fa-color-text); }
.fa-import__label, .fa-import__field > span { font-size: var(--fa-font-size-xs); font-weight: 600; color: var(--fa-color-text-muted); }
.fa-import__file { font: inherit; }
.fa-import__file:focus-visible, .fa-import select:focus-visible, .fa-import input[type='checkbox']:focus-visible { outline: none; box-shadow: var(--fa-focus-ring); }
.fa-import__grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(11rem, 1fr)); gap: var(--fa-space-3); align-items: end; }
.fa-import__field { display: flex; flex-direction: column; gap: var(--fa-space-1); }
.fa-import select { min-height: 2.25rem; padding: 0 var(--fa-space-2); border: 1px solid var(--fa-color-border); border-radius: var(--fa-radius); background: var(--fa-color-surface); color: var(--fa-color-text); font: inherit; }
.fa-import__check { display: inline-flex; gap: var(--fa-space-2); align-items: center; }
.fa-import__note { margin: 0; color: var(--fa-color-text-muted); }
.fa-import__warning { margin: 0; padding: var(--fa-space-2) var(--fa-space-3); border-radius: var(--fa-radius); background: var(--fa-color-warning-soft); color: var(--fa-color-warning); }
</style>
