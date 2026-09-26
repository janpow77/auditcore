import type { GeoArea, GeoPoint, GeoPort, LatLon, Locale, TileSource } from '@flowaudit/ui'
import { createElementComponent } from './createElementComponent'

export interface FlowauditGeoMapProps {
  /** Fachlogik, z. B. `createGeoRestPort({ baseUrl: '/api/geo' })` (docs/ui/geo-rest.md). */
  port: GeoPort | null
  points?: readonly GeoPoint[]
  areas?: readonly GeoArea[]
  /** Kachelquelle der Anwendung; ohne Angabe kein Hintergrund. */
  tiles?: TileSource | null
  center?: LatLon
  zoom?: number
  locale?: Locale
}

/** `<flowaudit-geo-map>` als React-Komponente: Karte, Umkreis, Punkt in Fläche, UTM, Vereinfachung, GeoPackage. */
export const FlowauditGeoMap = createElementComponent<
  FlowauditGeoMapProps,
  { onRadiusCompleted: string; onLocationChecked: string; onAreasLoaded: string; onReferenceChange: string; onError: string }
>('flowaudit-geo-map', {
  properties: ['port', 'points', 'areas', 'tiles', 'center', 'zoom', 'locale'],
  events: {
    onRadiusCompleted: 'radius-completed',
    onLocationChecked: 'location-checked',
    onAreasLoaded: 'areas-loaded',
    onReferenceChange: 'reference-change',
    onError: 'error',
  },
})
