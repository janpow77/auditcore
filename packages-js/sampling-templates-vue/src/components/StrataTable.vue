<script setup lang="ts">
import { MAX_STRATA, TEMPLATE_STRATA, type CellAddress, type CellValue, type RowView, type Translate } from '@auditcore/sampling-templates-core'
import { FaButton, useId } from '@auditcore/ui'
import CellControl from './CellControl.vue'

/**
 * Schichttabelle: aufeinanderfolgende Schichtzeilen eines Abschnitts als Tabelle
 * (Zeile = Größe, Spalte = Schicht) in einem eigenen waagerechten Rollbereich.
 * Schichten lassen sich hinzufügen und entfernen (`controls`, in der Regel nur an der
 * ersten Tabelle eines Blatts); ab der achten steht der Hinweis der Webfassung dabei.
 */
withDefaults(defineProps<{ rows: readonly RowView[]; count: number; t: Translate; controls?: boolean }>(), { controls: true })
defineEmits<{ update: [cell: CellAddress, value: CellValue]; add: []; remove: [] }>()

const id = useId('fa-st-strata')
const TEMPLATE_COUNT = TEMPLATE_STRATA.length
</script>

<template>
  <div class="fa-st__strata" data-strata>
    <div class="fa-st__strata-scroll" role="region" tabindex="0" :aria-label="t('strataScroll')">
      <table class="fa-st__strata-table">
        <caption class="fa-sr-only">{{ t('strataCaption') }}</caption>
        <thead>
          <tr>
            <td></td>
            <th scope="col">{{ t('strataTotal') }}</th>
            <th v-for="index in count" :key="index" scope="col">{{ t('stratum', { number: index }) }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.cell" :class="{ 'fa-st__row--key': row.key }" :data-row="row.cell">
            <th scope="row" class="fa-st__strata-label">
              <span class="fa-st__label-text">{{ row.type === 'percent' && row.kind === 'input' ? `${row.label} ${t('percentSuffix')}` : row.label }}</span>
              <span v-if="row.formula" class="fa-st__formula">{{ row.formula }}</span>
              <span v-if="row.hint" class="fa-st__hint">{{ row.hint }}</span>
            </th>
            <td :data-cell="row.strata?.total?.cell">
              <p v-if="row.strata?.total" class="fa-st__value" :class="{ 'fa-st__value--missing': row.strata.total.missing }">{{ row.strata.total.display }}</p>
            </td>
            <td v-for="(cell, index) in row.strata?.cells.slice(0, count)" :key="cell.cell" :data-cell="cell.cell">
              <CellControl :id="`${id}-${cell.cell}`" :row="row" :cell="cell" :t="t" :label="`${row.label} – ${t('stratum', { number: index + 1 })}`" @update="(address, value) => $emit('update', address, value)" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="controls" class="fa-st__strata-actions">
      <FaButton size="sm" icon="plus" :label="t('strataAdd')" :disabled="count >= MAX_STRATA" data-action="strata-add" @click="$emit('add')" />
      <FaButton size="sm" icon="minus" :label="t('strataRemove')" :disabled="count <= 1" data-action="strata-remove" @click="$emit('remove')" />
      <span class="fa-st__muted" role="status">{{ t('strataCount', { count, max: MAX_STRATA }) }}</span>
    </div>
    <p v-if="controls && count > TEMPLATE_COUNT" class="fa-st__hint" data-strata-note><strong>{{ t('webHint') }}:</strong> {{ t('strataBeyondTemplate') }}</p>
  </div>
</template>
