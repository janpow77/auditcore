// Zustandsautomat der Berichtsvorlagen (Vue und React): Vorlagen laden, Vorlage
// wählen, Datenvertrag anzeigen, Vorschau und Bericht über den Port (reporting_ui/1).

import type { DownloadFile } from '@auditcore/common'
import { createRunner, createStore, IDLE, type RequestState, type Store } from '../store'
import type {
  ReporttemplatesPort,
  TemplateCatalogue,
  TemplateData,
  TemplateDetail,
  TemplateFormat,
  TemplatePreview,
  TemplateRenderRequest,
  TemplateRequest,
} from './types'

export interface ReporttemplatesCallbacks {
  selected?: (detail: TemplateDetail) => void
  previewed?: (result: TemplatePreview) => void
  rendered?: (file: DownloadFile) => void
  failed?: (message: string) => void
}

/** Stand; `error` ist die Meldung der letzten abgelehnten Anfrage. */
export interface ReporttemplatesData extends RequestState<string> {
  catalogue: TemplateCatalogue | null
  templateId: string | null
  detail: TemplateDetail | null
  format: TemplateFormat | null
  designId: string | null
  filename: string
  preview: TemplatePreview | null
  /** Vorschau passt nicht mehr zu Vorlage, Gestaltung oder Daten. */
  stale: boolean
  renderedName: string | null
}

export interface ReporttemplatesSource {
  port: () => ReporttemplatesPort | null | undefined
  /** Daten der Anwendung; ohne Daten gelten die Beispieldaten der Vorlage. */
  data?: () => TemplateData | null | undefined
  callbacks?: () => ReporttemplatesCallbacks
}

export interface ReporttemplatesController {
  store: Store<ReporttemplatesData>
  load: () => Promise<void>
  select: (id: string | null) => Promise<void>
  preview: () => Promise<void>
  render: () => Promise<DownloadFile | null>
  setFormat: (format: TemplateFormat | null) => void
  setDesign: (designId: string | null) => void
  setFilename: (filename: string) => void
  /** Daten der Anwendung haben sich geändert. */
  dataChanged: () => void
}

export const INITIAL_REPORTTEMPLATES: ReporttemplatesData = {
  ...IDLE, catalogue: null, templateId: null, detail: null, format: null, designId: null,
  filename: '', preview: null, stale: false, renderedName: null,
}

const errorText = (error: unknown): string => (error instanceof Error ? error.message : String(error))

/** Daten für Vorschau und Bericht: die der Anwendung, sonst die Beispieldaten. */
export function reporttemplatesData(state: ReporttemplatesData, data: TemplateData | null | undefined): TemplateData | null {
  return data ?? state.detail?.sample ?? null
}

/** Anfrage aus Zustand und Daten oder `null`, solange keine Vorlage geladen ist. */
export function buildTemplateRequest(state: ReporttemplatesData, data: TemplateData | null | undefined): TemplateRequest | null {
  const values = reporttemplatesData(state, data)
  if (!state.detail || !values) return null
  return { data: values, version: state.detail.version, ...(state.designId ? { design: state.designId } : {}) }
}

function firstFormat(detail: TemplateDetail, catalogue: TemplateCatalogue | null): TemplateFormat | null {
  return detail.formats.find((format) => catalogue?.formats[format] !== false) ?? detail.formats[0] ?? null
}

export function createReporttemplatesController(source: ReporttemplatesSource): ReporttemplatesController {
  const store = createStore<ReporttemplatesData>({ ...INITIAL_REPORTTEMPLATES })
  const run = createRunner(store, () => source.port() ?? null, errorText, (message) => source.callbacks?.().failed?.(message))
  const request = (): TemplateRequest | null => buildTemplateRequest(store.get(), source.data?.())
  const changed = (patch: Partial<ReporttemplatesData>): void =>
    store.set((state) => ({ ...patch, stale: state.preview !== null, renderedName: null }))

  async function select(id: string | null): Promise<void> {
    store.set({ templateId: id, detail: null, preview: null, stale: false, renderedName: null })
    if (!id) return
    const detail = await run('detail', (port) => port.template(id))
    if (!detail || store.get().templateId !== id) return
    store.set((state) => ({ detail, format: firstFormat(detail, state.catalogue) }))
    source.callbacks?.().selected?.(detail)
  }

  return {
    store,
    async load() {
      const catalogue = await run('load', (port) => port.templates())
      if (!catalogue) return
      store.set({ catalogue, designId: catalogue.designs[0]?.id ?? null })
      await select(catalogue.templates[0]?.id ?? null)
    },
    select,
    async preview() {
      const built = request()
      const id = store.get().templateId
      if (!built || !id) return
      const result = await run('preview', (port) => port.preview(id, built))
      if (!result) return
      store.set({ preview: result, stale: false })
      source.callbacks?.().previewed?.(result)
    },
    async render() {
      const built = request()
      const { templateId, format, filename, catalogue } = store.get()
      if (!built || !templateId || !format || catalogue?.formats[format] === false) return null
      const name = filename.trim()
      const body: TemplateRenderRequest = { ...built, format, ...(name ? { filename: name } : {}) }
      const file = await run('render', (port) => port.render(templateId, body))
      if (!file) return null
      store.set({ renderedName: file.filename })
      source.callbacks?.().rendered?.(file)
      return file
    },
    setFormat: (format) => store.set({ format, renderedName: null }),
    setDesign: (designId) => changed({ designId }),
    setFilename: (filename) => store.set({ filename, renderedName: null }),
    dataChanged: () => changed({}),
  }
}
