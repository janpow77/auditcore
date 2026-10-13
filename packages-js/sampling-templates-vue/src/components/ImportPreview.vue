<script setup lang="ts">
import { EMPTY_VALUE } from '@auditcore/common'
import type { CellValue, MessageKey, Translate } from '@auditcore/sampling-templates-core'
import type { ImportDifference, ImportIssue, ImportReason } from '@auditcore/sampling-templates-core/xlsx'
import { FaButton, FaDialog, type Locale } from '@auditcore/ui'

/** Vorschau vor der Übernahme einer ausgefüllten Excel-Vorlage: was übernommen, umgedeutet oder nicht übernommen wird. */
export interface ImportPreviewData {
  file: string
  /** Blätter mit Werten. */
  sheets: readonly string[]
  /** Anzahl der übernommenen Eingaben. */
  count: number
  pending: readonly string[]
  issues: readonly ImportIssue[]
  differences: readonly ImportDifference[]
}

defineProps<{ preview: ImportPreviewData | null; t: Translate; locale?: Locale }>()
defineEmits<{ apply: []; cancel: [] }>()

const REASONS: Readonly<Record<ImportReason, MessageKey>> = {
  normalized: 'importReasonNormalized',
  'number-from-text': 'importReasonNumberFromText',
  'formula-value': 'importReasonFormulaValue',
  'number-as-text': 'importReasonNumberAsText',
  'not-in-list': 'importReasonNotInList',
  'not-a-number': 'importReasonNotANumber',
  unsupported: 'importReasonUnsupported',
}
const shown = (value: CellValue): string => (value === null ? EMPTY_VALUE : String(value))
</script>

<template>
  <FaDialog :open="preview !== null" :title="t('importTitle')" size="lg" :close-on-backdrop="false" :locale="locale" @update:open="$emit('cancel')">
    <div v-if="preview" class="fa-st__import" data-import-preview>
      <p>{{ t('importLead', { file: preview.file, count: preview.count, sheets: preview.sheets.join(', ') }) }}</p>
      <p v-if="preview.pending.length" class="fa-st__muted">{{ t('importPending', { sheets: preview.pending.join(', ') }) }}</p>
      <h3 class="fa-st__caption">{{ t('importIssues') }}</h3>
      <p v-if="preview.issues.length === 0" class="fa-st__muted">{{ t('importNoIssues') }}</p>
      <div v-else class="fa-st__strata-scroll" role="region" tabindex="0" :aria-label="t('importIssues')">
        <table class="fa-st__units-table" data-import-issues>
          <thead>
            <tr>
              <th scope="col">{{ t('importColumnSheet') }}</th>
              <th scope="col">{{ t('importColumnCell') }}</th>
              <th scope="col">{{ t('importColumnFound') }}</th>
              <th scope="col">{{ t('importColumnReason') }}</th>
              <th scope="col">{{ t('importColumnUsed') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="issue in preview.issues" :key="`${issue.sheet}-${issue.cell}`">
              <td>{{ issue.sheet }}</td>
              <th scope="row">{{ issue.cell }} · {{ issue.label }}</th>
              <td>{{ issue.found }}</td>
              <td>{{ t(REASONS[issue.reason]) }}</td>
              <td>{{ issue.used === null ? t('importNotUsed') : issue.used }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <h3 class="fa-st__caption">{{ t('importDifferences') }}</h3>
      <p v-if="preview.differences.length === 0" class="fa-st__muted">{{ t('importNoDifferences') }}</p>
      <div v-else class="fa-st__strata-scroll" role="region" tabindex="0" :aria-label="t('importDifferences')">
        <table class="fa-st__units-table" data-import-differences>
          <thead>
            <tr>
              <th scope="col">{{ t('importColumnSheet') }}</th>
              <th scope="col">{{ t('importColumnCell') }}</th>
              <th scope="col">{{ t('importColumnFound') }}</th>
              <th scope="col">{{ t('importColumnComputed') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="difference in preview.differences" :key="`${difference.sheet}-${difference.cell}`">
              <td>{{ difference.sheet }}</td>
              <th scope="row">{{ difference.cell }} · {{ difference.label }}</th>
              <td>{{ shown(difference.workbook) }}</td>
              <td>{{ difference.computed === null ? t('missing') : difference.computed }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <template #footer>
      <FaButton :label="t('cancel')" @click="$emit('cancel')" />
      <FaButton variant="primary" :label="t('importApply')" data-action="import-apply" @click="$emit('apply')" />
    </template>
  </FaDialog>
</template>
