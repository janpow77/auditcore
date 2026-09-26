import { computed, ref, shallowRef, watch, type ComputedRef, type Ref, type ShallowRef } from 'vue'
import { createRunner } from '../rest'
import type { GeoArea, GeoCatalogue, GeoPackageResult, GeoPoint, GeoPort, LatLon, LocateResult, RadiusResult } from './types'
import { useGeoAreas, type GeoBusy, type GeoHint, type UseGeoAreas } from './useGeoAreas'
import { useGeoReference, type UseGeoReference } from './useGeoReference'

export type { GeoBusy, GeoHint } from './useGeoAreas'

export interface GeoMapCallbacks {
  radius?: (result: RadiusResult) => void
  located?: (result: LocateResult) => void
  areasLoaded?: (areas: readonly GeoArea[], result: GeoPackageResult) => void
  reference?: (point: LatLon | null) => void
  failed?: (message: string) => void
}

export interface UseGeoMap extends UseGeoAreas, UseGeoReference {
  catalogue: ShallowRef<GeoCatalogue | null>
  points: ComputedRef<readonly GeoPoint[]>
  busy: Ref<GeoBusy | null>
  failure: Ref<string>
  hint: Ref<GeoHint>
  earthModel: Ref<string | null>
  radiusMetres: Ref<number>
  radiusResult: ShallowRef<RadiusResult | null>
  hitIds: ComputedRef<ReadonlySet<string>>
  boundaryInside: Ref<boolean>
  toleranceMetres: Ref<number>
  locateResult: ShallowRef<LocateResult | null>
  load: () => Promise<void>
  searchRadius: () => Promise<void>
  checkLocation: () => Promise<void>
}

interface Prepared {
  point: LatLon
  model: string
}

/** Voraussetzungen einer Berechnung; fehlt etwas, steht der Hinweis in `hint`. */
function prepare(point: LatLon | null, model: string | null, areaMissing: boolean, hint: Ref<GeoHint>): Prepared | null {
  if (!point) hint.value = 'needReference'
  else if (!model) hint.value = 'needModel'
  else hint.value = areaMissing ? 'needArea' : null
  return point && model && !hint.value ? { point, model } : null
}

/** Zustand und Abläufe der Geo-Karte; jede Berechnung läuft über den Port. */
export function useGeoMap(
  port: () => GeoPort | null,
  givenPoints: () => readonly GeoPoint[],
  givenAreas: () => readonly GeoArea[],
  callbacks: GeoMapCallbacks = {},
): UseGeoMap {
  const runner = createRunner<GeoPort, GeoBusy>(port, callbacks.failed)
  const hint = ref<GeoHint>(null)
  const catalogue = shallowRef<GeoCatalogue | null>(null)
  const radiusResult = shallowRef<RadiusResult | null>(null)
  const locateResult = shallowRef<LocateResult | null>(null)
  const areaState = useGeoAreas(runner, givenAreas, hint, callbacks.areasLoaded)
  const referenceState = useGeoReference(runner, port, catalogue, (point) => {
    radiusResult.value = null
    locateResult.value = null
    hint.value = null
    callbacks.reference?.(point)
  })
  const points = computed(() => givenPoints())
  const earthModel = ref<string | null>(null)
  const radiusMetres = ref(5000)
  const hitIds = computed<ReadonlySet<string>>(() => new Set(radiusResult.value?.treffer.map((hit) => hit.id) ?? []))
  const boundaryInside = ref(true)
  const toleranceMetres = ref(0)
  watch(areaState.areaId, () => (locateResult.value = null))

  async function load(): Promise<void> {
    const result = await runner.run('load', (active) => active.catalogue())
    if (!result) return
    catalogue.value = result
    earthModel.value = result.empfohlenes_erdmodell
    boundaryInside.value = result.rand_gilt_als_innen_empfohlen
    referenceState.ellipsoid.value = result.ellipsoide.includes('GRS80') ? 'GRS80' : (result.ellipsoide[0] ?? 'GRS80')
  }

  const ready = (needsArea: boolean): Prepared | null =>
    prepare(referenceState.reference.value, earthModel.value, needsArea && !areaState.area.value, hint)

  async function searchRadius(): Promise<void> {
    const given = ready(false)
    if (!given) return
    const punkte = points.value.map(({ id, lat, lon }) => ({ id, lat, lon }))
    const request = { zentrum: given.point, punkte, radius_m: radiusMetres.value, erdmodell: given.model }
    radiusResult.value = await runner.run('radius', (active) => active.radius(request))
    if (radiusResult.value) callbacks.radius?.(radiusResult.value)
  }

  async function checkLocation(): Promise<void> {
    const given = ready(true)
    const target = areaState.area.value
    if (!given || !target) return
    const request = {
      punkt: given.point, flaeche: target.geometry, erdmodell: given.model,
      rand_gilt_als_innen: boundaryInside.value, rand_toleranz_m: toleranceMetres.value,
    }
    locateResult.value = await runner.run('locate', (active) => active.locate(request))
    if (locateResult.value) callbacks.located?.(locateResult.value)
  }

  return {
    ...areaState, ...referenceState, catalogue, points, busy: runner.busy, failure: runner.failure, hint, earthModel,
    radiusMetres, radiusResult, hitIds, boundaryInside, toleranceMetres, locateResult, load, searchRadius, checkLocation,
  }
}
