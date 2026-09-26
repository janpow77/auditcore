// Zustandsautomat von <flowaudit-extraction> (Vue und React): Katalog laden,
// Datei und Profil wählen, Lauf anstoßen. Erkannt wird ausschließlich über den Port.

import { createRunner, createStore, IDLE, type RequestState } from '../store'
import type { ExtractionCatalogue, ExtractionPort, ExtractionRun } from './types'

export type ExtractionBusy = 'load' | 'run'
export type ExtractionValidation = 'needFile' | 'tooLarge' | 'profile' | null

export interface ExtractionCallbacks {
  completed?: (result: ExtractionRun) => void
  failed?: (message: string) => void
}

export interface ExtractionData extends RequestState<string> {
  catalogue: ExtractionCatalogue | null
  profileId: string | null
  file: Blob | null
  filename: string
  result: ExtractionRun | null
  validation: ExtractionValidation
}

export interface ExtractionSource {
  port: () => ExtractionPort | null | undefined
  callbacks?: () => ExtractionCallbacks
}

export const INITIAL_EXTRACTION: ExtractionData = {
  ...IDLE, catalogue: null, profileId: null, file: null, filename: '', result: null, validation: null,
}

const errorText = (error: unknown): string => (error instanceof Error ? error.message : String(error))

/** Prüfung vor dem Senden (reine Funktion). */
export function extractionValidation(state: ExtractionData): ExtractionValidation {
  if (!state.file) return 'needFile'
  if (state.catalogue && state.file.size > state.catalogue.limits.max_upload_bytes) return 'tooLarge'
  const profile = state.catalogue?.profiles.find((entry) => entry.id === state.profileId)
  return profile?.available ? null : 'profile'
}

export function createExtractionController(source: ExtractionSource) {
  const store = createStore<ExtractionData>({ ...INITIAL_EXTRACTION })
  const run = createRunner<ExtractionPort, string, ExtractionData>(store, () => source.port() ?? null, errorText, (message) => source.callbacks?.().failed?.(message))

  async function load(): Promise<void> {
    const loaded = await run('load', (active) => active.catalogue())
    if (loaded) store.set({ catalogue: loaded, profileId: loaded.default_profile })
  }

  async function extract(): Promise<void> {
    const state = store.get()
    const validation = extractionValidation(state)
    store.set({ validation })
    if (validation || !state.file || !state.profileId) return
    const { file, filename, profileId } = state
    const result = await run('run', (active) => active.run(file, filename, profileId))
    if (!result) return
    store.set({ result })
    source.callbacks?.().completed?.(result)
  }

  return {
    store,
    load,
    extract,
    /** Datei wählen (`null` = Auswahl aufheben). */
    selectFile: (file: File | null) => store.set({ file, filename: file?.name ?? '', validation: null }),
    setProfile: (profileId: string | null) => store.set({ profileId, validation: null }),
    /** Vorhandenes Ergebnis anzeigen (Eigenschaft `result`). */
    showResult: (result: ExtractionRun | null) => store.set({ result }),
  }
}

export type ExtractionController = ReturnType<typeof createExtractionController>
