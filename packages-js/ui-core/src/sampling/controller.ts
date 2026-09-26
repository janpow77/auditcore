// Zustandsautomat von <flowaudit-sampling> (Vue und React): Methodenwahl,
// Parameter, Stichprobenumfang, Grundgesamtheit, Auswahl mit Seed, Export.
// Die Fachlogik liegt im Port; hier werden nur Eingaben geprüft, Anfragen
// gebildet und Ergebnisse gehalten.

import type { DownloadFile } from '@auditcore/common'
import { createRunner, createStore, IDLE, type RequestState } from '../store'
import {
  buildSelectionRequest,
  buildSizeRequest,
  initialTexts,
  populationSuggestions,
  strataOf,
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

/** Stand des Stichprobenrechners; `error` ist die Meldung der letzten abgelehnten Anfrage. */
export interface SamplingData extends RequestState<string> {
  catalogue: SamplingCatalogue | null
  methodId: string
  texts: Record<string, string>
  confidence: number | null
  fieldErrors: Readonly<Record<string, FieldError>>
  size: SizeResult | null
  /** Importierte Grundgesamtheit; `null` = Eigenschaft `items`. */
  imported: readonly PopulationItem[] | null
  sampleSize: string
  seed: string
  variant: SelectionVariant | null
  allocation: AllocationMethod | null
  selection: SelectionResult | null
  lastRequest: (SelectionRequest & { seed: number }) | null
  selectionError: SelectionError | null
}

export interface SamplingSource {
  port: () => SamplingPort | null | undefined
  items: () => readonly PopulationItem[]
  /** Zahl → Text im Sprachformat (Startwerte und Vorschläge der Felder). */
  format: (value: number) => string
  callbacks?: () => SamplingCallbacks
}

export const INITIAL_SAMPLING: SamplingData = {
  ...IDLE, catalogue: null, methodId: '', texts: {}, confidence: null, fieldErrors: {}, size: null, imported: null,
  sampleSize: '', seed: '', variant: null, allocation: null, selection: null, lastRequest: null, selectionError: null,
}

export function samplingProfile(state: SamplingData): MethodProfile | null {
  return state.catalogue?.methods.find((method) => method.id === state.methodId) ?? null
}

export function samplingPopulation(state: SamplingData, items: readonly PopulationItem[]): readonly PopulationItem[] {
  return state.imported ?? items
}

export function isStratifiedPopulation(population: readonly PopulationItem[]): boolean {
  return strataOf(population).length > 0
}

const errorText = (error: unknown): string => (error instanceof Error ? error.message : String(error))

function createActions(source: SamplingSource, store: ReturnType<typeof createStore<SamplingData>>) {
  const run = createRunner<SamplingPort, string, SamplingData>(store, () => source.port() ?? null, errorText, (message) => source.callbacks?.().failed?.(message))

  async function calculate(): Promise<void> {
    const state = store.get()
    const profile = samplingProfile(state)
    if (!profile) return
    const checked = buildSizeRequest(profile, state.texts, state.confidence)
    store.set({ fieldErrors: checked.ok ? {} : checked.errors })
    if (!checked.ok) return
    const result = await run('size', (port) => port.size(checked.request))
    if (!result) return
    store.set({ size: result, sampleSize: String(result.sample_size) })
    source.callbacks?.().sizeCalculated?.(result)
  }

  async function draw(freshSeed = false): Promise<void> {
    const profile = samplingProfile(store.get())
    if (!profile) return
    if (freshSeed) store.set({ seed: '' })
    const state = store.get()
    const checked = buildSelectionRequest({
      profile, items: samplingPopulation(state, source.items()), sampleSize: state.sampleSize, seed: state.seed,
      variant: state.variant, allocation: state.allocation,
    })
    store.set({ selectionError: checked.ok ? null : checked.error })
    if (!checked.ok) return
    const result = await run('selection', (port) => port.selection(checked.request))
    if (!result) return
    store.set({ selection: result, lastRequest: { ...checked.request, seed: result.seed }, seed: String(result.seed) })
    source.callbacks?.().selectionDrawn?.(result)
  }

  return { run, calculate, draw }
}

export function createSamplingController(source: SamplingSource) {
  const store = createStore<SamplingData>({ ...INITIAL_SAMPLING })
  const { run, calculate, draw } = createActions(source, store)

  function selectMethod(id: string): void {
    const profile = samplingProfile({ ...store.get(), methodId: id })
    store.set({
      methodId: id, texts: profile ? initialTexts(profile, source.format) : {}, confidence: null, fieldErrors: {},
      size: null, variant: profile?.default_variant ?? null, selection: null,
    })
  }

  async function load(): Promise<void> {
    const result = await run('load', (active) => active.profiles())
    if (!result) return
    store.set({ catalogue: result })
    selectMethod(result.recommended.mus)
  }

  function applySuggestions(): void {
    const state = store.get()
    const suggestions = populationSuggestions(samplingPopulation(state, source.items()))
    const texts = { ...state.texts }
    for (const spec of samplingProfile(state)?.parameters ?? []) {
      const value = suggestions[spec.key]
      if (value !== undefined) texts[spec.key] = source.format(value)
    }
    store.set({ texts })
  }

  async function exportSelection(format: ExportFormat): Promise<DownloadFile | null> {
    const request = store.get().lastRequest
    return request ? run('export', (port) => port.exportSelection(request, format)) : null
  }

  return {
    store,
    load,
    selectMethod,
    applySuggestions,
    calculate,
    draw,
    exportSelection,
    /** Importierte Grundgesamtheit übernehmen; `null` kehrt zur Eigenschaft `items` zurück. */
    usePopulation: (imported: readonly PopulationItem[] | null) => store.set({ imported, selection: null }),
    setTexts: (texts: Record<string, string>) => store.set({ texts }),
    setConfidence: (confidence: number | null) => store.set({ confidence }),
    setSampleSize: (sampleSize: string) => store.set({ sampleSize }),
    setSeed: (seed: string) => store.set({ seed }),
    setVariant: (variant: SelectionVariant | null) => store.set({ variant }),
    setAllocation: (allocation: AllocationMethod | null) => store.set({ allocation }),
  }
}

export type SamplingController = ReturnType<typeof createSamplingController>
