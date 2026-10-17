<script setup lang="ts">
import { buildDataTable, type DataTable, type Translate } from '@auditcore/sampling-templates-core'
import { FaButton, FaDialog, type Locale } from '@auditcore/ui'
import { computed } from 'vue'

/**
 * Nachschlagetabelle der Vorlage (Blatt X1a) als Dialog: reine Anzeige, kein
 * Rechenblatt. Die Tabelle rollt in ihrem eigenen Bereich und ist per Tastatur erreichbar.
 */
const props = defineProps<{ table: DataTable | null; t: Translate; locale?: Locale }>()
defineEmits<{ close: [] }>()

const view = computed(() => (props.table ? buildDataTable(props.table) : null))
</script>

<template>
  <FaDialog :open="view !== null" :title="view?.title ?? ''" size="lg" :locale="locale" @update:open="$emit('close')">
    <div v-if="view" class="fa-st__datatable fa-st__scope" data-table>
      <p class="fa-st__muted">{{ t('dataTable') }} · {{ t('tableSource', { source: view.source }) }}</p>
      <div class="fa-st__datatable-scroll" role="region" tabindex="0" :aria-label="t('tableScroll')">
        <table class="fa-st__datatable-table">
          <caption class="fa-sr-only">{{ view.title }}</caption>
          <thead>
            <tr v-if="view.groups.length">
              <template v-for="(group, index) in view.groups" :key="index">
                <th v-if="group.label" :colspan="group.span" scope="colgroup">{{ group.label }}</th>
                <td v-else :colspan="group.span"></td>
              </template>
            </tr>
            <tr>
              <th v-for="column in view.columns" :key="column.key" scope="col">{{ column.label }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in view.rows" :key="index">
              <template v-for="(value, position) in row" :key="position">
                <th v-if="position === 0" scope="row">{{ value }}</th>
                <td v-else>{{ value }}</td>
              </template>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-for="note in view.notes" :key="note" class="fa-st__hint">{{ note }}</p>
    </div>
    <template #footer>
      <FaButton :label="t('close')" data-action="table-close" @click="$emit('close')" />
    </template>
  </FaDialog>
</template>
