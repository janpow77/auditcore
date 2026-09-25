import { computed, ref, shallowRef, type ComputedRef, type Ref, type ShallowRef } from 'vue'
import { createRunner, type DownloadFile, type Runner } from '../rest'
import {
  buildSelectionRequest,
  buildSizeRequest,
  initialTexts,
  populationSuggestions,
  type FieldError,
  type SelectionValidation,
} from './model'
import type {
  AllocationMethod,
  ExportFormat,
  MethodProfile,
  PopulationItem,
  SamplingCatalogue,
  SamplingPort,
  SelectionRequest,
  SelectionResult,
  SelectionVariant,
  SizeResult,
} from './types'

export type SamplingBusy = 'load' | 'size' | 'selection' | 'export'
export type SelectionError = Extract<SelectionValidation, { ok: false }>['error']

export interface SamplingCallbacks {
  sizeCalculated?: (result: SizeResult) => void
  selectionDrawn?: (result: SelectionResult) => void
  failed?: (message: string) => void
}

type SamplingRunner = Runner<SamplingPort, SamplingBusy>

/** Methodenwahl, Parameter und Stichprobenumfang. */
function useSize(runner: SamplingRunner, format: (value: number) => string, callbacks: SamplingCallbacks) {
  const catalogue = shallowRef<SamplingCatalogue | null>(null)
  const methodId = ref('')
  const profile = computed(() => catalogue.value?.methods.find((m) => m.id === methodId.value) ?? null)
  const texts = ref<Record<string, string>>({})
  const confidence = ref<number | null>(null)
  const fieldErrors = ref<Readonly<Record<string, FieldError>>>({})
  const size = shallowRef<SizeResult | null>(null)

  function selectMethod(id: string): void {
    methodId.value = id
    texts.value = profile.value ? initialTexts(profile.value, format) : {}
    confidence.value = null
    fieldErrors.value = {}
    size.value = null
  }

  async function calculate(): Promise<SizeResult | null> {
    if (!profile.value) return null
    const checked = buildSizeRequest(profile.value, texts.value, confidence.value)
    fieldErrors.value = checked.ok ? {} : checked.errors
    if (!checked.ok) return null
    const result = await runner.run('size', (port) => port.size(checked.request))
    if (result) {
      size.value = result
      callbacks.sizeCalculated?.(result)
    }
    return result
  }

  return { catalogue, methodId, profile, texts, confidence, fieldErrors, size, selectMethod, calculate }
}

/** Grundgesamtheit, Auswahl mit Seed und Export. */
function useSelection(runner: SamplingRunner, items: () => readonly PopulationItem[], callbacks: SamplingCallbacks) {
  const imported = shallowRef<readonly PopulationItem[] | null>(null)
  const population = computed(() => imported.value ?? items())
  const sampleSize = ref('')
  const seed = ref('')
  const variant = ref<SelectionVariant | null>(null)
  const allocation = ref<AllocationMethod | null>(null)
  const selection = shallowRef<SelectionResult | null>(null)
  const lastRequest = shallowRef<(SelectionRequest & { seed: number }) | null>(null)
  const selectionError = ref<SelectionError | null>(null)

  async function draw(profile: MethodProfile, freshSeed: boolean): Promise<void> {
    if (freshSeed) seed.value = ''
    const checked = buildSelectionRequest({
      profile, items: population.value, sampleSize: sampleSize.value, seed: seed.value,
      variant: variant.value, allocation: allocation.value,
    })
    selectionError.value = checked.ok ? null : checked.error
    if (!checked.ok) return
    const result = await runner.run('selection', (port) => port.selection(checked.request))
    if (!result) return
    selection.value = result
    lastRequest.value = { ...checked.request, seed: result.seed }
    seed.value = String(result.seed)
    callbacks.selectionDrawn?.(result)
  }

  async function exportSelection(format: ExportFormat): Promise<DownloadFile | null> {
    const request = lastRequest.value
    return request ? runner.run('export', (port) => port.exportSelection(request, format)) : null
  }

  function usePopulation(next: readonly PopulationItem[] | null): void {
    imported.value = next
    selection.value = null
  }

  return {
    population, sampleSize, seed, variant, allocation, selection, selectionError, draw, exportSelection, usePopulation,
  }
}

export interface UseSampling {
  catalogue: ShallowRef<SamplingCatalogue | null>
  profile: ComputedRef<MethodProfile | null>
  methodId: Ref<string>
  texts: Ref<Record<string, string>>
  confidence: Ref<number | null>
  fieldErrors: Ref<Readonly<Record<string, FieldError>>>
  size: ShallowRef<SizeResult | null>
  population: ComputedRef<readonly PopulationItem[]>
  sampleSize: Ref<string>
  seed: Ref<string>
  variant: Ref<SelectionVariant | null>
  allocation: Ref<AllocationMethod | null>
  selection: ShallowRef<SelectionResult | null>
  selectionError: Ref<SelectionError | null>
  busy: Ref<SamplingBusy | null>
  failure: Ref<string>
  load: () => Promise<void>
  selectMethod: (id: string) => void
  /** Importierte Grundgesamtheit übernehmen; `null` kehrt zur Eigenschaft `items` zurück. */
  usePopulation: (items: readonly PopulationItem[] | null) => void
  applySuggestions: () => void
  calculate: () => Promise<void>
  draw: (freshSeed?: boolean) => Promise<void>
  exportSelection: (format: ExportFormat) => Promise<DownloadFile | null>
}

/**
 * Zustand und Abläufe des Stichprobenrechners. Die Fachlogik liegt im Port;
 * hier werden nur Eingaben geprüft, Anfragen gebildet und Ergebnisse gehalten.
 */
export function useSampling(
  port: () => SamplingPort | null,
  items: () => readonly PopulationItem[],
  format: (value: number) => string,
  callbacks: SamplingCallbacks = {},
): UseSampling {
  const runner = createRunner<SamplingPort, SamplingBusy>(port, callbacks.failed)
  const sizing = useSize(runner, format, callbacks)
  const picking = useSelection(runner, items, callbacks)

  function selectMethod(id: string): void {
    sizing.selectMethod(id)
    picking.variant.value = sizing.profile.value?.default_variant ?? null
    picking.selection.value = null
  }

  return {
    ...sizing,
    ...picking,
    busy: runner.busy,
    failure: runner.failure,
    selectMethod,
    load: async () => {
      const result = await runner.run('load', (active) => active.profiles())
      if (!result) return
      sizing.catalogue.value = result
      selectMethod(result.recommended.mus)
    },
    applySuggestions: () => {
      const suggestions = populationSuggestions(picking.population.value)
      const next = { ...sizing.texts.value }
      for (const spec of sizing.profile.value?.parameters ?? []) {
        const value = suggestions[spec.key]
        if (value !== undefined) next[spec.key] = format(value)
      }
      sizing.texts.value = next
    },
    calculate: async () => {
      const result = await sizing.calculate()
      if (result) picking.sampleSize.value = String(result.sample_size)
    },
    draw: async (freshSeed = false) => {
      if (sizing.profile.value) await picking.draw(sizing.profile.value, freshSeed)
    },
  }
}
