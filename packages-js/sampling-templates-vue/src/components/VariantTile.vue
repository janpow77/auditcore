<script setup lang="ts">
import type { Translate, Variant } from '@auditcore/sampling-templates-core'

/**
 * Eintrag einer Variante in der Liste der Altvorlagen: Name, Fundstelle und
 * Entsprechung in der Vorlage von 2017. `table`: Das Blatt ist eine
 * Nachschlagetabelle – der Eintrag öffnet sie, als Verfahren wählbar ist er nicht.
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
    <span class="fa-st__tile-name">{{ variant.name }}<template v-if="table"> · {{ t('dataTable') }}</template><template v-else-if="!available"> · {{ t('notAvailable') }}</template></span>
    <span class="fa-st__tile-ref">{{ variant.reference }} · {{ t('template2017', { name: variant.template2017 }) }}</span>
  </button>
</template>
