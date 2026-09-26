<script setup lang="ts">
import { computed } from 'vue'
import { itemsFromImport, populationText, samplingMessages, type ImportedColumns, type PopulationItem } from '@flowaudit/ui-core'
import { useId } from '../composables/useId'
import { useI18n, type Locale } from '../i18n'
import TableImport from '../tabular/TableImport.vue'

const props = withDefaults(defineProps<{ items: readonly PopulationItem[]; locale?: Locale }>(), { locale: undefined })
const emit = defineEmits<{ import: [items: PopulationItem[]] }>()
const { t, locale: active } = useI18n(samplingMessages, () => props.locale)
const id = useId('fa-sampling-population')
const summary = computed(() => populationText(props.items, t, active.value))

function onImport(columns: ImportedColumns): void {
  emit('import', itemsFromImport(columns))
}
</script>

<template>
  <section class="fa-sampling__card" :aria-labelledby="`${id}-title`">
    <h3 :id="`${id}-title`" class="fa-sampling__heading">{{ t('population') }}</h3>
    <p v-if="items.length" class="fa-sampling__muted" data-testid="sampling-population">{{ summary }}</p>
    <p v-else class="fa-sampling__muted">{{ t('populationEmpty') }}</p>
    <TableImport mode="items" :locale="locale" @import="onImport" />
  </section>
</template>
