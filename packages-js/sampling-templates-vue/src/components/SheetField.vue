<script setup lang="ts">
import type { CellAddress, CellValue, RowView, Translate } from '@auditcore/sampling-templates-core'
import { FaBadge, useId } from '@auditcore/ui'
import { computed } from 'vue'
import CellControl from './CellControl.vue'

/** Eine Zeile des Rechenblatts: Bezeichnung, Kurzformel, Fundstelle und das Bedienelement der Zelle. */
const props = defineProps<{ row: RowView; t: Translate }>()
defineEmits<{ update: [cell: CellAddress, value: CellValue] }>()

const id = useId('fa-st-field')
const isInput = computed(() => props.row.control === 'text' || props.row.control === 'number' || props.row.control === 'select')
</script>

<template>
  <div class="fa-st__row" :class="{ 'fa-st__row--output': !isInput, 'fa-st__row--key': row.key }" :data-cell="row.cell">
    <div class="fa-st__label">
      <label v-if="isInput" class="fa-st__label-text" :for="id">{{ row.type === 'percent' ? `${row.label} ${t('percentSuffix')}` : row.label }}</label>
      <span v-else class="fa-st__label-text">{{ row.label }}</span>
      <span v-if="row.formula" class="fa-st__formula">{{ row.formula }}</span>
      <span v-if="row.hint" :id="`${id}-hint`" class="fa-st__hint">{{ row.hint }}</span>
      <span v-if="row.link" class="fa-st__hint" data-link>{{ row.link.overridden ? t('overridden') : t('linked', { sheet: row.link.sheet }) }}</span>
      <span v-if="row.subsample && isInput" class="fa-st__hint">{{ t('subsampleTarget') }}</span>
      <span v-if="row.web" class="fa-st__hint"><FaBadge class="fa-st__tag" :label="t('webHint')" /></span>
      <span v-if="row.interpretation" class="fa-st__hint"><FaBadge class="fa-st__tag" tone="accent" :label="t('interpretation')" /> {{ row.interpretation }}</span>
    </div>
    <div class="fa-st__control">
      <CellControl :id="id" :row="row" :cell="row" :t="t" :described-by="row.hint ? `${id}-hint` : undefined" @update="(cell, value) => $emit('update', cell, value)" />
    </div>
  </div>
</template>
