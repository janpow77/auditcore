<script setup lang="ts">
import type { Translate, Variant } from '@auditcore/sampling-templates-core'

/** Kachel einer Variante: Blattnummer, Name, Fundstelle und Entsprechung in der Vorlage von 2017. */
const props = defineProps<{ variant: Variant; available: boolean; t: Translate }>()
const emit = defineEmits<{ select: [sheet: string] }>()

function choose(): void {
  if (props.available) emit('select', props.variant.sheet)
}
</script>

<template>
  <button type="button" class="fa-st__tile" :aria-disabled="available ? undefined : 'true'" :data-sheet="variant.sheet" @click="choose">
    <span class="fa-st__tile-no">{{ t('sheetNumber', { number: variant.number }) }}<template v-if="!available"> · {{ t('notAvailable') }}</template></span>
    <span class="fa-st__tile-name">{{ variant.name }}</span>
    <span class="fa-st__tile-ref">{{ variant.reference }}</span>
    <span class="fa-st__tile-ref">{{ t('template2017', { name: variant.template2017 }) }}</span>
  </button>
</template>
