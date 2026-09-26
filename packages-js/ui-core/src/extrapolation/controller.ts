// Zustandsautomat von <flowaudit-extrapolation> (Vue und React): Methode,
// Konfidenzniveau, Schichten und geprüfte Einheiten erfassen, hochrechnen
// (TER), getrennt davon die Restfehlerquote (RER) berechnen und exportieren.
// Gerechnet wird ausschließlich über den Port.

import type { DownloadFile } from '@flowaudit/common'
import { createRunner, createStore, IDLE, type RequestState, type Store } from '../store'
import {
  buildEvaluationRequest,
  buildResidualRequest,
  confidenceChoices,
  EMPTY_RESIDUAL,
  emptyStratum,
  emptyUnit,
  extrapolationMethodById,
  residualFormFrom,
  stratumRows,
  unitRows,
  type ExtrapolationForm,
  type ExtrapolationFormError,
  type ExtrapolationIssues,
  type ResidualForm,
  type StratumRow,
  type UnitRow,
} from './model'
import type {
  EvaluationRequest,
  EvaluationResult,
  ExtrapolationCatalogue,
  ExtrapolationExportFormat,
  ExtrapolationMethod,
  ExtrapolationPort,
  ResidualResult,
  StratumInput,
  UnitInput,
} from './types'

export type ExtrapolationBusy = 'load' | 'evaluate' | 'residual' | 'export'

export interface ExtrapolationCallbacks {
  evaluated?: (result: EvaluationResult) => void
  residualComputed?: (result: ResidualResult) => void
  failed?: (message: string) => void
}

/** Stand der Hochrechnung; `error` ist die Meldung der letzten abgelehnten Anfrage. */
export interface ExtrapolationData extends RequestState<string> {
  catalogue: ExtrapolationCatalogue | null
  form: ExtrapolationForm
  formError: ExtrapolationFormError | null
  issues: ExtrapolationIssues
  result: EvaluationResult | null
  lastRequest: EvaluationRequest | null
  residualForm: ResidualForm
  residualIssues: ExtrapolationIssues
  residual: ResidualResult | null
}

export interface ExtrapolationSource {
  port: () => ExtrapolationPort | null | undefined
  strata: () => readonly StratumInput[]
  units: () => readonly UnitInput[]
  /** Zahl → Eingabetext im Sprachformat. */
  format: (value: number) => string
  callbacks?: () => ExtrapolationCallbacks
}

const EMPTY_FORM: ExtrapolationForm = { methodId: '', confidence: null, profileId: null, sampleSize: '', materiality: '', strata: [], units: [] }

export const INITIAL_EXTRAPOLATION: ExtrapolationData = {
  ...IDLE, catalogue: null, form: EMPTY_FORM, formError: null, issues: {}, result: null, lastRequest: null,
  residualForm: EMPTY_RESIDUAL, residualIssues: {}, residual: null,
}

export function extrapolationMethod(state: ExtrapolationData): ExtrapolationMethod | null {
  return extrapolationMethodById(state.catalogue, state.form.methodId)
}

const errorText = (error: unknown): string => (error instanceof Error ? error.message : String(error))

function replaceAt<T>(rows: readonly T[], index: number, patch: Partial<T>): T[] {
  return rows.map((row, position) => (position === index ? { ...row, ...patch } : row))
}

function createRows(store: Store<ExtrapolationData>) {
  let counter = 0
  const key = (prefix: string): string => `${prefix}n${(counter += 1)}`
  const patchForm = (patch: Partial<ExtrapolationForm>): void => store.set((state) => ({ form: { ...state.form, ...patch } }))
  return {
    patchForm,
    addStratum: () => patchForm({ strata: [...store.get().form.strata, emptyStratum(key('s'))] }),
    updateStratum: (index: number, patch: Partial<StratumRow>) => patchForm({ strata: replaceAt(store.get().form.strata, index, patch) }),
    removeStratum: (index: number) => patchForm({ strata: store.get().form.strata.filter((_, position) => position !== index) }),
    addUnit: () => {
      const form = store.get().form
      patchForm({ units: [...form.units, emptyUnit(key('u'), form.strata[0]?.name ?? '')] })
    },
    updateUnit: (index: number, patch: Partial<UnitRow>) => patchForm({ units: replaceAt(store.get().form.units, index, patch) }),
    removeUnit: (index: number) => patchForm({ units: store.get().form.units.filter((_, position) => position !== index) }),
  }
}

