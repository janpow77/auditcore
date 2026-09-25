<script setup lang="ts">
import { computed } from 'vue'
import { useId } from '../composables/useId'
import { formatNumber, useI18n, type Locale } from '../i18n'
import TableImport from '../tabular/TableImport.vue'
import type { ImportedColumns } from '../tabular/useTableImport'
import { samplingMessages } from './messages'
import { itemsFromImport, positiveSum, strataOf } from './model'
import type { PopulationItem } from './types'

const props = withDefaults(defineProps<{ items: readonly PopulationItem[]; locale?: Locale }>(), { locale: undefined })
const emit = defineEmits<{ import: [items: PopulationItem[]] }>()
const { t, locale: active } = useI18n(samplingMessages, () => props.locale)
const id = useId('fa-sampling-population')
const strata = computed(() => strataOf(props.items).length)

function onImport(columns: ImportedColumns): void {
  emit('import', itemsFromImport(columns))
}
</script>

<template>
  <section class="fa-sampling__card" :aria-labelledby="`${id}-title`">
    <h3 :id="`${id}-title`" class="fa-sampling__heading">{{ t('population') }}</h3>
    <p v-if="items.length" class="fa-sampling__muted" data-testid="sampling-population">
      {{ t('populationCount', { count: formatNumber(items.length, active), sum: formatNumber(positiveSum(items), active, { maximumFractionDigits: 2 }) }) }}
      <template v-if="strata"> · {{ t('strataCount', { count: strata }) }}</template>
    </p>
    <p v-else class="fa-sampling__muted">{{ t('populationEmpty') }}</p>
    <TableImport mode="items" :locale="locale" @import="onImport" />
  </section>
</template>
