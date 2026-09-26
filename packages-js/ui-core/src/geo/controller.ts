// Zustandsautomat der Geo-Karte (Vue und React): Katalog, Bezugspunkt mit UTM
// und Adresssuche, Umkreis, Punkt in Fläche, Vereinfachung, GeoPackage.
// Jede Berechnung läuft über den Port (auditcore_geo.web).

import { createRunner, createStore, type Store } from '../store'
import { areasFromGeoPackage, parseLatLon, TOLERANCE_STEPS, type CoordinateError } from './model'
import type { MapLayers } from './mapView'
import type {
  GeoArea,
  GeoCatalogue,
  GeocodeResult,
  GeoPackageResult,
  GeoPoint,
  GeoPort,
  LatLon,
  LocateResult,
  RadiusResult,
  SimplifyResult,
  SimplifyUnit,
  UtmResult,
} from './types'

export type GeoBusy = 'load' | 'radius' | 'locate' | 'utm' | 'simplify' | 'gpkg' | 'geocode'
export type GeoHint = 'needReference' | 'needArea' | 'needModel' | null

export interface GeoMapCallbacks {
  radius?: (result: RadiusResult) => void
  located?: (result: LocateResult) => void
  areasLoaded?: (areas: readonly GeoArea[], result: GeoPackageResult) => void
  reference?: (point: LatLon | null) => void
  failed?: (message: string) => void
}

export interface GeoData {
  busy: GeoBusy | null
  failure: string
  error: string | null
  notice: string
  hint: GeoHint
  catalogue: GeoCatalogue | null
  earthModel: string | null
  radiusMetres: number
  radiusResult: RadiusResult | null
  boundaryInside: boolean
  toleranceMetres: number
  locateResult: LocateResult | null
  loadedAreas: readonly GeoArea[]
  areaId: string | null
  simplifyUnit: SimplifyUnit
  simplifyStep: number
  simplifyResult: SimplifyResult | null
  gpkgResult: GeoPackageResult | null
  ellipsoid: string
  reference: LatLon | null
  latText: string
  lonText: string
  coordinateError: CoordinateError
  utm: UtmResult | null
  geocodeResult: GeocodeResult | null
}

/** Eingaben der Komponente (Props). */
export interface GeoInputs {
  port: GeoPort | null
  points: readonly GeoPoint[]
  areas: readonly GeoArea[]
}

export interface GeoSelection {
  areas: readonly GeoArea[]
  area: GeoArea | null
  simplifyTolerance: number
  hitIds: ReadonlySet<string>
  canGeocode: boolean
  layers: MapLayers
}

function layersOf(state: GeoData, inputs: GeoInputs, areas: readonly GeoArea[], hits: ReadonlySet<string>): MapLayers {
  return {
    points: inputs.points,
    areas,
    reference: state.reference,
    radiusMetres: state.radiusResult ? state.radiusResult.radius_m : null,
    hits,
    selectedArea: state.areaId,
    simplified: state.simplifyResult?.geometrie ?? null,
  }
}

function geocodingAvailable(state: GeoData, inputs: GeoInputs): boolean {
  return Boolean(inputs.port?.geocode) && state.catalogue?.geocoder.aktiv === true
}

export function selectGeo(state: GeoData, inputs: GeoInputs): GeoSelection {
  const areas = [...inputs.areas, ...state.loadedAreas]
  const hitIds = new Set(state.radiusResult?.treffer.map((hit) => hit.id) ?? [])
  return {
    areas,
    area: areas.find((entry) => entry.id === state.areaId) ?? null,
    simplifyTolerance: TOLERANCE_STEPS[state.simplifyUnit][state.simplifyStep] ?? 0,
    hitIds,
    canGeocode: geocodingAvailable(state, inputs),
    layers: layersOf(state, inputs, areas, hitIds),
  }
}

