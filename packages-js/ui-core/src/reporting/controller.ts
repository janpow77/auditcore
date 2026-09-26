// Zustandsautomat des Tabellenexports (Vue und React): Formatprofile laden,
// Profil wählen, Vorschau und Export über den Port (reporting_ui/1).

import type { DownloadFile } from '@auditcore/common'
import { createRunner, createStore, IDLE, type RequestState } from '../store'
import type { FormatProfile, ReportingCatalogue, ReportingPort, ReportTableInput, WorkbookPreview, WorkbookRequest } from './types'

export type ReportingBusy = 'load' | 'preview' | 'export'
export type ReportingError = 'noTables' | 'profile'

export interface ReportingCallbacks {
  previewed?: (result: WorkbookPreview) => void
  exported?: (file: DownloadFile) => void
  failed?: (message: string) => void
}

export interface ReportingData extends RequestState<string> {
  catalogue: ReportingCatalogue | null
  profileId: string | null
  filename: string
  preview: WorkbookPreview | null
  /** Vorschau passt nicht mehr zu Profil, Dateiname oder Tabellen. */
  stale: boolean
  validation: ReportingError | null
  exportedName: string | null
}

export interface ReportingSource {
  port: () => ReportingPort | null | undefined
  tables: () => readonly ReportTableInput[]
  callbacks?: () => ReportingCallbacks
}

export const INITIAL_REPORTING: ReportingData = {
  ...IDLE, catalogue: null, profileId: null, filename: '', preview: null, stale: false, validation: null, exportedName: null,
}

export function reportingProfile(state: ReportingData): FormatProfile | null {
  return state.catalogue?.profiles.find((entry) => entry.id === state.profileId) ?? null
}

/** Anfrage aus Zustand und Tabellen oder der erste fehlende Punkt. */
export function buildWorkbookRequest(state: ReportingData, tables: readonly ReportTableInput[]): { ok: true; request: WorkbookRequest } | { ok: false; error: ReportingError } {
  if (!tables.length) return { ok: false, error: 'noTables' }
  if (!state.profileId) return { ok: false, error: 'profile' }
  const filename = state.filename.trim()
  return { ok: true, request: { profile: state.profileId, tables, ...(filename ? { filename } : {}) } }
}

const errorText = (error: unknown): string => (error instanceof Error ? error.message : String(error))

export function createReportingController(source: ReportingSource) {
  const store = createStore<ReportingData>({ ...INITIAL_REPORTING })
  const run = createRunner<ReportingPort, string, ReportingData>(store, () => source.port() ?? null, errorText, (message) => source.callbacks?.().failed?.(message))

  function checked(): WorkbookRequest | null {
    const built = buildWorkbookRequest(store.get(), source.tables())
    store.set({ validation: built.ok ? null : built.error })
    return built.ok ? built.request : null
  }

  async function load(): Promise<void> {
    const loaded = await run('load', (active) => active.profiles())
    if (!loaded) return
    store.set({ catalogue: loaded, profileId: loaded.profiles[0]?.id ?? null })
  }

  async function preview(): Promise<void> {
    const request = checked()
    if (!request) return
    const result = await run('preview', (active) => active.preview(request))
    if (!result) return
    store.set({ preview: result, stale: false })
    source.callbacks?.().previewed?.(result)
  }

  async function exportWorkbook(): Promise<DownloadFile | null> {
    const request = checked()
    if (!request) return null
    const file = await run('export', (active) => active.exportWorkbook(request))
    if (!file) return null
    store.set({ exportedName: file.filename })
    source.callbacks?.().exported?.(file)
    return file
  }

  const changed = (patch: Partial<ReportingData>): void => store.set((state) => ({ ...patch, stale: state.preview !== null, exportedName: null }))

  return {
    store,
    load,
    preview,
    exportWorkbook,
    setProfile: (profileId: string | null) => changed({ profileId }),
    setFilename: (filename: string) => changed({ filename }),
    /** Tabellen der Anwendung haben sich geändert. */
    tablesChanged: () => changed({}),
  }
}

export type ReportingController = ReturnType<typeof createReportingController>
