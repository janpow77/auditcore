import { computed, ref, shallowRef, type ComputedRef, type Ref, type ShallowRef } from 'vue'
import type { Runner } from '../rest'
import { parseLatLon, type CoordinateError } from './model'
import type { GeoCatalogue, GeocodeResult, GeoPort, LatLon, UtmResult } from './types'
import type { GeoBusy } from './useGeoAreas'

export interface UseGeoReference {
  ellipsoid: Ref<string>
  reference: Ref<LatLon | null>
  latText: Ref<string>
  lonText: Ref<string>
  coordinateError: Ref<CoordinateError>
  utm: ShallowRef<UtmResult | null>
  geocodeResult: ShallowRef<GeocodeResult | null>
  canGeocode: ComputedRef<boolean>
  setReference: (point: LatLon | null) => Promise<void>
  applyTexts: () => Promise<void>
  refreshUtm: () => Promise<void>
  geocode: (query: string) => Promise<void>
}

function rounded(value: number): string {
  return String(Math.round(value * 1e6) / 1e6)
}

/** Bezugspunkt mit Texteingabe, UTM-Anzeige und (nur freigegeben) Adresssuche. */
export function useGeoReference(
  runner: Runner<GeoPort, GeoBusy>,
  port: () => GeoPort | null,
  catalogue: ShallowRef<GeoCatalogue | null>,
  changed: (point: LatLon | null) => void,
): UseGeoReference {
  const ellipsoid = ref('GRS80')
  const reference = ref<LatLon | null>(null)
  const latText = ref('')
  const lonText = ref('')
  const coordinateError = ref<CoordinateError>(null)
  const utm = shallowRef<UtmResult | null>(null)
  const geocodeResult = shallowRef<GeocodeResult | null>(null)
  const canGeocode = computed(() => Boolean(port()?.geocode) && catalogue.value?.geocoder.aktiv === true)

  async function refreshUtm(): Promise<void> {
    const point = reference.value
    if (!point) return
    const result = await runner.run('utm', (active) => active.utm({ punkt: point, ellipsoid: ellipsoid.value }))
    if (result) utm.value = result
  }

  async function setReference(point: LatLon | null): Promise<void> {
    reference.value = point
    coordinateError.value = null
    latText.value = point ? rounded(point.lat) : ''
    lonText.value = point ? rounded(point.lon) : ''
    utm.value = null
    changed(point)
    await refreshUtm()
  }

  async function applyTexts(): Promise<void> {
    const parsed = parseLatLon(latText.value, lonText.value)
    coordinateError.value = parsed.error
    if (parsed.point) await setReference(parsed.point)
  }

  async function geocode(query: string): Promise<void> {
    const text = query.trim()
    if (!canGeocode.value || !text) return
    const result = await runner.run('geocode', (active) => active.geocode?.(text) ?? Promise.reject(new Error('Adresssuche nicht angeboten.')))
    if (result) geocodeResult.value = result
  }

  return { ellipsoid, reference, latText, lonText, coordinateError, utm, geocodeResult, canGeocode, setReference, applyTexts, refreshUtm, geocode }
}
