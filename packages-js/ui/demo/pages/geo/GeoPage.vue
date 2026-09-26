<script setup lang="ts">
import { ref } from 'vue'
import { createGeoRestPort, FaGeoMap, type LatLon, type RadiusResult, type TileSource } from '@flowaudit/ui'
import { demoAreas, demoPoints } from './demoData'

const port = createGeoRestPort({ baseUrl: '/api/geo' })
const points = demoPoints()
const areas = demoAreas()
// Synthetische Kacheln des Demo-Backends (geo_demo.py); kein fremder Kachelserver.
const tiles: TileSource = { url: '/api/geo-demo/kacheln/{z}/{x}/{y}.png', attribution: 'Synthetische Demokacheln (keine Kartendaten)', maxZoom: 18 }
const last = ref('')

function onRadius(result: RadiusResult): void {
  last.value = `Ereignis radius-completed: ${result.treffer.length} Treffer`
}

function onReference(point: LatLon | null): void {
  last.value = point ? `Ereignis reference-change: ${point.lat.toFixed(5)}, ${point.lon.toFixed(5)}` : ''
}
</script>

<template>
  <h1>Geo-Karte</h1>
  <p>
    <code>&lt;FaGeoMap&gt;</code> bzw. <code>&lt;flowaudit-geo-map&gt;</code> mit dem REST-Port auf
    <code>auditcore_geo.web</code>: Umkreissuche mit Erdmodell, Punkt in Fläche mit Randregel, UTM,
    Douglas-Peucker und GeoPackage. Alle Standorte und Flächen sind erfunden; die Kacheln kommen aus dem
    Demo-Backend. Beispieldatei zum Hochladen:
    <a href="/api/geo-demo/schutzgebiete-demo.gpkg" download>schutzgebiete-demo.gpkg</a>.
  </p>
  <FaGeoMap :port="port" :points="points" :areas="areas" :tiles="tiles" @radius-completed="onRadius" @reference-change="onReference" />
  <p class="demo-event" aria-live="polite">{{ last }}</p>
</template>
