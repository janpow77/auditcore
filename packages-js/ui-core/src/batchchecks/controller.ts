// Zustandsautomat von <flowaudit-batch-checks> (Vue und React): Katalog laden,
// Bestand als CSV (gemeinsamer TableImport-Controller) oder JSON einlesen,
// Spalten zuordnen, Prüflauf und Export ausschließlich über den Port.

import type { DecimalSeparator, DownloadFile } from '@auditcore/common'
import { createRunner, createStore, IDLE, type RequestState, type Store } from '../store'
import { createTableImportController, type TableImportController } from '../tabular'
import { batchchecksAutoMapping, batchchecksDecimal, batchchecksJsonDocuments, batchchecksLooksLikeJson, buildBatchchecksRequest, type BatchchecksError, type BatchchecksMapping } from './model'
import type { BatchchecksAnswer, BatchchecksCatalogue, BatchchecksDocument, BatchchecksExportFormat, BatchchecksPort, BatchchecksRequest } from './types'

export type BatchchecksBusy = 'load' | 'run' | 'export'

export interface BatchchecksCallbacks {
  completed?: (answer: BatchchecksAnswer) => void
  failed?: (message: string) => void
}

/** Stand; `error` ist die Meldung der letzten abgelehnten Anfrage. */
export interface BatchchecksData extends RequestState<string> {
  catalogue: BatchchecksCatalogue | null
  /** Belege aus einer JSON-Datei (sonst gilt die Tabelle des TableImport-Controllers). */
  json: readonly BatchchecksDocument[] | null
  jsonName: string
  mapping: BatchchecksMapping
  totalVolume: string
  supplementary: boolean
  validation: BatchchecksError | null
  request: BatchchecksRequest | null
  answer: BatchchecksAnswer | null
  /** Regel, deren Befunde angezeigt werden (`null` = alle). */
  ruleFilter: string | null
}

export interface BatchchecksSource {
  port: () => BatchchecksPort | null | undefined
  callbacks?: () => BatchchecksCallbacks
}

export const INITIAL_BATCHCHECKS: BatchchecksData = {
  ...IDLE, catalogue: null, json: null, jsonName: '', mapping: {}, totalVolume: '', supplementary: true,
  validation: null, request: null, answer: null, ruleFilter: null,
}

const errorText = (error: unknown): string => (error instanceof Error ? error.message : String(error))

/** Datei lesen: JSON als Belegliste, sonst Tabelle mit automatischer Spaltenzuordnung. */
function fileActions(store: Store<BatchchecksData>, table: TableImportController) {
  /** Spalten neu zuordnen; das Dezimaltrennzeichen aus allen zugeordneten Zahlenspalten ableiten. */
  const remap = (): void => {
    const loaded = table.store.get().table
    const fields = store.get().catalogue?.fields ?? []
    const mapping = batchchecksAutoMapping(fields, loaded?.header ?? [])
    store.set({ mapping })
    if (loaded) table.setDecimal(batchchecksDecimal(loaded, fields, mapping))
  }
  function loadText(filename: string, text: string): void {
    store.set({ answer: null, request: null, ruleFilter: null, validation: null })
    if (batchchecksLooksLikeJson(filename, text)) {
      const json = batchchecksJsonDocuments(text)
      table.load('', '')
      store.set({ json, jsonName: filename, mapping: {}, validation: json ? null : 'json' })
      return
    }
    store.set({ json: null, jsonName: '' })
    table.load(filename, text)
    remap()
  }
  return {
    /** Dateiinhalt übernehmen (Datei bereits gelesen, z. B. Beispielbestand). */
    loadText,
    readFile: async (file: File) => loadText(file.name, await file.text()),
    setHasHeader: (hasHeader: boolean) => {
      table.setHasHeader(hasHeader)
      table.reparse()
      remap()
    },
    setDecimal: (decimal: DecimalSeparator) => table.setDecimal(decimal),
    /** Feld einer Spalte zuordnen (`null` = keine). */
    setColumn: (field: string, column: number | null) => store.set((state) => ({ mapping: { ...state.mapping, [field]: column } })),
  }
}

export function createBatchchecksController(source: BatchchecksSource) {
  const store = createStore<BatchchecksData>({ ...INITIAL_BATCHCHECKS })
  const table = createTableImportController()
  const callbacks = (): BatchchecksCallbacks => source.callbacks?.() ?? {}
  const run = createRunner<BatchchecksPort, string, BatchchecksData>(store, () => source.port() ?? null, errorText, (message) => callbacks().failed?.(message))

  async function load(): Promise<void> {
    const catalogue = await run('load', (port) => port.catalogue())
    if (catalogue) store.set({ catalogue, supplementary: catalogue.defaults.supplementary })
  }

  async function check(): Promise<void> {
    const state = store.get()
    if (!state.catalogue) return
    const loaded = table.store.get()
    const built = buildBatchchecksRequest({
      catalogue: state.catalogue, table: state.json ? null : loaded.table, json: state.json, mapping: state.mapping,
      decimal: loaded.decimal, totalVolume: state.totalVolume, supplementary: state.supplementary,
    })
    store.set({ validation: built.ok ? null : built.error })
    if (!built.ok) return
    const answer = await run('run', (port) => port.run(built.request))
    if (!answer) return
    store.set({ answer, request: built.request, ruleFilter: null })
    callbacks().completed?.(answer)
  }

  /** Export des letzten Laufs; die Datei bietet die Oberfläche zum Speichern an. */
  async function exportRun(format: BatchchecksExportFormat): Promise<DownloadFile | null> {
    const request = store.get().request
    return request ? run('export', (port) => port.exportRun(request, format)) : null
  }

  return {
    store,
    /** Tabellenimport (gemeinsamer TableImport-Controller aus `@auditcore/ui-core`). */
    table,
    load,
    check,
    exportRun,
    ...fileActions(store, table),
    setTotalVolume: (totalVolume: string) => store.set({ totalVolume }),
    setSupplementary: (supplementary: boolean) => store.set({ supplementary }),
    setRuleFilter: (ruleFilter: string | null) => store.set({ ruleFilter }),
    /** Vorhandenes Ergebnis anzeigen (Eigenschaft `result`). */
    showAnswer: (answer: BatchchecksAnswer | null) => store.set({ answer, ruleFilter: null }),
  }
}

export type BatchchecksController = ReturnType<typeof createBatchchecksController>
