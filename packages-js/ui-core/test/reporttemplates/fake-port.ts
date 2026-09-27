/**
 * Port mit den Antworten des echten Python-Backends (Fixtures von
 * auditcore_reporting.web, erzeugt aus den mitgelieferten neutralen Vorlagen).
 * `calls` hält die Anfragen fest; `failing` lässt eine Methode scheitern.
 */
import type { ReporttemplatesPort, TemplateCatalogue, TemplateDetail, TemplatePreview, TemplateRenderRequest, TemplateRequest } from '../../src'
import list from '../fixtures/reporttemplates-list.json'
import report from '../fixtures/reporttemplates-pruefbericht.json'
import memo from '../fixtures/reporttemplates-vermerk.json'
import previewResult from '../fixtures/reporttemplates-preview.json'
import invalidResult from '../fixtures/reporttemplates-preview-invalid.json'

export const templateCatalogue = list as unknown as TemplateCatalogue
export const templateDetails: Record<string, TemplateDetail> = {
  pruefbericht: report as unknown as TemplateDetail,
  vermerk: memo as unknown as TemplateDetail,
}
export const templatePreview = previewResult as unknown as TemplatePreview
export const templatePreviewInvalid = invalidResult as unknown as TemplatePreview

export interface TemplatesFakeOptions {
  failing?: keyof ReporttemplatesPort
  pdf?: boolean
  empty?: boolean
}

export type TemplatesFake = ReporttemplatesPort & {
  calls: { preview: [string, TemplateRequest][]; render: [string, TemplateRenderRequest][] }
}

export function fakeTemplatesPort(options: TemplatesFakeOptions = {}): TemplatesFake {
  const calls: TemplatesFake['calls'] = { preview: [], render: [] }
  const fail = (name: keyof ReporttemplatesPort): void => {
    if (options.failing === name) throw new Error('Dienst nicht erreichbar')
  }
  const catalogue: TemplateCatalogue = {
    ...templateCatalogue,
    templates: options.empty ? [] : templateCatalogue.templates,
    formats: { ...templateCatalogue.formats, pdf: options.pdf ?? true },
  }
  return {
    calls,
    templates: async () => (fail('templates'), catalogue),
    template: async (id) => {
      fail('template')
      const detail = templateDetails[id]
      if (!detail) throw new Error(`Vorlage ${id} ist nicht registriert.`)
      return detail
    },
    preview: async (id, request) => {
      fail('preview')
      calls.preview.push([id, request])
      return 'pruefbehoerde' in request.data ? templatePreview : templatePreviewInvalid
    },
    render: async (id, request) => {
      fail('render')
      calls.render.push([id, request])
      return { blob: new Blob(['PK']), filename: `${request.filename ?? id}.${request.format}`, mediaType: 'application/octet-stream' }
    },
  }
}
