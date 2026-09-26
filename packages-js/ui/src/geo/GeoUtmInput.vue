<script setup lang="ts">
import FaButton from '../base/FaButton.vue'
import { useId } from '../composables/useId'
import { utmErrorKey } from '@flowaudit/ui-core'
import { useGeoContext } from './context'

const { state, t } = useGeoContext()
const id = useId('fa-geo-utm')
const selected = (event: Event): string => (event.target as HTMLSelectElement).value
</script>

<template>
  <details v-if="state.canFromUtm.value" class="fa-geo__utm" data-testid="geo-utm-input">
    <summary>{{ t('utmInput') }}</summary>
    <p :id="`${id}-help`" class="fa-geo__muted">{{ t('utmInputHelp') }}</p>
    <form class="fa-geo__row" novalidate :aria-describedby="`${id}-help`" @submit.prevent="state.applyUtm">
      <label class="fa-geo__field">
        <span class="fa-geo__label">{{ t('utmZone') }}</span>
        <input v-model="state.zoneText.value" class="fa-geo__input fa-geo__input--short" inputmode="numeric" :aria-invalid="state.utmError.value === 'zone'" data-testid="geo-utm-zone" />
      </label>
      <label class="fa-geo__field">
        <span class="fa-geo__label">{{ t('utmHemisphere') }}</span>
        <select :value="state.northern.value ? 'N' : 'S'" class="fa-geo__input" data-testid="geo-utm-hemisphere" @change="state.northern.value = selected($event) === 'N'">
          <option value="N">{{ t('hemisphereNorth') }}</option>
          <option value="S">{{ t('hemisphereSouth') }}</option>
        </select>
      </label>
      <label class="fa-geo__field">
        <span class="fa-geo__label">{{ t('utmEast') }}</span>
        <input v-model="state.eastText.value" class="fa-geo__input" inputmode="decimal" :aria-invalid="state.utmError.value === 'east'" data-testid="geo-utm-east" />
      </label>
      <label class="fa-geo__field">
        <span class="fa-geo__label">{{ t('utmNorth') }}</span>
        <input v-model="state.northText.value" class="fa-geo__input" inputmode="decimal" :aria-invalid="state.utmError.value === 'north'" data-testid="geo-utm-north" />
      </label>
      <FaButton type="submit" :loading="state.busy.value === 'utm'" data-testid="geo-utm-apply">{{ t('apply') }}</FaButton>
    </form>
    <p v-if="state.utmError.value" class="fa-geo__error" role="alert">{{ t(utmErrorKey(state.utmError.value)) }}</p>
  </details>
</template>
