/**
 * Kartenansicht auf Leaflet (BSD-2-Clause). Leaflet wird erst beim Anlegen
 * einer Karte geladen (dynamischer Import), damit Anwendungen ohne Karte es
 * nicht laden. Farben kommen über CSS-Klassen aus den `--fa-*`-Token.
 */
import type { AreaGeometry, GeoArea, GeoPoint, LatLon, TileSource } from './types'

export interface MapLayers {
  points: readonly GeoPoint[]
  areas: readonly GeoArea[]
  reference: LatLon | null
  radiusMetres: number | null
  hits: ReadonlySet<string>
  selectedArea: string | null
  simplified: AreaGeometry | null
}

export interface MapViewOptions {
  center: LatLon
  zoom: number
  tiles: TileSource | null
  /** Klick auf die Karte: neuer Bezugspunkt. */
  onPick: (point: LatLon) => void
  /** Beschriftung eines Punktes bzw. einer Fläche für Tooltips. */
  label: (entry: GeoPoint | GeoArea) => string
}

export interface MapView {
  update(layers: MapLayers): void
  setTiles(tiles: TileSource | null): void
  /** Ausschnitt auf alle Punkte, Flächen und den Umkreis setzen. */
  fit(): void
  destroy(): void
}

type Leaflet = typeof import('leaflet')

/** Leaflet setzt Tooltips und Namensnennung als HTML; Daten gehen deshalb nur als Text hinein. */
export function escapeHtml(text: string): string {
  return text.replace(/[&<>"']/g, (char) => `&#${char.charCodeAt(0)};`)
}

function textElement(text: string): HTMLElement {
  const span = document.createElement('span')
  span.textContent = text
  return span
}

function tileLayer(L: Leaflet, tiles: TileSource | null): import('leaflet').TileLayer | null {
  if (!tiles?.url) return null
  return L.tileLayer(tiles.url, {
    attribution: escapeHtml(tiles.attribution),
    maxZoom: tiles.maxZoom ?? 19,
    subdomains: tiles.subdomains ?? 'abc',
  })
}

function drawAreas(L: Leaflet, group: import('leaflet').LayerGroup, layers: MapLayers, options: MapViewOptions): void {
  for (const area of layers.areas) {
    const selected = area.id === layers.selectedArea
    L.geoJSON(area.geometry, { style: () => ({ className: `fa-geo__area${selected ? ' fa-geo__area--selected' : ''}` }) })
      .bindTooltip(textElement(options.label(area)))
      .addTo(group)
  }
  if (layers.simplified) {
    L.geoJSON(layers.simplified, { style: () => ({ className: 'fa-geo__simplified' }), interactive: false }).addTo(group)
  }
}

function drawPoints(L: Leaflet, group: import('leaflet').LayerGroup, layers: MapLayers, options: MapViewOptions): void {
  for (const point of layers.points) {
    const hit = layers.hits.has(point.id)
    L.circleMarker([point.lat, point.lon], { radius: hit ? 7 : 5, className: `fa-geo__point${hit ? ' fa-geo__point--hit' : ''}` })
      .bindTooltip(textElement(options.label(point)))
      .addTo(group)
  }
  const reference = layers.reference
  if (!reference) return
  if (layers.radiusMetres) {
    L.circle([reference.lat, reference.lon], { radius: layers.radiusMetres, className: 'fa-geo__radius', interactive: false }).addTo(group)
  }
  L.circleMarker([reference.lat, reference.lon], { radius: 8, className: 'fa-geo__reference', interactive: false }).addTo(group)
}

/** Legt die Leaflet-Karte im Element an. */
export async function createLeafletView(element: HTMLElement, options: MapViewOptions): Promise<MapView> {
  const L = await import('leaflet')
  const map = L.map(element, { center: [options.center.lat, options.center.lon], zoom: options.zoom, keyboard: true, zoomControl: true })
  map.attributionControl.setPrefix('<a href="https://leafletjs.com">Leaflet</a>')
  let tiles = tileLayer(L, options.tiles)
  tiles?.addTo(map)
  const group = L.featureGroup().addTo(map)
  map.on('click', (event: import('leaflet').LeafletMouseEvent) => options.onPick({ lat: event.latlng.lat, lon: L.Util.wrapNum(event.latlng.lng, [-180, 180], true) }))
  return {
    update(layers) {
      group.clearLayers()
      drawAreas(L, group, layers, options)
      drawPoints(L, group, layers, options)
    },
    setTiles(next) {
      tiles?.remove()
      tiles = tileLayer(L, next)
      tiles?.addTo(map)
    },
    fit() {
      const bounds = group.getBounds()
      if (bounds.isValid()) map.fitBounds(bounds, { padding: [24, 24], maxZoom: 15 })
    },
    destroy() {
      map.remove()
    },
  }
}
