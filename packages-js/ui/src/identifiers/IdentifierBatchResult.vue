<script setup lang="ts">
import { computed } from 'vue'
import { downloadText, identifierBatchCsv, identifierBatchLines, identifierBatchSummary, type IdentifierBatchAnswer } from '@auditcore/ui-core'
import FaButton from '../base/FaButton.vue'
import { useIdentifierContext } from './context'

const props = defineProps<{ answer: IdentifierBatchAnswer }>()
const { view, t } = useIdentifierContext()
const { controller, state } = view
const lines = computed(() => (state.value.catalogue ? identifierBatchLines(state.value.catalogue, props.answer, state.value.batchRequest, state.value.onlyIssues, t) : []))

function exportCsv(): void {
  const catalogue = state.value.catalogue
  if (catalogue) downloadText(identifierBatchCsv(catalogue, props.answer, state.value.batchRequest, t), 'kennungspruefung.csv', 'text/csv;charset=utf-8')
}

const checked = (event: Event): boolean => (event.target as HTMLInputElement).checked
</script>

<template>
  <div class="fa-ident__batch" aria-live="polite" data-testid="ident-batch-result">
    <p class="fa-ident__summary">{{ identifierBatchSummary(answer, t) }}</p>
    <div class="fa-ident__actions">
      <label class="fa-ident__check">
        <input type="checkbox" :checked="state.onlyIssues" data-testid="ident-only-issues" @change="controller.setField('onlyIssues', checked($event))" />
        {{ t('onlyInvalid') }}
      </label>
      <FaButton data-testid="ident-export" @click="exportCsv">{{ t('export') }}</FaButton>
    </div>
    <div class="fa-ident__scroll">
      <table class="fa-ident__table">
        <thead>
          <tr>
            <th scope="col">{{ t('colRef') }}</th>
            <th scope="col">{{ t('colKind') }}</th>
            <th scope="col">{{ t('colValue') }}</th>
            <th scope="col">{{ t('colStatus') }}</th>
            <th scope="col">{{ t('colReason') }}</th>
            <th scope="col">{{ t('colNormalized') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="line in lines" :key="line.key">
            <td>{{ line.ref }}</td>
            <td>{{ line.kind }}</td>
            <td><code>{{ line.value }}</code></td>
            <td><span :class="['fa-ident__badge', `fa-ident__badge--${line.tone}`]">{{ line.status }}</span></td>
            <td>{{ line.reason }}</td>
            <td><code>{{ line.normalized }}</code></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
