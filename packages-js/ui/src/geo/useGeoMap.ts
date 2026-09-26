// Vue-Anbindung des Geo-Zustandsautomaten aus @auditcore/ui-core. Die Felder
// sind (schreibbare) berechnete Referenzen auf den Controller-Zustand, damit
// die Teilkomponenten sie wie bisher mit v-model binden.

import { computed, type ComputedRef, type Ref, type WritableComputedRef } from 'vue'
import {
  createGeoController,
  selectGeo,
  type GeoArea,
  type GeoBusy,
  type GeoCatalogue,
  type GeoController,
  type GeoData,
  type GeoField,
  type GeoHint,
  type GeocodeResult,
  type GeoMapCallbacks,
  type GeoPackageResult,
  type GeoPoint,
  type GeoPort,
  type GeoSelection,
  type LatLon,
  type LocateResult,
  type RadiusResult,
  type SimplifyResult,
  type SimplifyUnit,
  type UtmResult,
  type CoordinateError,
  type UtmInputError,
} from '@auditcore/ui-core'
import { useStore } from '../composables/useStore'

export type { GeoBusy, GeoHint, GeoMapCallbacks } from '@auditcore/ui-core'

export interface UseGeoMap {
  controller: GeoController
  selection: ComputedRef<GeoSelection>
  catalogue: ComputedRef<GeoCatalogue | null>
  points: ComputedRef<readonly GeoPoint[]>
  areas: ComputedRef<readonly GeoArea[]>
  area: ComputedRef<GeoArea | null>
  areaId: WritableComputedRef<string | null>
  busy: ComputedRef<GeoBusy | null>
  failure: ComputedRef<string>
  hint: ComputedRef<GeoHint>
  earthModel: WritableComputedRef<string | null>
  radiusMetres: WritableComputedRef<number>
  radiusResult: ComputedRef<RadiusResult | null>
  hitIds: ComputedRef<ReadonlySet<string>>
  boundaryInside: WritableComputedRef<boolean>
  toleranceMetres: WritableComputedRef<number>
  locateResult: ComputedRef<LocateResult | null>
  simplifyUnit: WritableComputedRef<SimplifyUnit>
  simplifyStep: WritableComputedRef<number>
  simplifyTolerance: ComputedRef<number>
  simplifyResult: ComputedRef<SimplifyResult | null>
  gpkgResult: ComputedRef<GeoPackageResult | null>
  ellipsoid: WritableComputedRef<string>
  reference: ComputedRef<LatLon | null>
  latText: WritableComputedRef<string>
  lonText: WritableComputedRef<string>
  coordinateError: ComputedRef<CoordinateError>
  utm: ComputedRef<UtmResult | null>
  zoneText: WritableComputedRef<string>
  eastText: WritableComputedRef<string>
  northText: WritableComputedRef<string>
  northern: WritableComputedRef<boolean>
  utmError: ComputedRef<UtmInputError>
  canFromUtm: ComputedRef<boolean>
  geocodeResult: ComputedRef<GeocodeResult | null>
  canGeocode: ComputedRef<boolean>
  load: () => Promise<void>
  searchRadius: () => Promise<void>
  checkLocation: () => Promise<void>
  setReference: (point: LatLon | null) => Promise<void>
  applyTexts: () => Promise<void>
  refreshUtm: () => Promise<void>
  applyUtm: () => Promise<void>
  geocode: (query: string) => Promise<void>
  simplifyArea: () => Promise<void>
  loadFile: (file: Blob) => Promise<void>
  loadSource: (name: string) => Promise<void>
}

type Readers = { [K in keyof GeoData]: ComputedRef<GeoData[K]> }

function readers(state: Readonly<Ref<GeoData>>): Readers {
  const keys = Object.keys(state.value) as (keyof GeoData)[]
  return Object.fromEntries(keys.map((key) => [key, computed(() => state.value[key])])) as unknown as Readers
}

function field<K extends GeoField>(controller: GeoController, state: Readonly<Ref<GeoData>>, key: K): WritableComputedRef<GeoData[K]> {
  return computed({ get: () => state.value[key], set: (value) => controller.setField(key, value) })
}

/** Zustand und Abläufe der Geo-Karte; jede Berechnung läuft über den Port. */
export function useGeoMap(
  port: () => GeoPort | null,
  givenPoints: () => readonly GeoPoint[],
  givenAreas: () => readonly GeoArea[],
  callbacks: GeoMapCallbacks = {},
): UseGeoMap {
  const controller = createGeoController({ ...callbacks, inputs: () => ({ port: port(), points: givenPoints(), areas: givenAreas() }) })
  const state = useStore(controller.store)
  const selection = computed(() => selectGeo(state.value, { port: port(), points: givenPoints(), areas: givenAreas() }))
  const read = readers(state)
  const fields = (['radiusMetres', 'earthModel', 'boundaryInside', 'toleranceMetres', 'simplifyStep', 'ellipsoid', 'latText', 'lonText', 'zoneText', 'eastText', 'northText', 'northern'] as const)
    .map((key) => [key, field(controller, state, key)])
  return {
    ...read,
    ...(Object.fromEntries(fields) as Pick<UseGeoMap, GeoField>),
    controller,
    selection,
    points: computed(() => givenPoints()),
    areas: computed(() => selection.value.areas),
    area: computed(() => selection.value.area),
    areaId: computed({ get: () => state.value.areaId, set: controller.selectArea }),
    simplifyUnit: computed({ get: () => state.value.simplifyUnit, set: controller.setSimplifyUnit }),
    simplifyTolerance: computed(() => selection.value.simplifyTolerance),
    hitIds: computed(() => selection.value.hitIds),
    canGeocode: computed(() => selection.value.canGeocode),
    canFromUtm: computed(() => selection.value.canFromUtm),
    load: controller.load,
    searchRadius: controller.searchRadius,
    checkLocation: controller.checkLocation,
    setReference: controller.setReference,
    applyTexts: controller.applyTexts,
    refreshUtm: controller.refreshUtm,
    applyUtm: controller.applyUtm,
    geocode: controller.geocode,
    simplifyArea: controller.simplifyArea,
    loadFile: controller.loadFile,
    loadSource: controller.loadSource,
  }
}
