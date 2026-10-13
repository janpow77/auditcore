<script setup lang="ts">
import { WORKFLOW_STEPS, findAvailableSheet, tableOf, type MessageKey, type MethodDefinition, type SheetModule, type Translate, type WorkflowStep } from '@auditcore/sampling-templates-core'
import { FaButton } from '@auditcore/ui'
import { computed } from 'vue'

/** Gewähltes Verfahren als Kapsel und die Arbeitsschritte der Vorlage zum Umschalten. */
const props = defineProps<{ definition: MethodDefinition | null; step: WorkflowStep['id']; sheets: readonly SheetModule[]; t: Translate }>()
const emit = defineEmits<{ change: []; step: [id: WorkflowStep['id']]; table: [sheet: string] }>()

/** Nachschlagetabellen des gewählten Verfahrens, die im Blattbestand als Datentabelle vorliegen. */
const tables = computed(() => (props.definition?.tables ?? []).filter((sheet) => tableOf(sheet, props.sheets) !== undefined))

const STEP_KEYS: Readonly<Record<WorkflowStep['id'], MessageKey>> = {
  population: 'stepPopulation',
  method: 'stepMethod',
  subsamples: 'stepSubsamples',
  totalErrorRate: 'stepTotalErrorRate',
  report: 'stepReport',
}
/** Ein Schritt ist bedienbar, sobald sein Blatt einen Rechenkern hat; „Verfahren“ immer. */
const isReady = (step: WorkflowStep): boolean => step.id === 'method' || (step.sheet !== undefined && findAvailableSheet(step.sheet, props.sheets) !== undefined)

function choose(step: WorkflowStep): void {
  if (isReady(step)) emit('step', step.id)
}
</script>

<template>
  <div class="fa-st__methodbar fa-st__inner">
    <div v-if="definition" class="fa-st__chip">
      <span class="fa-st__chip-no">{{ t('sheetNumber', { number: definition.number }) }}</span>
      <strong>{{ definition.shortTitle }}</strong>
      <FaButton size="sm" :label="t('changeMethod')" @click="$emit('change')" />
      <FaButton v-for="sheet in tables" :key="sheet" size="sm" :label="t('showTable', { name: tableOf(sheet, sheets)?.title ?? sheet })" :data-action="`table-${sheet}`" @click="emit('table', sheet)" />
    </div>
    <nav class="fa-st__stepnav" :aria-label="t('steps')">
      <ol class="fa-st__steps">
        <li v-for="entry in WORKFLOW_STEPS" :key="entry.id">
          <button type="button" class="fa-st__step" :data-step="entry.id" :aria-current="entry.id === step ? 'step' : undefined" :aria-disabled="isReady(entry) ? undefined : 'true'" :title="isReady(entry) ? undefined : t('notAvailable')" @click="choose(entry)">
            {{ t(STEP_KEYS[entry.id]) }}<span v-if="!isReady(entry)" class="fa-st__step-note" data-step-follows> · {{ t('stepFollows') }}</span>
          </button>
        </li>
      </ol>
    </nav>
  </div>
</template>
