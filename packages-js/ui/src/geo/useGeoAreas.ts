import { computed, ref, shallowRef, watch, type ComputedRef, type Ref, type ShallowRef } from 'vue'
import type { Runner } from '../rest'
import { areasFromGeoPackage, TOLERANCE_STEPS } from './model'
import type { GeoArea, GeoPackageResult, GeoPort, SimplifyResult, SimplifyUnit } from './types'

export type GeoBusy = 'load' | 'radius' | 'locate' | 'utm' | 'simplify' | 'gpkg' | 'geocode'
export type GeoHint = 'needReference' | 'needArea' | 'needModel' | null

export interface UseGeoAreas {
  areas: ComputedRef<readonly GeoArea[]>
  areaId: Ref<string | null>
  area: ComputedRef<GeoArea | null>
  simplifyUnit: Ref<SimplifyUnit>
  simplifyStep: Ref<number>
  simplifyTolerance: ComputedRef<number>
  simplifyResult: ShallowRef<SimplifyResult | null>
  gpkgResult: ShallowRef<GeoPackageResult | null>
  simplifyArea: () => Promise<void>
  loadFile: (file: Blob) => Promise<void>
  loadSource: (name: string) => Promise<void>
}

function missing(what: string): Promise<never> {
  return Promise.reject(new Error(`${what} nicht angeboten.`))
}

/** Flächen (übergeben und aus GeoPackage geladen), Auswahl und Vereinfachung. */
export function useGeoAreas(
  runner: Runner<GeoPort, GeoBusy>,
  givenAreas: () => readonly GeoArea[],
  hint: Ref<GeoHint>,
  loadedCallback?: (areas: readonly GeoArea[], result: GeoPackageResult) => void,
): UseGeoAreas {
  const loaded = shallowRef<readonly GeoArea[]>([])
  const areas = computed(() => [...givenAreas(), ...loaded.value])
  const areaId = ref<string | null>(null)
  const area = computed(() => areas.value.find((entry) => entry.id === areaId.value) ?? null)
  const simplifyUnit = ref<SimplifyUnit>('meter')
  const simplifyStep = ref(4)
  const simplifyTolerance = computed(() => TOLERANCE_STEPS[simplifyUnit.value][simplifyStep.value] ?? 0)
  const simplifyResult = shallowRef<SimplifyResult | null>(null)
  const gpkgResult = shallowRef<GeoPackageResult | null>(null)

  watch(areaId, () => {
    simplifyResult.value = null
  })
  watch(simplifyUnit, (unit) => {
    simplifyStep.value = Math.min(simplifyStep.value, TOLERANCE_STEPS[unit].length - 1)
    simplifyResult.value = null
  })

  async function simplifyArea(): Promise<void> {
    const target = area.value
    hint.value = target ? null : 'needArea'
    if (!target) return
    const request = { flaeche: target.geometry, toleranz: simplifyTolerance.value, einheit: simplifyUnit.value }
    const result = await runner.run('simplify', (active) => active.simplify(request))
    if (result) simplifyResult.value = result
  }

  function accept(result: GeoPackageResult, origin: string): void {
    gpkgResult.value = result
    const added = areasFromGeoPackage(result, origin)
    loaded.value = [...loaded.value.filter((entry) => !entry.id.startsWith(`${origin}:`)), ...added]
    if (!areaId.value && added[0]) areaId.value = added[0].id
    loadedCallback?.(added, result)
  }

  async function loadFile(file: Blob): Promise<void> {
    const result = await runner.run('gpkg', (active) => active.loadGeoPackage?.(file) ?? missing('GeoPackage-Upload'))
    if (result) accept(result, 'datei')
  }

  async function loadSource(name: string): Promise<void> {
    const result = await runner.run('gpkg', (active) => active.loadSource?.(name) ?? missing('Serverquelle'))
    if (result) accept(result, name)
  }

  return { areas, areaId, area, simplifyUnit, simplifyStep, simplifyTolerance, simplifyResult, gpkgResult, simplifyArea, loadFile, loadSource }
}
