/** Gemeinsame Paritätsfälle der Geo-Karte (Vue ↔ React); Antworten des echten auditcore_geo.web. */
import { vi } from 'vitest'
import type { GeoArea, GeoCatalogue, GeoPackageResult, GeoPoint, GeoPort, LocateResult, RadiusResult, SimplifyResult, TileSource, UtmResult } from '../../src'
import catalogue from '../fixtures/geo-catalogue.json'
import gpkg from '../fixtures/geo-gpkg.json'
import locate from '../fixtures/geo-locate-rand.json'
import radius from '../fixtures/geo-radius.json'
import simplify from '../fixtures/geo-simplify.json'
import utm from '../fixtures/geo-utm.json'
import type { ParityCase } from './cases'

export const GEO_POINTS: GeoPoint[] = [
  { id: 'V-1', label: 'Vorhaben Nord', lat: 50.105, lon: 8.67 },
  { id: 'V-2', label: 'Vorhaben Ost', lat: 50.14, lon: 8.68 },
  { id: 'V-3', label: 'Vorhaben Berlin', lat: 52.52, lon: 13.405 },
]
export const GEO_AREA: GeoArea = { id: 'G-1', label: 'Gebiet A', geometry: { type: 'Polygon', coordinates: [[[8.66, 50.1], [8.68, 50.1], [8.68, 50.11], [8.66, 50.11], [8.66, 50.1]]] } }
export const GEO_RESULTS = { catalogue, gpkg, locate, radius, simplify, utm }

export function fakeGeoPort(extra: Partial<GeoPort> = {}): GeoPort & Record<string, ReturnType<typeof vi.fn>> {
  return {
    catalogue: vi.fn(async () => catalogue as unknown as GeoCatalogue),
    radius: vi.fn(async () => radius as unknown as RadiusResult),
    locate: vi.fn(async () => locate as unknown as LocateResult),
    utm: vi.fn(async () => utm as unknown as UtmResult),
    simplify: vi.fn(async () => simplify as unknown as SimplifyResult),
    loadGeoPackage: vi.fn(async () => gpkg as unknown as GeoPackageResult),
    ...extra,
  } as GeoPort & Record<string, ReturnType<typeof vi.fn>>
}

export interface GeoCaseProps {
  port?: GeoPort | null
  points?: readonly GeoPoint[]
  areas?: readonly GeoArea[]
  tiles?: TileSource | null
  locale?: 'de' | 'en'
}

export const geoCases: ReadonlyArray<ParityCase<GeoCaseProps>> = [
  {
    name: 'Punkte und Fläche ohne Kachelquelle',
    props: () => ({ port: fakeGeoPort(), points: GEO_POINTS, areas: [GEO_AREA] }),
    expect: { texts: ['Keine Kachelquelle'], roles: [['application', /3 Punkten und 1 Flächen/]], counts: { '[data-testid="geo-gpkg-file"]': 1 } },
  },
  {
    name: 'mit Kachelquelle',
    props: () => ({ port: fakeGeoPort(), tiles: { url: '/kacheln/{z}/{x}/{y}.png', attribution: 'Synthetische Kacheln' } }),
    expect: { texts: ['Kartendaten: Synthetische Kacheln'] },
  },
  { name: 'ohne Port', props: () => ({}), expect: { texts: ['Kein Port übergeben'] } },
  { name: 'englisch', props: () => ({ port: fakeGeoPort(), points: GEO_POINTS, locale: 'en' }), expect: { texts: ['Radius search'] } },
]
