<script setup lang="ts">
import { computed } from 'vue'
import { identifierColumnFields, identifierErrorKey, importOptionalColumn } from '@auditcore/ui-core'
import FaButton from '../base/FaButton.vue'
import { useIdentifierContext } from './context'
import IdentifierBatchResult from './IdentifierBatchResult.vue'

const { view, t, id } = useIdentifierContext()
const { controller, state, table, kinds, mapping } = view
const columns = computed(() => identifierColumnFields(mapping.value))

async function onFile(event: Event): Promise<void> {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file) await controller.readFile(file)
}

const selected = (event: Event): string => (event.target as HTMLSelectElement).value
const checked = (event: Event): boolean => (event.target as HTMLInputElement).checked
</script>

<template>
  <section class="fa-ident__card" :aria-labelledby="`${id}-batch`">
    <h3 :id="`${id}-batch`" class="fa-ident__heading">{{ t('batch') }}</h3>
    <p class="fa-ident__muted">{{ t('batchHelp') }}</p>
    <label :for="`${id}-file`" class="fa-ident__label">{{ t('file') }}</label>
    <input :id="`${id}-file`" class="fa-ident__file" type="file" accept=".csv,.tsv,.txt,text/csv,text/plain" data-testid="ident-file" @change="onFile" />
    <form v-if="table.table" class="fa-ident__form" novalidate @submit.prevent="controller.checkBatch">
      <p class="fa-ident__muted" aria-live="polite">{{ t('tableSummary', { file: table.filename, rows: table.table.rows.length }) }}</p>
      <label class="fa-ident__check">
        <input type="checkbox" :checked="table.hasHeader" data-testid="ident-header" @change="controller.setHasHeader(checked($event))" />
        {{ t('header') }}
      </label>
      <label class="fa-ident__field">
        <span class="fa-ident__label">{{ t('kindSource') }}</span>
        <select :value="state.batchKind ?? ''" class="fa-ident__select" data-testid="ident-batch-kind" @change="controller.setBatchKind(selected($event) || null)">
          <option value="">{{ t('fromColumn') }}</option>
          <option v-for="entry in kinds" :key="entry.id" :value="entry.id">{{ entry.label }}</option>
        </select>
      </label>
      <label v-for="field in columns" :key="field.id" class="fa-ident__field">
        <span class="fa-ident__label">{{ t(field.label) }}</span>
        <select :value="field.value ?? ''" class="fa-ident__select" :data-testid="`ident-col-${field.id}`" @change="controller.setColumn(field.id, importOptionalColumn(selected($event)))">
          <option v-if="field.placeholder" value="">{{ t(field.placeholder) }}</option>
          <option v-for="(name, index) in table.table.header" :key="index" :value="index">{{ name }}</option>
        </select>
      </label>
      <p v-if="state.batchValidation" class="fa-ident__error" role="alert">{{ t(identifierErrorKey(state.batchValidation)) }}</p>
      <FaButton variant="primary" type="submit" :loading="state.busy === 'batch'" data-testid="ident-batch-run">{{ t('batchRun') }}</FaButton>
    </form>
    <IdentifierBatchResult v-if="state.batch" :answer="state.batch" />
  </section>
</template>
