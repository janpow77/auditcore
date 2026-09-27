<script setup lang="ts">
import { computed } from 'vue'
import type { DecimalSeparator } from '@auditcore/common'
import {
  batchchecksColumnFields,
  batchchecksHasTable,
  batchchecksSourceText,
  importOptionalColumn,
  type BatchchecksController,
  type BatchchecksData,
  type BatchchecksTranslate,
  type TableImportData,
} from '@auditcore/ui-core'
import FaButton from '../base/FaButton.vue'

const props = defineProps<{
  id: string
  controller: BatchchecksController
  state: BatchchecksData
  table: TableImportData
  t: BatchchecksTranslate
}>()

const hasTable = computed(() => batchchecksHasTable(props.state, props.table))
const columns = computed(() => batchchecksColumnFields(props.state))
const header = computed(() => props.table.table?.header ?? [])
const source = computed(() => batchchecksSourceText(props.state, props.table, props.t))
const max = computed(() => props.state.catalogue?.limits.max_documents ?? 0)

async function onFile(event: Event): Promise<void> {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file) await props.controller.readFile(file)
}

const value = (event: Event): string => (event.target as HTMLInputElement | HTMLSelectElement).value
const checked = (event: Event): boolean => (event.target as HTMLInputElement).checked
</script>

<template>
  <form class="fa-batchchecks__card" novalidate :aria-labelledby="`${id}-input`" @submit.prevent="controller.check">
    <h3 :id="`${id}-input`" class="fa-batchchecks__heading">{{ t('input') }}</h3>
    <label class="fa-batchchecks__field">
      <span class="fa-batchchecks__label">{{ t('file') }}</span>
      <input class="fa-batchchecks__file" type="file" accept=".csv,.tsv,.txt,.json,text/csv,text/plain,application/json" data-testid="batchchecks-file" @change="onFile" />
    </label>
    <p class="fa-batchchecks__muted">{{ t('fileHelp', { max }) }}</p>
    <p v-if="source" class="fa-batchchecks__muted" aria-live="polite" data-testid="batchchecks-source">{{ source }}</p>
    <fieldset v-if="hasTable" class="fa-batchchecks__card">
      <legend class="fa-batchchecks__subheading">{{ t('columns') }}</legend>
      <label class="fa-batchchecks__check">
        <input type="checkbox" :checked="table.hasHeader" data-testid="batchchecks-header" @change="controller.setHasHeader(checked($event))" />
        {{ t('header') }}
      </label>
      <div class="fa-batchchecks__grid">
        <label class="fa-batchchecks__field">
          <span class="fa-batchchecks__label">{{ t('decimal') }}</span>
          <select class="fa-batchchecks__input" :value="table.decimal" data-testid="batchchecks-decimal" @change="controller.setDecimal(value($event) as DecimalSeparator)">
            <option value=",">{{ t('decimalComma') }}</option>
            <option value=".">{{ t('decimalDot') }}</option>
          </select>
        </label>
        <label v-for="field in columns" :key="field.name" class="fa-batchchecks__field">
          <span class="fa-batchchecks__label">{{ field.label }}</span>
          <select class="fa-batchchecks__input" :value="field.value ?? ''" :data-testid="`batchchecks-col-${field.name}`" @change="controller.setColumn(field.name, importOptionalColumn(value($event)))">
            <option value="">{{ t('none') }}</option>
            <option v-for="(name, index) in header" :key="index" :value="index">{{ name }}</option>
          </select>
        </label>
      </div>
    </fieldset>
    <div class="fa-batchchecks__grid">
      <label class="fa-batchchecks__field">
        <span class="fa-batchchecks__label">{{ t('totalVolume') }}</span>
        <input class="fa-batchchecks__input" type="text" inputmode="decimal" :value="state.totalVolume" data-testid="batchchecks-total" @input="controller.setTotalVolume(value($event))" />
      </label>
      <label class="fa-batchchecks__check">
        <input type="checkbox" :checked="state.supplementary" data-testid="batchchecks-supplementary" @change="controller.setSupplementary(checked($event))" />
        {{ t('supplementary') }}
      </label>
    </div>
    <p class="fa-batchchecks__muted">{{ t('totalVolumeHelp') }}</p>
    <p v-if="state.validation" class="fa-batchchecks__error" role="alert">{{ t(`error${state.validation}`, { max }) }}</p>
    <div>
      <FaButton variant="primary" type="submit" :loading="state.busy === 'run'" data-testid="batchchecks-run">{{ t('run') }}</FaButton>
    </div>
  </form>
</template>
