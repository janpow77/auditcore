<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import FaButton from '../base/FaButton.vue'
import { useGeoContext } from './context'
import { createLeafletView, type MapLayers, type MapView } from './mapView'
import { displayName } from './model'
import type { LatLon, TileSource } from './types'

const props = defineProps<{ layers: MapLayers; tiles: TileSource | null; center: LatLon; zoom: number }>()
const emit = defineEmits<{ pick: [point: LatLon] }>()
const { t } = useGeoContext()
const container = ref<HTMLElement | null>(null)
let view: MapView | null = null
let unmounted = false

function fit(): void {
  view?.fit()
}

onMounted(async () => {
  if (!container.value) return
  const created = await createLeafletView(container.value, {
    center: props.center,
    zoom: props.zoom,
    tiles: props.tiles,
    onPick: (point) => emit('pick', point),
    label: displayName,
  })
  if (unmounted) {
    created.destroy()
    return
  }
  view = created
  view.update(props.layers)
  if (props.layers.points.length + props.layers.areas.length > 0) fit()
})

watch(() => props.layers, (layers) => view?.update(layers))
watch(() => props.layers.points.length + props.layers.areas.length, fit)
watch(() => props.tiles, (tiles) => view?.setTiles(tiles))

onBeforeUnmount(() => {
  unmounted = true
  view?.destroy()
  view = null
})
</script>

<template>
  <div class="fa-geo__canvas-wrap">
    <div
      ref="container"
      class="fa-geo__canvas"
      role="application"
      :aria-label="t('mapLabel', { points: layers.points.length, areas: layers.areas.length })"
      data-testid="geo-map"
    />
    <div class="fa-geo__map-bar">
      <p v-if="tiles?.url" class="fa-geo__muted" data-testid="geo-attribution">{{ t('attribution', { text: tiles.attribution }) }}</p>
      <p v-else class="fa-geo__muted" data-testid="geo-no-tiles">{{ t('noTiles') }}</p>
      <FaButton size="sm" icon="expand" data-testid="geo-fit" @click="fit">{{ t('fit') }}</FaButton>
    </div>
  </div>
</template>
