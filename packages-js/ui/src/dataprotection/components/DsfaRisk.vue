<script setup lang="ts">
import { computed } from 'vue'
import FaBadge from '../../base/FaBadge.vue'
import FaButton from '../../base/FaButton.vue'
import { useId } from '../../composables/useId'
import { useI18n } from '../../i18n'
import { addScenario, bandTone, removeScenario, withScenario } from '../dsfaView'
import { dataprotectionMessages } from '../messages'
import type { DataProtectionProfile, Proposal, SurveyInput } from '../types'
import DsfaScenario from './DsfaScenario.vue'

const props = withDefaults(defineProps<{
  profile: DataProtectionProfile
  survey: SurveyInput
  proposal?: Proposal | null
  preview?: boolean
  readonly?: boolean
}>(), { proposal: null, preview: false, readonly: false })

const emit = defineEmits<{ 'survey-change': [survey: SurveyInput] }>()
const { t } = useI18n(dataprotectionMessages)
const id = useId('fa-dsfa-risk')
const risk = computed(() => props.proposal?.risk ?? null)
const texts = computed(() => [
  { key: 'necessity' as const, label: t('necessity') },
  { key: 'proportionality' as const, label: t('proportionality') },
])

function setText(key: 'necessity' | 'proportionality', value: string): void {
  emit('survey-change', { ...props.survey, [key]: value })
}

function setDossier(key: string, value: string): void {
  emit('survey-change', { ...props.survey, dossier: { ...(props.survey.dossier ?? {}), [key]: value } })
}
</script>

<template>
  <div data-testid="dsfa-risk">
    <section class="fa-dataprotection__panel" :aria-label="t('scenarios')">
      <div class="fa-dataprotection__bar">
        <h3>{{ t('scenarios') }}</h3>
        <template v-if="risk && risk.scenarios.length">
          <FaBadge :tone="bandTone(risk.net_band, profile.risk.bands)">{{ risk.net_band }}</FaBadge>
          <span aria-live="polite">{{ t('riskSummary', { gross: risk.gross_maximum, net: risk.net_maximum, band: risk.net_band }) }}</span>
        </template>
        <FaBadge v-if="preview" tone="accent">{{ t('preview') }}</FaBadge>
      </div>
      <p v-if="!survey.scenarios.length" class="fa-dataprotection__muted">{{ t('noScenarios') }}</p>
      <DsfaScenario
        v-for="(scenario, index) in survey.scenarios"
        :key="index"
        :profile="profile"
        :scenario="scenario"
        :index="index"
        :result="risk?.scenarios[index] ?? null"
        :readonly="readonly"
        @scenario-change="emit('survey-change', withScenario(survey, index, $event))"
        @remove="emit('survey-change', removeScenario(survey, index))"
      />
      <FaButton v-if="!readonly" icon="plus" :label="t('addScenario')" @click="emit('survey-change', addScenario(survey, profile))" />
    </section>
    <section class="fa-dataprotection__panel" :aria-label="t('necessityTitle')">
      <h3>{{ t('necessityTitle') }}</h3>
      <div v-for="entry in texts" :key="entry.key" class="fa-dataprotection__field">
        <label :for="`${id}-${entry.key}`">{{ entry.label }}</label>
        <textarea :id="`${id}-${entry.key}`" rows="3" :readonly="readonly" :value="survey[entry.key]" @input="setText(entry.key, ($event.target as HTMLTextAreaElement).value)" />
      </div>
    </section>
    <section v-if="profile.dossier_fields.length" class="fa-dataprotection__panel" :aria-label="t('dossierTitle')">
      <h3>{{ t('dossierTitle') }}</h3>
      <div class="fa-dataprotection__grid">
        <div v-for="field in profile.dossier_fields" :key="field.key" class="fa-dataprotection__field" :class="{ 'fa-dataprotection__field--required': field.required }">
          <label :for="`${id}-d-${field.key}`">{{ field.title }}</label>
          <select v-if="field.kind === 'choice'" :id="`${id}-d-${field.key}`" :disabled="readonly" :value="survey.dossier?.[field.key] ?? ''" @change="setDossier(field.key, ($event.target as HTMLSelectElement).value)">
            <option value="">{{ t('empty') }}</option>
            <option v-for="choice in field.choices" :key="choice.key" :value="choice.key">{{ choice.title }}</option>
          </select>
          <input v-else :id="`${id}-d-${field.key}`" :type="field.kind === 'date' ? 'date' : 'text'" :readonly="readonly" :value="survey.dossier?.[field.key] ?? ''" @input="setDossier(field.key, ($event.target as HTMLInputElement).value)" />
        </div>
      </div>
    </section>
  </div>
</template>
