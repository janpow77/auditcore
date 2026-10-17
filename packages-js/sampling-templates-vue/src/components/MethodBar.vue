<script setup lang="ts">
import { WORKFLOW_STEPS, findAvailableSheet, tableOf, type MessageKey, type MethodDefinition, type SheetModule, type Translate, type WorkflowStep } from '@auditcore/sampling-templates-core'
import { FaButton } from '@auditcore/ui'
import { computed } from 'vue'

/**
 * Schrittleiste des Assistenten (nummerierte Arbeitsschritte der Vorlage) und das
 * gewählte Verfahren als Kapsel mit dem Teilschritt „Verfahren wählen“ bzw.
 * „Parameter und Ergebnis“.
 */
const props = withDefaults(defineProps<{ definition: MethodDefinition | null; step: WorkflowStep['id']; sheets: readonly SheetModule[]; t: Translate; choosing?: boolean }>(), { choosing: false })
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
    <nav class="fa-st__stepnav" :aria-label="t('steps')">
      <ol class="fa-st__steps">
        <li v-for="(entry, index) in WORKFLOW_STEPS" :key="entry.id">
          <button type="button" class="fa-st__step" :data-step="entry.id" :aria-current="entry.id === step ? 'step' : undefined" :aria-disabled="isReady(entry) ? undefined : 'true'" :title="isReady(entry) ? undefined : t('notAvailable')" @click="choose(entry)">
            <span class="fa-st__step-no" aria-hidden="true">{{ index + 1 }}</span>
            <span>{{ t(STEP_KEYS[entry.id]) }}<span v-if="!isReady(entry)" class="fa-st__step-note" data-step-follows> · {{ t('stepFollows') }}</span></span>
          </button>
        </li>
      </ol>
    </nav>
    <div v-if="step === 'method'" class="fa-st__substeps" data-substeps>
      <span class="fa-st__substep" :aria-current="choosing ? 'step' : undefined">{{ t('substepChoose') }}</span>
      <span class="fa-st__substep-sep" aria-hidden="true">›</span>
      <span class="fa-st__substep" :aria-current="!choosing && definition ? 'step' : undefined">{{ t('substepParameters') }}</span>
    </div>
    <div v-if="definition && !choosing" class="fa-st__chip">
      <strong>{{ definition.shortTitle }}</strong>
      <FaButton size="sm" :label="t('changeMethod')" @click="$emit('change')" />
      <FaButton v-for="sheet in tables" :key="sheet" size="sm" :label="t('showTable', { name: tableOf(sheet, sheets)?.title ?? sheet })" :data-action="`table-${sheet}`" @click="emit('table', sheet)" />
    </div>
  </div>
</template>