/** Einfache Eingabefelder, die die Oberfläche direkt setzen darf. */
export type GeoField = 'radiusMetres' | 'earthModel' | 'boundaryInside' | 'toleranceMetres' | 'simplifyStep' | 'ellipsoid' | 'latText' | 'lonText'

const INITIAL: GeoData = {
  busy: null, failure: '', error: null, notice: '', hint: null, catalogue: null, earthModel: null, radiusMetres: 5000,
  radiusResult: null, boundaryInside: true, toleranceMetres: 0, locateResult: null, loadedAreas: [], areaId: null,
  simplifyUnit: 'meter', simplifyStep: 4, simplifyResult: null, gpkgResult: null, ellipsoid: 'GRS80', reference: null,
  latText: '', lonText: '', coordinateError: null, utm: null, geocodeResult: null,
}

function rounded(value: number): string {
  return String(Math.round(value * 1e6) / 1e6)
}

function missing(what: string): Promise<never> {
  return Promise.reject(new Error(`${what} nicht angeboten.`))
}

type Run = <T>(kind: GeoBusy, task: (port: GeoPort) => Promise<T>) => Promise<T | null>

/** Voraussetzungen einer Berechnung; fehlt etwas, steht der Hinweis im Zustand. */
function prepare(store: Store<GeoData>, area: GeoArea | null, needsArea: boolean): { point: LatLon; model: string } | null {
  const { reference: point, earthModel: model } = store.get()
  const hint: GeoHint = !point ? 'needReference' : !model ? 'needModel' : needsArea && !area ? 'needArea' : null
  store.set({ hint })
  return point && model && !hint ? { point, model } : null
}

function referenceActions(store: Store<GeoData>, run: Run, inputs: () => GeoInputs, callbacks: GeoMapCallbacks) {
  async function refreshUtm(): Promise<void> {
    const { reference: point, ellipsoid } = store.get()
    if (!point) return
    const result = await run('utm', (active) => active.utm({ punkt: point, ellipsoid }))
    if (result) store.set({ utm: result })
  }

  async function setReference(point: LatLon | null): Promise<void> {
    store.set({
      reference: point, coordinateError: null, latText: point ? rounded(point.lat) : '', lonText: point ? rounded(point.lon) : '',
      utm: null, radiusResult: null, locateResult: null, hint: null,
    })
    callbacks.reference?.(point)
    await refreshUtm()
  }

  async function applyTexts(): Promise<void> {
    const parsed = parseLatLon(store.get().latText, store.get().lonText)
    store.set({ coordinateError: parsed.error })
    if (parsed.point) await setReference(parsed.point)
  }

  async function geocode(query: string): Promise<void> {
    const text = query.trim()
    if (!selectGeo(store.get(), inputs()).canGeocode || !text) return
    const result = await run('geocode', (active) => active.geocode?.(text) ?? missing('Adresssuche'))
    if (result) store.set({ geocodeResult: result })
  }

  return { refreshUtm, setReference, applyTexts, geocode }
}

