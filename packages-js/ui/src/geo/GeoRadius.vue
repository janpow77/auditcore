<script setup lang="ts">
import { computed } from 'vue'
import FaButton from '../base/FaButton.vue'
import { useId } from '../composables/useId'
import { useGeoContext } from './context'
import { displayName, formatDistance } from '@auditcore/ui-core'

const { state, t, locale } = useGeoContext()
const id = useId('fa-geo-radius')
const names = computed(() => new Map(state.points.value.map((point) => [point.id, displayName(point)])))
</script>

<template>
  <section class="fa-geo__card" :aria-labelledby="`${id}-h`">
    <h3 :id="`${id}-h`" class="fa-geo__heading">{{ t('radius') }}</h3>
    <form class="fa-geo__row" novalidate @submit.prevent="state.searchRadius">
      <label class="fa-geo__field">
        <span class="fa-geo__label">{{ t('radiusMetres') }}</span>
        <input v-model.number="state.radiusMetres.value" class="fa-geo__input" type="number" min="0" step="100" data-testid="geo-radius" />
      </label>
      <label v-if="state.catalogue.value" class="fa-geo__field fa-geo__grow">
        <span class="fa-geo__label">{{ t('earthModel') }}</span>
        <select v-model="state.earthModel.value" class="fa-geo__input" data-testid="geo-earth-model">
          <option v-for="model in state.catalogue.value.erdmodelle" :key="model.id" :value="model.id" :title="model.beschreibung">
            {{ model.empfohlen ? t('recommended', { label: model.id }) : model.id }}
          </option>
        </select>
      </label>
      <FaButton variant="primary" type="submit" :loading="state.busy.value === 'radius'" data-testid="geo-radius-run">{{ t('radiusRun') }}</FaButton>
    </form>
    <div v-if="state.radiusResult.value" aria-live="polite" data-testid="geo-radius-result">
      <p class="fa-geo__summary">
        {{ t('radiusSummary', { hits: state.radiusResult.value.treffer.length, checked: state.radiusResult.value.geprueft, radius: formatDistance(state.radiusResult.value.radius_m, locale) }) }}
      </p>
      <table v-if="state.radiusResult.value.treffer.length" class="fa-geo__table">
        <thead>
          <tr><th scope="col">{{ t('colName') }}</th><th scope="col" class="fa-geo__num">{{ t('colDistance') }}</th></tr>
        </thead>
        <tbody>
          <tr v-for="hit in state.radiusResult.value.treffer" :key="hit.id">
            <td>{{ names.get(hit.id) ?? hit.id }}</td>
            <td class="fa-geo__num">{{ formatDistance(hit.abstand_m, locale) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
