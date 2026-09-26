<script setup lang="ts">
import { computed } from 'vue'
import FaBadge from '../base/FaBadge.vue'
import FaButton from '../base/FaButton.vue'
import { useId } from '../composables/useId'
import GeoAreaSelect from './GeoAreaSelect.vue'
import { useGeoContext } from './context'
import { formatDistance } from '@flowaudit/ui-core'
import type { BadgeTone } from '../base/types'

const { state, t, locale } = useGeoContext()
const id = useId('fa-geo-locate')
const TONES: Readonly<Record<string, BadgeTone>> = { innen: 'success', aussen: 'neutral', rand: 'warning' }
const result = computed(() => state.locateResult.value)
const boundaryCase = computed(() => result.value?.lage_mit_toleranz === 'rand')
const boundaryText = computed(() => {
  const found = result.value
  if (!found) return ''
  const how = found.lage === 'rand'
    ? t('boundaryExact')
    : t('boundaryTolerance', { tolerance: formatDistance(found.rand_toleranz_m, locale.value) })
  return t('boundaryCase', { how, rule: t(found.rand_gilt_als_innen ? 'ruleInside' : 'ruleOutside') })
})
</script>

<template>
  <section class="fa-geo__card" :aria-labelledby="`${id}-h`">
    <h3 :id="`${id}-h`" class="fa-geo__heading">{{ t('locate') }}</h3>
    <form class="fa-geo__stack" novalidate @submit.prevent="state.checkLocation">
      <GeoAreaSelect testid="geo-locate-area" />
      <label class="fa-geo__check">
        <input v-model="state.boundaryInside.value" type="checkbox" data-testid="geo-boundary-inside" />
        {{ t('boundaryInside') }}
      </label>
      <p class="fa-geo__muted">{{ t('boundaryHelp') }}</p>
      <div class="fa-geo__row">
        <label class="fa-geo__field">
          <span class="fa-geo__label">{{ t('tolerance') }}</span>
          <input v-model.number="state.toleranceMetres.value" class="fa-geo__input" type="number" min="0" step="1" data-testid="geo-tolerance" />
        </label>
        <FaButton variant="primary" type="submit" :loading="state.busy.value === 'locate'" data-testid="geo-locate-run">{{ t('locateRun') }}</FaButton>
      </div>
    </form>
    <div v-if="result" class="fa-geo__stack" aria-live="polite" data-testid="geo-locate-result">
      <p class="fa-geo__summary">
        <FaBadge :tone="TONES[result.lage_mit_toleranz]" data-testid="geo-position">{{ t(`position${result.lage_mit_toleranz}`) }}</FaBadge>
        <strong>{{ t(result.enthaelt ? 'contains' : 'notContains') }}</strong>
      </p>
      <p v-if="boundaryCase" class="fa-geo__notice" data-testid="geo-boundary-case">{{ boundaryText }}</p>
      <p v-if="result.lage === 'aussen'" class="fa-geo__muted">{{ t('distance', { distance: formatDistance(result.abstand_m, locale) }) }}</p>
      <details v-if="result.hinweise.length" class="fa-geo__details">
        <summary>{{ t('notes') }}</summary>
        <ul class="fa-geo__list">
          <li v-for="note in result.hinweise" :key="note">{{ note }}</li>
        </ul>
      </details>
    </div>
  </section>
</template>