type Run = ReturnType<typeof createRunner<ExtrapolationPort, string, ExtrapolationData>>

function createRequests(source: ExtrapolationSource, store: Store<ExtrapolationData>, run: Run) {
  async function evaluate(): Promise<void> {
    const state = store.get()
    if (!state.catalogue) return
    const checked = buildEvaluationRequest(state.catalogue, state.form)
    store.set({ formError: checked.ok ? null : checked.error, issues: checked.ok ? {} : checked.issues })
    if (!checked.ok) return
    const result = await run('evaluate', (port) => port.evaluate(checked.request))
    if (!result) return
    store.set({ result, lastRequest: checked.request, residual: null, residualIssues: {}, residualForm: residualFormFrom(result, store.get().residualForm, source.format) })
    source.callbacks?.().evaluated?.(result)
  }

  async function computeResidual(): Promise<void> {
    const state = store.get()
    const checked = buildResidualRequest(state.residualForm, state.lastRequest?.materiality_rate ?? 0.02)
    store.set({ residualIssues: checked.ok ? {} : checked.issues })
    if (!checked.ok) return
    const result = await run('residual', (port) => port.residual(checked.request))
    if (!result) return
    store.set({ residual: result })
    source.callbacks?.().residualComputed?.(result)
  }

  async function exportEvaluation(format: ExtrapolationExportFormat): Promise<DownloadFile | null> {
    const request = store.get().lastRequest
    return request ? run('export', (port) => port.exportEvaluation(request, format)) : null
  }

  return { evaluate, computeResidual, exportEvaluation }
}

export function createExtrapolationController(source: ExtrapolationSource) {
  const store = createStore<ExtrapolationData>({ ...INITIAL_EXTRAPOLATION })
  const run: Run = createRunner<ExtrapolationPort, string, ExtrapolationData>(store, () => source.port() ?? null, errorText, (message) => source.callbacks?.().failed?.(message))
  const rows = createRows(store)

  /** Eigenschaften `strata`/`units` als bearbeitbare Zeilen übernehmen (verwirft das Ergebnis). */
  function applyInputs(): void {
    const strata = stratumRows(source.strata(), source.format)
    rows.patchForm({ strata: strata.length ? strata : [emptyStratum('s1')], units: unitRows(source.units(), source.format) })
    store.set({ result: null, residual: null, issues: {}, formError: null })
  }

  async function load(): Promise<void> {
    const catalogue = await run('load', (port) => port.profiles())
    if (!catalogue) return
    store.set({ catalogue })
    rows.patchForm({ profileId: catalogue.recommended_profile, materiality: source.format(catalogue.materiality.default * 100) })
    applyInputs()
  }

  function selectMethod(methodId: string): void {
    const state = store.get()
    const method = extrapolationMethodById(state.catalogue, methodId)
    const keep = state.catalogue && state.form.confidence !== null && confidenceChoices(state.catalogue, method).includes(state.form.confidence)
    rows.patchForm({ methodId, confidence: keep ? state.form.confidence : null })
    store.set({ formError: null })
  }

  return {
    store,
    load,
    applyInputs,
    selectMethod,
    ...createRequests(source, store, run),
    ...rows,
    setConfidence: (confidence: number | null) => rows.patchForm({ confidence }),
    setProfile: (profileId: string | null) => rows.patchForm({ profileId }),
    setSampleSize: (sampleSize: string) => rows.patchForm({ sampleSize }),
    setMateriality: (materiality: string) => rows.patchForm({ materiality }),
    setResidual: (patch: Partial<ResidualForm>) => store.set((state) => ({ residualForm: { ...state.residualForm, ...patch } })),
  }
}

export type ExtrapolationController = ReturnType<typeof createExtrapolationController>
