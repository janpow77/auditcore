import type { ElementDefinition } from '../elements/define'
import FaGeoMap from './FaGeoMap.vue'

/**
 * `<flowaudit-geo-map>`: Eigenschaften `port` (GeoPort), `points`, `areas`,
 * `tiles` (TileSource), `center`, `zoom`, `locale`; Ereignisse
 * `radius-completed`, `location-checked`, `areas-loaded`, `reference-change`,
 * `error`.
 */
export const geoMapElement: ElementDefinition = { tag: 'flowaudit-geo-map', component: FaGeoMap }
