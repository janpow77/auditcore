// Zustandsautomat von „Kennung prüfen“ (Vue und React): Katalog laden,
// Einzelprüfung, Stapelprüfung aus einer Tabelle. Die Datei liest der
// gemeinsame TableImport-Controller; geprüft wird ausschließlich über den Port.

import { createRunner, createStore, IDLE, type RequestState, type Store } from '../store'
import { createTableImportController, type TableImportController, type TableImportData } from '../tabular'
import { buildIdentifierBatch, buildIdentifierCheck, identifierProfileKinds, type IdentifierBatchMapping, type IdentifierColumn, type IdentifierError } from './model'
import type { IdentifierBatchAnswer, IdentifierBatchRequest, IdentifierCatalogue, IdentifierResult, IdentifiersPort } from './types'

export type IdentifierBusy = 'load' | 'check' | 'batch'

export interface IdentifierCallbacks {
  checked?: (result: IdentifierResult) => void
  batchChecked?: (answer: IdentifierBatchAnswer) => void
  failed?: (message: string) => void
}

export interface IdentifierData extends RequestState<string> {
  catalogue: IdentifierCatalogue | null
  profileId: string | null
  kind: string | null
  value: string
  country: string
  result: IdentifierResult | null
  validation: IdentifierError | null
  /** Kennungsart aller Tabellenzeilen; `null` = aus `kindColumn`. */
  batchKind: string | null
  kindColumn: number | null
  countryColumn: number | null
  batchRequest: IdentifierBatchRequest | null
  batch: IdentifierBatchAnswer | null
  batchValidation: IdentifierError | null
  onlyIssues: boolean
}

export const INITIAL_IDENTIFIERS: IdentifierData = {
  ...IDLE, catalogue: null, profileId: null, kind: null, value: '', country: '', result: null, validation: null,
  batchKind: null, kindColumn: null, countryColumn: null, batchRequest: null, batch: null, batchValidation: null, onlyIssues: false,
}

/** Einfache Eingabefelder, die die Oberfläche direkt setzen darf. */
export type IdentifierField = 'value' | 'country' | 'kindColumn' | 'countryColumn' | 'onlyIssues'

export interface IdentifierSource {
  port: () => IdentifiersPort | null | undefined
  callbacks?: () => IdentifierCallbacks
}

const errorText = (error: unknown): string => (error instanceof Error ? error.message : String(error))

/** Zuordnung aus beiden Zuständen (Tabelle und Kennungsprüfung). */
export function identifierBatchMapping(state: IdentifierData, loaded: TableImportData): IdentifierBatchMapping {
  return {
    table: loaded.table, hasHeader: loaded.hasHeader, valueColumn: loaded.valueColumn, refColumn: loaded.idColumn,
    kind: state.batchKind, kindColumn: state.kindColumn, countryColumn: state.countryColumn,
  }
}

function keepKind(store: Store<IdentifierData>, kind: string | null, profileId: string | null): string | null {
  const offered = identifierProfileKinds(store.get().catalogue, profileId)
  return offered.some((entry) => entry.id === kind) ? kind : (offered[0]?.id ?? null)
}

/** Datei und Spaltenzuordnung der Stapelprüfung. */
function tableActions(store: Store<IdentifierData>, table: TableImportController) {
  return {
    /** Spalte zuordnen; `null` = keine (nur optionale Spalten). */
    setColumn: (column: IdentifierColumn, index: number | null) => {
      if (column === 'value') table.setValueColumn(index ?? 0)
      else if (column === 'ref') table.setIdColumn(index)
      else store.set(column === 'kind' ? { kindColumn: index } : { countryColumn: index })
    },
    setHasHeader: (hasHeader: boolean) => {
      table.setHasHeader(hasHeader)
      table.reparse()
    },
    readFile: async (file: File) => {
      await table.read(file)
      store.set({ batch: null, batchRequest: null, batchValidation: null, kindColumn: null, countryColumn: null })
    },
  }
}

export function createIdentifierController(source: IdentifierSource) {
  const store = createStore<IdentifierData>({ ...INITIAL_IDENTIFIERS })
  const table = createTableImportController()
  const callbacks = (): IdentifierCallbacks => source.callbacks?.() ?? {}
  const run = createRunner<IdentifiersPort, string, IdentifierData>(store, () => source.port() ?? null, errorText, (message) => callbacks().failed?.(message))

  async function load(): Promise<void> {
    const loaded = await run('load', (active) => active.catalogue())
    if (!loaded) return
    store.set({ catalogue: loaded, profileId: null })
    setProfile(loaded.recommended_profile)
    store.set((state) => ({ batchKind: state.kind }))
  }

  function setProfile(profileId: string | null): void {
    const { kind, batchKind } = store.get()
    store.set({ profileId, kind: keepKind(store, kind, profileId), batchKind: batchKind === null ? null : keepKind(store, batchKind, profileId), result: null, batch: null })
  }

  async function check(): Promise<void> {
    const state = store.get()
    if (!state.catalogue) return
    const checked = buildIdentifierCheck({ catalogue: state.catalogue, profile: state.profileId, kind: state.kind, value: state.value, country: state.country })
    store.set({ validation: checked.ok ? null : checked.error })
    if (!checked.ok) return
    const answer = await run('check', (active) => active.check(checked.request))
    if (!answer) return
    store.set({ result: answer.result })
    callbacks().checked?.(answer.result)
  }

  async function checkBatch(): Promise<void> {
    const state = store.get()
    if (!state.catalogue) return
    const checked = buildIdentifierBatch(state.catalogue, state.profileId, identifierBatchMapping(state, table.store.get()))
    store.set({ batchValidation: checked.ok ? null : checked.error })
    if (!checked.ok) return
    const answer = await run('batch', (active) => active.checkBatch(checked.request))
    if (!answer) return
    store.set({ batch: answer, batchRequest: checked.request })
    callbacks().batchChecked?.(answer)
  }

  return {
    store,
    /** Datei-Import (gemeinsamer TableImport-Controller aus `@flowaudit/ui-core`). */
    table,
    load,
    check,
    checkBatch,
    setProfile,
    setKind: (kind: string | null) => store.set({ kind, result: null }),
    setBatchKind: (batchKind: string | null) => store.set({ batchKind }),
    setField: <K extends IdentifierField>(key: K, value: IdentifierData[K]) => store.set({ [key]: value } as Partial<IdentifierData>),
    ...tableActions(store, table),
  }
}

export type IdentifierController = ReturnType<typeof createIdentifierController>
