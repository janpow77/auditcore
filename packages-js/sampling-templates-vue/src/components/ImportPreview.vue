<script setup lang="ts">
import { EMPTY_VALUE } from '@auditcore/common'
import type { CellValue, MessageKey, Translate } from '@auditcore/sampling-templates-core'
import type { ImportDifference, ImportIssue, ImportNote, ImportNoteKind, ImportReason } from '@auditcore/sampling-templates-core/workbook'
import { FaButton, FaDialog, type Locale } from '@auditcore/ui'
import { computed } from 'vue'

/** Vorschau vor der Übernahme einer ausgefüllten Excel-Vorlage: was übernommen, umgedeutet oder nicht übernommen wird. */
export interface ImportPreviewData {
  file: string
  /** Blätter mit Werten. */
  sheets: readonly string[]
  /** Anzahl der übernommenen Eingaben. */
  count: number
  pending: readonly string[]
  issues: readonly ImportIssue[]
  /** Blattweite Hinweise: ungelesene Schichtdaten, kein Methodenblatt gewählt, gelöschte Vorgaben, Kopien des Blatts 17. */
  notes: readonly ImportNote[]
  differences: readonly ImportDifference[]
}

const props = defineProps<{ preview: ImportPreviewData | null; t: Translate; locale?: Locale }>()
defineEmits<{ apply: []; cancel: [] }>()

const REASONS: Readonly<Record<ImportReason, MessageKey>> = {
  normalized: 'importReasonNormalized',
  'number-from-text': 'importReasonNumberFromText',
  'formula-value': 'importReasonFormulaValue',
  'number-as-text': 'importReasonNumberAsText',
  'not-in-list': 'importReasonNotInList',
  'not-a-number': 'importReasonNotANumber',
  'date-from-serial': 'importReasonDateFromSerial',
  unsupported: 'importReasonUnsupported',
}
const NOTES: Readonly<Record<ImportNoteKind, MessageKey>> = {
  'unread-cells': 'importNoteUnreadCells',
  'method-not-chosen': 'importNoteMethodNotChosen',
  'default-cleared': 'importNoteDefaultCleared',
  'list-copy': 'importNoteListCopy',
}
/** Echte Unterschiede zuerst; begründete („Angabe fehlt“, die Vorlage rechnet mit 0) stehen getrennt darunter. */
const real = computed(() => (props.preview?.differences ?? []).filter((difference) => !difference.explained))
const explained = computed(() => (props.preview?.differences ?? []).filter((difference) => difference.explained))
const shown = (value: CellValue): string => (value === null ? EMPTY_VALUE : String(value))
</script>

<template>
  <FaDialog :open="preview !== null" :title="t('importTitle')" size="lg" :close-on-backdrop="false" :locale="locale" @update:open="$emit('cancel')">
    <div v-if="preview" class="fa-st__import fa-st__scope" data-import-preview>
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
      <template v-if="preview.notes.length">
        <h3 class="fa-st__caption">{{ t('importNotes') }}</h3>
        <ul class="fa-st__notices fa-st__import-notes" data-import-notes>
          <li v-for="note in preview.notes" :key="`${note.kind}-${note.sheet}-${note.detail}`" class="fa-st__notice fa-st__notice--warning">
            <p>{{ t(NOTES[note.kind], { sheet: note.sheet, detail: note.detail }) }}</p>
          </li>
        </ul>
      </template>
      <h3 class="fa-st__caption">{{ t('importDifferences') }}</h3>
      <p v-if="real.length === 0" class="fa-st__muted">{{ t('importNoDifferences') }}</p>
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
            <tr v-for="difference in real" :key="`${difference.sheet}-${difference.cell}`">
              <td>{{ difference.sheet }}</td>
              <th scope="row">{{ difference.cell }} · {{ difference.label }}</th>
              <td>{{ difference.workbook === null ? t('importWorkbookEmpty') : shown(difference.workbook) }}</td>
              <td>{{ difference.computed === null ? t('missing') : difference.computed }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <details v-if="explained.length" class="fa-st__import-explained" data-import-explained>
        <summary>{{ t('importExplained', { count: explained.length }) }}</summary>
        <div class="fa-st__strata-scroll" role="region" tabindex="0" :aria-label="t('importExplained', { count: explained.length })">
          <table class="fa-st__units-table">
            <thead>
              <tr>
                <th scope="col">{{ t('importColumnSheet') }}</th>
                <th scope="col">{{ t('importColumnCell') }}</th>
                <th scope="col">{{ t('importColumnFound') }}</th>
                <th scope="col">{{ t('importColumnComputed') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="difference in explained" :key="`${difference.sheet}-${difference.cell}`">
                <td>{{ difference.sheet }}</td>
                <th scope="row">{{ difference.cell }} · {{ difference.label }}</th>
                <td>{{ shown(difference.workbook) }}</td>
                <td>{{ t('missing') }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </details>
    </div>
    <template #footer>
      <FaButton :label="t('cancel')" @click="$emit('cancel')" />
      <FaButton variant="primary" :label="t('importApply')" data-action="import-apply" @click="$emit('apply')" />
    </template>
  </FaDialog>
</template>
