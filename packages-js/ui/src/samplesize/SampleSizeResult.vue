<!-- Ergebnis des Planers: Umfang, Aufteilung, Herleitung mit Fundstellen, Hinweise. -->
<script setup lang="ts">
import { computed } from 'vue'
import { samplesizeAllocation, samplesizeDerivation, samplesizeMessages, samplesizeSummary, type SampleSizePlan } from '@auditcore/ui-core'
import { useI18n, type Locale } from '../i18n'

const props = withDefaults(defineProps<{
  plan: SampleSizePlan
  locale?: Locale
}>(), { locale: undefined })
const { t, locale: active } = useI18n(samplesizeMessages, () => props.locale)
const summary = computed(() => samplesizeSummary(props.plan, t, active.value))
const allocation = computed(() => samplesizeAllocation(props.plan, t, active.value))
const derivation = computed(() => samplesizeDerivation(props.plan, active.value))
const allocationHead = computed(() => [t('stratumName'), t('allocationSize'), t('allocationShare'), t('allocationCutOff'), t('stratumExhaustive')])
const derivationHead = computed(() => [t('stepLabel'), t('stepFormula'), t('stepValue'), t('stepSource')])
</script>

<template>
  <section class="fa-samplesize__result" :aria-label="t('result')" data-testid="samplesize-result">
    <h3 class="fa-samplesize__heading">{{ t('result') }} <span class="fa-samplesize__badge">{{ plan.status_label }}</span></h3>
    <dl class="fa-samplesize__summary">
      <div v-for="row in summary" :key="row.key">
        <dt>{{ row.key }}</dt>
        <dd>{{ row.text }}</dd>
      </div>
    </dl>
    <table v-if="allocation.length" class="fa-samplesize__table" data-testid="samplesize-allocation">
      <caption>{{ t('allocation') }}</caption>
      <thead><tr><th v-for="head in allocationHead" :key="head" scope="col">{{ head }}</th></tr></thead>
      <tbody><tr v-for="(row, index) in allocation" :key="index"><td v-for="(cell, column) in row" :key="column">{{ cell }}</td></tr></tbody>
    </table>
    <table class="fa-samplesize__table" data-testid="samplesize-derivation">
      <caption>{{ t('derivation') }}</caption>
      <thead><tr><th v-for="head in derivationHead" :key="head" scope="col">{{ head }}</th></tr></thead>
      <tbody><tr v-for="(row, index) in derivation" :key="index"><td v-for="(cell, column) in row" :key="column">{{ cell }}</td></tr></tbody>
    </table>
    <ul v-if="plan.warnings.length" class="fa-samplesize__warnings" :aria-label="t('warnings')">
      <li v-for="warning in plan.warnings" :key="warning">{{ warning }}</li>
    </ul>
  </section>
</template>
