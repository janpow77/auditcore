<script setup lang="ts">
import { computed, provide, watch } from 'vue'
import { useI18n, type Locale } from '../i18n'
import { GEO_CONTEXT } from './context'
import GeoLocate from './GeoLocate.vue'
import GeoMapCanvas from './GeoMapCanvas.vue'
import GeoPackageLoader from './GeoPackageLoader.vue'
import GeoRadius from './GeoRadius.vue'
import GeoReference from './GeoReference.vue'
import GeoSimplify from './GeoSimplify.vue'
import type { MapLayers } from '@flowaudit/ui-core'
import { geoMessages } from '@flowaudit/ui-core'
import type { GeoArea, GeoPackageResult, GeoPoint, GeoPort, LatLon, LocateResult, RadiusResult, TileSource } from '@flowaudit/ui-core'
import { useGeoMap } from './useGeoMap'

const props = withDefaults(defineProps<{
  /** Fachlogik, z. B. `createGeoRestPort({ baseUrl: '/api/geo' })`. */
  port?: GeoPort | null
  /** Punkte (Dezimalgrad, WGS 84/ETRS89). */
  points?: readonly GeoPoint[]
  /** Flächen als GeoJSON-Polygon/-MultiPolygon. */
  areas?: readonly GeoArea[]
  /** Kachelquelle der Anwendung; ohne Angabe kein Hintergrund und kein fremder Server. */
  tiles?: TileSource | null
  /** Anfangsausschnitt; ohne Punkte und Flächen gilt er dauerhaft. */
  center?: LatLon
  zoom?: number
  locale?: Locale
}>(), {
  port: null,
  points: () => [],
  areas: () => [],
  tiles: null,
  center: () => ({ lat: 51.163, lon: 10.448 }),
  zoom: 6,
  locale: undefined,
})

const emit = defineEmits<{
  'radius-completed': [result: RadiusResult]
  'location-checked': [result: LocateResult]
  'areas-loaded': [areas: readonly GeoArea[], result: GeoPackageResult]
  'reference-change': [point: LatLon | null]
  error: [message: string]
}>()

const { t, locale: active } = useI18n(geoMessages, () => props.locale)
const state = useGeoMap(() => props.port, () => props.points, () => props.areas, {
  radius: (result) => emit('radius-completed', result),
  located: (result) => emit('location-checked', result),
  areasLoaded: (areas, result) => emit('areas-loaded', areas, result),
  reference: (point) => emit('reference-change', point),
  failed: (message) => emit('error', message),
})
provide(GEO_CONTEXT, { state, t, locale: active })

const layers = computed<MapLayers>(() => state.selection.value.layers)
const upload = computed(() => Boolean(props.port?.loadGeoPackage))
const sources = computed(() => Boolean(props.port?.loadSource))
const hint = computed(() => state.hint.value)

watch(() => props.port, () => void state.load(), { immediate: true })
</script>

<template>
  <div class="fa-geo" :lang="active">
    <p v-if="!port" class="fa-geo__notice" role="status">{{ t('noPort') }}</p>
    <p v-if="state.busy.value === 'load'" class="fa-geo__muted" role="status">{{ t('loading') }}</p>
    <p v-if="state.failure.value" class="fa-geo__failure" role="alert">{{ t('failed', { message: state.failure.value }) }}</p>
    <p v-if="hint" class="fa-geo__error" role="alert" data-testid="geo-hint">{{ t(hint) }}</p>
    <div class="fa-geo__layout">
      <GeoMapCanvas :layers="layers" :tiles="tiles" :center="center" :zoom="zoom" @pick="state.setReference" />
      <div class="fa-geo__panel">
        <GeoReference />
        <template v-if="state.catalogue.value">
          <GeoRadius />
          <GeoLocate />
          <GeoSimplify />
          <GeoPackageLoader v-if="upload || sources" :upload="upload" :sources="sources" />
        </template>
      </div>
    </div>
  </div>
</template>
