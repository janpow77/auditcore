<script setup lang="ts">
import { computed } from 'vue'
import FaBadge from '../../base/FaBadge.vue'
import FaButton from '../../base/FaButton.vue'
import { useId } from '../../composables/useId'
import { useI18n } from '../../i18n'
import { bandTone, toggleMeasure } from '../dsfaView'
import { dataprotectionMessages } from '../messages'
import type { DataProtectionProfile, ScenarioInput, ScenarioResult } from '../types'

const props = withDefaults(defineProps<{
  profile: DataProtectionProfile
  scenario: ScenarioInput
  index: number
  result?: ScenarioResult | null
  readonly?: boolean
}>(), { result: null, readonly: false })

const emit = defineEmits<{ 'scenario-change': [scenario: ScenarioInput]; remove: [] }>()
const { t } = useI18n(dataprotectionMessages)
const id = useId('fa-dsfa-s')
const risk = computed(() => props.profile.risk)
const residual = computed(() => props.scenario.residual_severity !== null || props.scenario.residual_likelihood !== null)

function patch(changes: Partial<ScenarioInput>): void {
  emit('scenario-change', { ...props.scenario, ...changes })
}

function level(event: Event): number | null {
  const raw = (event.target as HTMLSelectElement).value
  return raw === '' ? null : Number(raw)
}
</script>

<template>
  <fieldset class="fa-dsfa__scenario" :disabled="readonly" :data-scenario="index">
    <legend class="fa-dataprotection__label">{{ t('scenario', { index: index + 1 }) }}</legend>
    <div class="fa-dataprotection__grid">
      <div class="fa-dataprotection__field">
        <label :for="`${id}-dim`">{{ t('dimension') }}</label>
        <select :id="`${id}-dim`" :value="scenario.dimension" @change="patch({ dimension: ($event.target as HTMLSelectElement).value })">
          <option v-for="dimension in risk.dimensions" :key="dimension.key" :value="dimension.key">{{ dimension.title }}</option>
        </select>
      </div>
      <div class="fa-dataprotection__field fa-dataprotection__field--required">
        <label :for="`${id}-text`">{{ t('description') }}</label>
        <textarea :id="`${id}-text`" rows="2" :value="scenario.description" @input="patch({ description: ($event.target as HTMLTextAreaElement).value })" />
      </div>
      <div class="fa-dataprotection__field">
        <label :for="`${id}-sev`">{{ t('severity') }}</label>
        <select :id="`${id}-sev`" :value="scenario.severity" @change="patch({ severity: level($event) ?? scenario.severity })">
          <option v-for="entry in risk.severity_levels" :key="entry.value" :value="entry.value">{{ entry.value }} – {{ entry.label }}</option>
        </select>
      </div>
      <div class="fa-dataprotection__field">
        <label :for="`${id}-lik`">{{ t('likelihood') }}</label>
        <select :id="`${id}-lik`" :value="scenario.likelihood" @change="patch({ likelihood: level($event) ?? scenario.likelihood })">
          <option v-for="entry in risk.likelihood_levels" :key="entry.value" :value="entry.value">{{ entry.value }} – {{ entry.label }}</option>
        </select>
      </div>
    </div>
    <fieldset class="fa-dataprotection__field">
      <legend>{{ t('measures') }}</legend>
      <ul class="fa-dsfa__measures">
        <li v-for="measure in risk.measures" :key="measure.key">
          <label class="fa-dataprotection__choice">
            <input type="checkbox" :checked="scenario.measures.includes(measure.key)" @change="emit('scenario-change', toggleMeasure(scenario, measure.key))" />
            {{ measure.title }}
          </label>
        </li>
      </ul>
    </fieldset>
    <details :open="residual">
      <summary>{{ t('residual') }}</summary>
      <div class="fa-dataprotection__grid">
        <div class="fa-dataprotection__field">
          <label :for="`${id}-rsev`">{{ t('residualSeverity') }}</label>
          <select :id="`${id}-rsev`" :value="scenario.residual_severity ?? ''" @change="patch({ residual_severity: level($event) })">
            <option value="">{{ t('computed') }}</option>
            <option v-for="entry in risk.severity_levels" :key="entry.value" :value="entry.value">{{ entry.value }} – {{ entry.label }}</option>
          </select>
        </div>
        <div class="fa-dataprotection__field">
          <label :for="`${id}-rlik`">{{ t('residualLikelihood') }}</label>
          <select :id="`${id}-rlik`" :value="scenario.residual_likelihood ?? ''" @change="patch({ residual_likelihood: level($event) })">
            <option value="">{{ t('computed') }}</option>
            <option v-for="entry in risk.likelihood_levels" :key="entry.value" :value="entry.value">{{ entry.value }} – {{ entry.label }}</option>
          </select>
        </div>
      </div>
      <div class="fa-dataprotection__field" :class="{ 'fa-dataprotection__field--required': residual }">
        <label :for="`${id}-why`">{{ t('residualJustification') }}</label>
        <textarea :id="`${id}-why`" rows="2" :value="scenario.residual_justification" @input="patch({ residual_justification: ($event.target as HTMLTextAreaElement).value })" />
      </div>
    </details>
    <div class="fa-dsfa__result">
      <template v-if="result">
        <FaBadge :tone="bandTone(result.gross_band, risk.bands)">{{ result.gross_band }}</FaBadge>
        <span aria-hidden="true">→</span>
        <FaBadge :tone="bandTone(result.net_band, risk.bands)">{{ result.net_band }}</FaBadge>
        <span>{{ t('scenarioResult', { gross: result.gross, grossBand: result.gross_band, net: result.net, netBand: result.net_band }) }}</span>
      </template>
      <FaButton v-if="!readonly" class="fa-dataprotection__actions" variant="ghost" size="sm" icon="trash" :label="t('removeScenario', { index: index + 1 })" @click="emit('remove')" />
    </div>
  </fieldset>
</template>
