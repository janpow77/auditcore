<script setup lang="ts">
import { computed } from 'vue'
import FaButton from '../base/FaButton.vue'
import { useId } from '../composables/useId'
import { formatNumber } from '../i18n'
import GeoAreaSelect from './GeoAreaSelect.vue'
import { useGeoContext } from './context'
import { TOLERANCE_STEPS, vertexCount } from '@flowaudit/ui-core'

const { state, t, locale } = useGeoContext()
const id = useId('fa-geo-simplify')
const steps = computed(() => TOLERANCE_STEPS[state.simplifyUnit.value])
const toleranceText = computed(() => {
  const value = state.simplifyTolerance.value
  return state.simplifyUnit.value === 'meter'
    ? `${formatNumber(value, locale.value)} m`
    : `${formatNumber(value, locale.value, { maximumFractionDigits: 5 })}°`
})
const result = computed(() => state.simplifyResult.value)
</script>

<template>
  <section class="fa-geo__card" :aria-labelledby="`${id}-h`">
    <h3 :id="`${id}-h`" class="fa-geo__heading">{{ t('simplify') }}</h3>
    <form class="fa-geo__stack" novalidate @submit.prevent="state.simplifyArea">
      <GeoAreaSelect testid="geo-simplify-area" />
      <p v-if="state.area.value" class="fa-geo__muted">{{ t('simplifyVertices', { count: vertexCount(state.area.value.geometry) }) }}</p>
      <fieldset class="fa-geo__fieldset">
        <legend class="fa-geo__label">{{ t('unit') }}</legend>
        <label v-for="unit in ['meter', 'grad'] as const" :key="unit" class="fa-geo__check">
          <input v-model="state.simplifyUnit.value" type="radio" :name="`${id}-unit`" :value="unit" :data-testid="`geo-unit-${unit}`" />
          {{ t(`unit${unit}`) }}
        </label>
      </fieldset>
      <label class="fa-geo__field">
        <span :id="`${id}-tol`" class="fa-geo__label">{{ t('simplifyTolerance', { value: toleranceText }) }}</span>
        <input
          v-model.number="state.simplifyStep.value"
          class="fa-geo__range"
          type="range"
          min="0"
          :max="steps.length - 1"
          step="1"
          :aria-labelledby="`${id}-tol`"
          :aria-valuetext="toleranceText"
          data-testid="geo-simplify-tolerance"
          @change="state.area.value && state.simplifyArea()"
        />
      </label>
      <FaButton variant="primary" type="submit" :loading="state.busy.value === 'simplify'" data-testid="geo-simplify-run">{{ t('simplifyRun') }}</FaButton>
    </form>
    <div v-if="result" class="fa-geo__stack" aria-live="polite" data-testid="geo-simplify-result">
      <p class="fa-geo__summary">{{ t('simplifyResult', { before: result.stuetzpunkte_vorher, after: result.stuetzpunkte_nachher }) }}</p>
      <p v-if="result.entfallene_ringe.length" class="fa-geo__muted">{{ t('simplifyDropped', { count: result.entfallene_ringe.length }) }}</p>
      <p v-if="!result.geometrie" class="fa-geo__notice">{{ t('simplifyGone') }}</p>
    </div>
  </section>
</template>
