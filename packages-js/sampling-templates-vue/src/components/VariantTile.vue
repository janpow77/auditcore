<script setup lang="ts">
import type { Translate, Variant } from '@auditcore/sampling-templates-core'

/**
 * Kachel einer Variante: Blattnummer, Name, Fundstelle und Entsprechung in der
 * Vorlage von 2017. `table`: Das Blatt ist eine Nachschlagetabelle – die Kachel
 * öffnet sie, als Verfahren wählbar ist sie nicht.
 */
const props = withDefaults(defineProps<{ variant: Variant; available: boolean; t: Translate; table?: boolean }>(), { table: false })
const emit = defineEmits<{ select: [sheet: string]; table: [sheet: string] }>()

function choose(): void {
  if (props.table) emit('table', props.variant.sheet)
  else if (props.available) emit('select', props.variant.sheet)
}
</script>

<template>
  <button type="button" class="fa-st__tile" :aria-disabled="available || table ? undefined : 'true'" :data-sheet="variant.sheet" :data-table-sheet="table ? variant.sheet : undefined" @click="choose">
    <span class="fa-st__tile-no">{{ t('sheetNumber', { number: variant.number }) }}<template v-if="table"> · {{ t('dataTable') }}</template><template v-else-if="!available"> · {{ t('notAvailable') }}</template></span>
    <span class="fa-st__tile-name">{{ variant.name }}</span>
    <span class="fa-st__tile-ref">{{ variant.reference }}</span>
    <span class="fa-st__tile-ref">{{ t('template2017', { name: variant.template2017 }) }}</span>
  </button>
</template>
