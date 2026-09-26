<script setup lang="ts">
import { computed, ref } from 'vue'
import FaButton from '../base/FaButton.vue'
import { useId } from '../composables/useId'
import { useGeoContext } from './context'
import GeoUtmInput from './GeoUtmInput.vue'
import { displayName, formatDegrees, formatMetres } from '@auditcore/ui-core'

const { state, t, locale } = useGeoContext()
const id = useId('fa-geo-ref')
const pointId = ref('')
const address = ref('')
const utmText = computed(() => {
  const utm = state.utm.value
  if (!utm) return ''
  return t('utmValue', {
    zone: utm.zone,
    hemisphere: utm.nordhalbkugel ? 'N' : 'S',
    east: formatMetres(utm.ost, locale.value),
    north: formatMetres(utm.nord, locale.value),
  })
})

function takePoint(): void {
  const point = state.points.value.find((entry) => entry.id === pointId.value)
  if (point) void state.setReference({ lat: point.lat, lon: point.lon })
}
</script>

<template>
  <section class="fa-geo__card" :aria-labelledby="`${id}-h`">
    <h3 :id="`${id}-h`" class="fa-geo__heading">{{ t('reference') }}</h3>
    <p class="fa-geo__muted">{{ t('referenceHelp') }}</p>
    <form class="fa-geo__row" novalidate @submit.prevent="state.applyTexts">
      <label class="fa-geo__field">
        <span class="fa-geo__label">{{ t('lat') }}</span>
        <input v-model="state.latText.value" class="fa-geo__input" inputmode="decimal" :aria-invalid="state.coordinateError.value === 'lat'" data-testid="geo-lat" />
      </label>
      <label class="fa-geo__field">
        <span class="fa-geo__label">{{ t('lon') }}</span>
        <input v-model="state.lonText.value" class="fa-geo__input" inputmode="decimal" :aria-invalid="state.coordinateError.value === 'lon'" data-testid="geo-lon" />
      </label>
      <FaButton type="submit" data-testid="geo-apply">{{ t('apply') }}</FaButton>
    </form>
    <p v-if="state.coordinateError.value" class="fa-geo__error" role="alert">{{ t(state.coordinateError.value === 'lat' ? 'errorlat' : 'errorlon') }}</p>
    <GeoUtmInput />
    <div v-if="state.points.value.length" class="fa-geo__row">
      <label class="fa-geo__field fa-geo__grow">
        <span class="fa-geo__label">{{ t('fromPoint') }}</span>
        <select v-model="pointId" class="fa-geo__input" data-testid="geo-point-select">
          <option value="">{{ t('choose') }}</option>
          <option v-for="point in state.points.value" :key="point.id" :value="point.id">{{ displayName(point) }}</option>
        </select>
      </label>
      <FaButton :disabled="!pointId" data-testid="geo-point-take" @click="takePoint">{{ t('apply') }}</FaButton>
    </div>
    <form v-if="state.canGeocode.value" class="fa-geo__row" novalidate @submit.prevent="state.geocode(address)">
      <label class="fa-geo__field fa-geo__grow">
        <span class="fa-geo__label">{{ t('geocode') }}</span>
        <input v-model="address" class="fa-geo__input" type="search" autocomplete="off" data-testid="geo-address" />
      </label>
      <FaButton type="submit" :loading="state.busy.value === 'geocode'">{{ t('geocodeRun') }}</FaButton>
    </form>
    <p v-if="state.canGeocode.value" class="fa-geo__muted">{{ t('geocodeHelp') }}</p>
    <ul v-if="state.geocodeResult.value" class="fa-geo__list" aria-live="polite">
      <li v-if="!state.geocodeResult.value.treffer.length">{{ t('geocodeNone') }}</li>
      <li v-for="hit in state.geocodeResult.value.treffer" :key="hit.rang">
        <button type="button" class="fa-geo__link" @click="state.setReference({ lat: hit.lat, lon: hit.lon })">{{ hit.anzeigename ?? `${hit.lat}, ${hit.lon}` }}</button>
      </li>
      <li class="fa-geo__muted">{{ state.geocodeResult.value.namensnennung }}</li>
    </ul>
    <dl v-if="state.reference.value" class="fa-geo__facts" aria-live="polite" data-testid="geo-reference">
      <dt>{{ t('reference') }}</dt>
      <dd>{{ formatDegrees(state.reference.value.lat, locale) }}, {{ formatDegrees(state.reference.value.lon, locale) }}</dd>
      <dt>{{ t('utm') }}</dt>
      <dd data-testid="geo-utm">
        {{ utmText }}
        <span v-if="state.utm.value?.epsg" class="fa-geo__muted">({{ t('utmEpsg', { epsg: state.utm.value.epsg }) }})</span>
      </dd>
    </dl>
    <label v-if="state.catalogue.value && (state.reference.value || state.canFromUtm.value)" class="fa-geo__field">
      <span class="fa-geo__label">{{ t('ellipsoid') }}</span>
      <select v-model="state.ellipsoid.value" class="fa-geo__input" data-testid="geo-ellipsoid" @change="state.refreshUtm">
        <option v-for="entry in state.catalogue.value.ellipsoide" :key="entry" :value="entry">{{ entry }}</option>
      </select>
    </label>
    <p v-if="state.utm.value" class="fa-geo__muted">{{ t('utmNote') }}</p>
  </section>
</template>
