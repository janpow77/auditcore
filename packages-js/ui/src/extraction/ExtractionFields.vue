<script setup lang="ts">
import {
  extractionConfidenceText,
  extractionConfidenceTone,
  extractionDecisionText,
  extractionDecisionTone,
  extractionFieldLabel,
  extractionProposalText,
  extractionValueText,
  type ExtractedField,
  type ExtractionTranslate,
  type Locale,
} from '@flowaudit/ui-core'
import FaBadge from '../base/FaBadge.vue'

defineProps<{
  fields: readonly ExtractedField[]
  threshold: number | null
  t: ExtractionTranslate
  locale: Locale
}>()
</script>

<template>
  <h4 class="fa-extraction__heading">{{ t('fields') }}</h4>
  <p class="fa-extraction__muted">{{ t('confidenceHelp') }}</p>
  <p v-if="!fields.length" class="fa-extraction__muted">{{ t('noFields') }}</p>
  <div v-else class="fa-extraction__scroll">
    <table class="fa-extraction__table" data-testid="extraction-fields">
      <thead>
        <tr>
          <th scope="col">{{ t('colField') }}</th>
          <th scope="col">{{ t('colValue') }}</th>
          <th scope="col">{{ t('colConfidence') }}</th>
          <th scope="col">{{ t('colDecision') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="field in fields" :key="field.name" :data-field="field.name">
          <th scope="row">{{ extractionFieldLabel(field.name, t) }}</th>
          <td>{{ extractionValueText(field.value, locale) || t('noValue') }}</td>
          <td class="fa-extraction__number">
            <FaBadge v-if="field.confidence !== null" :tone="extractionConfidenceTone(field.confidence, threshold)">{{ extractionConfidenceText(field.confidence, locale) }}</FaBadge>
            <template v-else>{{ t('noValue') }}</template>
          </td>
          <td>
            <FaBadge v-if="field.decision" :tone="extractionDecisionTone(field)">{{ extractionDecisionText(field, t) }}</FaBadge>
            <template v-else>{{ t('noValue') }}</template>
            <div v-if="extractionProposalText(field, t, locale)" class="fa-extraction__muted">{{ extractionProposalText(field, t, locale) }}</div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
