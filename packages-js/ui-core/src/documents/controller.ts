// Zustandsautomat von <flowaudit-comparisons> (Vue und React): gespeicherte
// Vergleiche laden, neuen Vergleich hochladen, Ergebnis importieren, löschen.

import { RestError } from '@flowaudit/common'
import { createRunner, createStore, IDLE, type RequestState, type Store } from '../store'
import type { ImportRequest, SynopsisPort, SynopsisRestClient } from '../synopsis/port'
import type { Comparison, ComparisonProfile, ComparisonSummary, RowStatus } from '../synopsis/types'
import { DEFAULT_FORM, DEFAULT_MAX_UPLOAD_BYTES, formProblems, toCompareFields, toggleSection, type CompareForm } from './form'
import { parseImport } from './importing'
import { summaryOf } from './list'
import type { ComparisonsTranslate } from './messages'

/**
 * Port zur Anwendung: {@link createSynopsisRestClient} erfüllt ihn vollständig.
 * `load`/`updateRows`/`exportUrl` braucht nur die eingebettete Synopse,
 * `importResult` nur der Import.
 */
export type ComparisonsPort = Pick<SynopsisRestClient, 'profiles' | 'list' | 'create' | 'remove'> &
  Partial<Pick<SynopsisRestClient, 'importResult' | 'load' | 'updateRows' | 'exportUrl'>>

/** Der Port als Datenzugang der eingebetteten Synopse, wenn er Vergleiche laden kann. */
export function synopsisPortOf(port: ComparisonsPort | null | undefined): SynopsisPort | null {
  return port?.load ? (port as SynopsisPort) : null
}

/** Fehler einer Portanfrage: Meldung des Servers bzw. `network_error` mit Status 0. */
export interface ComparisonsError {
  code: string
  message: string
  status: number
}

export type ComparisonsBusy = 'load' | 'create' | 'import' | 'remove'

export interface ComparisonsData extends RequestState<ComparisonsError> {
  profiles: ComparisonProfile[]
  items: ComparisonSummary[]
  loaded: boolean
  query: string
  form: CompareForm
  /** Nach dem ersten Absenden werden Befunde der Formularprüfung angezeigt. */
  submitted: boolean
  /** Geöffneter Vergleich (Synopse). */
  openId: string | null
  /** Vergleich, dessen Löschen bestätigt werden soll. */
  pendingRemove: string | null
}

export interface ComparisonsHooks {
  onCreated?: (comparison: Comparison) => void
  onImported?: (comparison: Comparison) => void
  onRemoved?: (id: string) => void
  onError?: (error: ComparisonsError) => void
}

export interface ComparisonsControllerOptions extends ComparisonsHooks {
  port: () => ComparisonsPort | null
  t: () => ComparisonsTranslate
  maxBytes?: () => number
  lang?: () => string
}

export const INITIAL_COMPARISONS: ComparisonsData = {
  ...IDLE, profiles: [], items: [], loaded: false, query: '', form: DEFAULT_FORM, submitted: false, openId: null, pendingRemove: null,
}

export function asComparisonsError(error: unknown, t: ComparisonsTranslate): ComparisonsError {
  if (error instanceof RestError) return { code: error.code, message: error.message, status: error.status }
  const raw = error instanceof Error ? error.message : String(error)
  return { code: 'network_error', message: t('networkError', { message: raw }), status: 0 }
}

type Run = ReturnType<typeof createRunner<ComparisonsPort, ComparisonsError, ComparisonsData>>

function titleOf(state: ComparisonsData, id: string): string {
  return state.items.find((item) => item.id === id)?.title ?? id
}

/** Neuer oder importierter Vergleich: oben in die Liste, Meldung für `aria-live`. */
function added(store: Store<ComparisonsData>, comparison: Comparison, notice: string): void {
  store.set((state) => ({
    items: [summaryOf(comparison), ...state.items.filter((item) => item.id !== comparison.id)],
    notice,
  }))
}

function formActions(store: Store<ComparisonsData>) {
  const update = (patch: Partial<CompareForm>): void => store.set((state) => ({ form: { ...state.form, ...patch } }))
  return {
    updateForm: update,
    toggleSection: (status: RowStatus, enabled: boolean) => update({ sections: toggleSection(store.get().form.sections, status, enabled) }),
    resetForm: () => store.set({ form: DEFAULT_FORM, submitted: false }),
  }
}

function writeActions(store: Store<ComparisonsData>, run: Run, options: ComparisonsControllerOptions) {
  const maxBytes = (): number => options.maxBytes?.() ?? DEFAULT_MAX_UPLOAD_BYTES
  const lang = (): string => options.lang?.() ?? 'de'

  async function submit(): Promise<Comparison | null> {
    const form = store.get().form
    store.set({ submitted: true })
    const { oldFile, newFile } = form
    if (formProblems(form, maxBytes(), lang()).length > 0 || !oldFile || !newFile) return null
    const created = await run('create', (port) => port.create(oldFile, oldFile.name, newFile, newFile.name, toCompareFields(form)))
    if (!created) return null
    added(store, created, options.t()('created', { title: created.title }))
    store.set({ form: DEFAULT_FORM, submitted: false })
    options.onCreated?.(created)
    return created
  }

  async function importText(text: string): Promise<Comparison | null> {
    const parsed = parseImport(text)
    if (!parsed.ok) return fail(parsed.key)
    if (!options.port()?.importResult) return fail('importUnsupported')
    const request: ImportRequest = parsed.request
    const imported = await run('import', (port) => port.importResult?.(request) ?? Promise.reject(new Error('importResult')))
    if (!imported) return null
    added(store, imported, options.t()('imported', { title: imported.title }))
    options.onImported?.(imported)
    return imported
  }

  function fail(key: 'importUnreadable' | 'importInvalid' | 'importUnsupported'): null {
    const error: ComparisonsError = { code: 'invalid_import', message: options.t()(key), status: 0 }
    store.set({ error })
    options.onError?.(error)
    return null
  }

  async function confirmRemove(): Promise<boolean> {
    const id = store.get().pendingRemove
    if (!id) return false
    const title = titleOf(store.get(), id)
    const done = await run('remove', async (port) => {
      await port.remove(id)
      return true
    })
    store.set({ pendingRemove: null })
    if (!done) return false
    store.set((state) => ({
      items: state.items.filter((item) => item.id !== id),
      openId: state.openId === id ? null : state.openId,
      notice: options.t()('removed', { title }),
    }))
    options.onRemoved?.(id)
    return true
  }

  return { submit, importText, confirmRemove }
}

export function createComparisonsController(options: ComparisonsControllerOptions) {
  const store = createStore<ComparisonsData>(INITIAL_COMPARISONS)
  const run = createRunner(store, options.port, (error) => asComparisonsError(error, options.t()), options.onError)

  async function load(): Promise<void> {
    const loaded = await run('load', async (port) => Promise.all([port.profiles(), port.list()]))
    if (loaded) store.set({ profiles: loaded[0], items: loaded[1], loaded: true })
  }

  return {
    store,
    load,
    ...formActions(store),
    ...writeActions(store, run, options),
    setQuery: (query: string) => store.set({ query }),
    open: (id: string | null) => store.set({ openId: id }),
    askRemove: (id: string) => store.set({ pendingRemove: id }),
    cancelRemove: () => store.set({ pendingRemove: null }),
    dismissError: () => store.set({ error: null }),
  }
}

export type ComparisonsController = ReturnType<typeof createComparisonsController>