function areaActions(store: Store<GeoData>, run: Run, inputs: () => GeoInputs, callbacks: GeoMapCallbacks) {
  const area = (): GeoArea | null => selectGeo(store.get(), inputs()).area

  async function simplifyArea(): Promise<void> {
    const target = area()
    store.set({ hint: target ? null : 'needArea' })
    if (!target) return
    const { simplifyUnit: einheit } = store.get()
    const toleranz = selectGeo(store.get(), inputs()).simplifyTolerance
    const result = await run('simplify', (active) => active.simplify({ flaeche: target.geometry, toleranz, einheit }))
    if (result) store.set({ simplifyResult: result })
  }

  function accept(result: GeoPackageResult, origin: string): void {
    const added = areasFromGeoPackage(result, origin)
    store.set((state) => ({
      gpkgResult: result,
      loadedAreas: [...state.loadedAreas.filter((entry) => !entry.id.startsWith(`${origin}:`)), ...added],
    }))
    if (!store.get().areaId && added[0]) selectArea(added[0].id)
    callbacks.areasLoaded?.(added, result)
  }

  function selectArea(id: string | null): void {
    if (id === store.get().areaId) return
    store.set({ areaId: id, simplifyResult: null, locateResult: null })
  }

  function setSimplifyUnit(unit: SimplifyUnit): void {
    store.set((state) => ({ simplifyUnit: unit, simplifyStep: Math.min(state.simplifyStep, TOLERANCE_STEPS[unit].length - 1), simplifyResult: null }))
  }

  async function loadFile(file: Blob): Promise<void> {
    const result = await run('gpkg', (active) => active.loadGeoPackage?.(file) ?? missing('GeoPackage-Upload'))
    if (result) accept(result, 'datei')
  }

  async function loadSource(name: string): Promise<void> {
    const result = await run('gpkg', (active) => active.loadSource?.(name) ?? missing('Serverquelle'))
    if (result) accept(result, name)
  }

  return { simplifyArea, selectArea, setSimplifyUnit, loadFile, loadSource }
}

function calculations(store: Store<GeoData>, run: Run, inputs: () => GeoInputs, callbacks: GeoMapCallbacks) {
  async function searchRadius(): Promise<void> {
    const given = prepare(store, null, false)
    if (!given) return
    const punkte = inputs().points.map(({ id, lat, lon }) => ({ id, lat, lon }))
    const request = { zentrum: given.point, punkte, radius_m: store.get().radiusMetres, erdmodell: given.model }
    const result = await run('radius', (active) => active.radius(request))
    store.set({ radiusResult: result })
    if (result) callbacks.radius?.(result)
  }

  async function checkLocation(): Promise<void> {
    const target = selectGeo(store.get(), inputs()).area
    const given = prepare(store, target, true)
    if (!given || !target) return
    const { boundaryInside, toleranceMetres } = store.get()
    const request = { punkt: given.point, flaeche: target.geometry, erdmodell: given.model, rand_gilt_als_innen: boundaryInside, rand_toleranz_m: toleranceMetres }
    const result = await run('locate', (active) => active.locate(request))
    store.set({ locateResult: result })
    if (result) callbacks.located?.(result)
  }

  async function load(): Promise<void> {
    const result = await run('load', (active) => active.catalogue())
    if (!result) return
    const ellipsoid = result.ellipsoide.includes('GRS80') ? 'GRS80' : (result.ellipsoide[0] ?? 'GRS80')
    store.set({ catalogue: result, earthModel: result.empfohlenes_erdmodell, boundaryInside: result.rand_gilt_als_innen_empfohlen, ellipsoid })
  }

  return { load, searchRadius, checkLocation }
}

export interface GeoControllerOptions extends GeoMapCallbacks {
  inputs: () => GeoInputs
}

export function createGeoController(options: GeoControllerOptions) {
  const store = createStore<GeoData>(INITIAL)
  const toError = (error: unknown): string => (error instanceof Error ? error.message : String(error))
  const runner = createRunner<GeoPort, string, GeoData>(store, () => options.inputs().port, toError, options.failed)
  const run: Run = async (kind, task) => {
    store.set({ failure: '' })
    const result = await runner(kind, task)
    const error = store.get().error
    if (error) store.set({ failure: error, error: null })
    return result
  }
  return {
    store,
    /** Einfaches Eingabefeld setzen (Radius, Erdmodell, Rand, Toleranz, Stufe, Ellipsoid, Texte). */
    setField: <K extends GeoField>(key: K, value: GeoData[K]) => store.set({ [key]: value } as Partial<GeoData>),
    ...calculations(store, run, options.inputs, options),
    ...referenceActions(store, run, options.inputs, options),
    ...areaActions(store, run, options.inputs, options),
  }
}

export type GeoController = ReturnType<typeof createGeoController>
