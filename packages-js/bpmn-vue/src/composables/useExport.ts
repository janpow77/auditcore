/**
 * Export orchestration: SVG/PNG/PDF with post-processing, BPMN, MyST and
 * report tables; optionally neutralised (the neutral diagram is rendered in
 * an off-screen editor so the image contains no bodies or findings).
 */

import {
  buildMystSnippet,
  collectExportData,
  copyToClipboard,
  download,
  fileName,
  findingsList,
  headerOf,
  imageToPdf,
  loadDefinitions,
  modelFromDefinitions,
  neutralize,
  prepareSvg,
  PROCESS_TABLE_COLUMNS,
  processTable,
  riskControlMatrix,
  svgToJpeg,
  svgToPng,
  toCsv,
  toMyst,
  type ExportChoice,
  type ExportFormat,
  type NeutralizationResult,
  type PaletteColor,
  type ProcessModel,
  type ProfileData,
} from '@flowaudit/bpmn-flowaudit'
import type { EditorFactory } from '../editor/createEditor'
import type { EditorStore } from '../stores/editorStore'

export interface ExportContext {
  editor: EditorStore
  factory: EditorFactory
  name: () => string
  diagramId: () => string | undefined
  profile: () => ProfileData | null
  author: () => string
  replacements: () => Record<string, string>
  palette?: readonly PaletteColor[]
}

export interface ExportResult {
  format: ExportFormat
  neutralization?: NeutralizationResult
  copied?: boolean
}

async function renderOffscreen(factory: EditorFactory, xml: string, profile: ProfileData | null): Promise<string> {
  const host = document.createElement('div')
  host.style.cssText = 'position:fixed;left:-10000px;top:0;width:1600px;height:1200px;'
  document.body.appendChild(host)
  const editor = factory({ container: host, locale: 'de', flowaudit: { profile } })
  try {
    await editor.importXML(xml)
    return (await editor.saveSVG()).svg
  } finally {
    editor.destroy()
    host.remove()
  }
}

type Writer = (xml: string, svg: () => Promise<string>, model: ProcessModel, choice: ExportChoice, name: string) => Promise<boolean | void>

const blob = (text: string, type: string) => new Blob([text], { type: `${type};charset=utf-8` })

export function useExport(ctx: ExportContext) {
  function decorate(svg: string, model: ProcessModel, choice: ExportChoice): string {
    const data = collectExportData(model, ctx.palette)
    const header = headerOf(model.info, choice.title)
    return prepareSvg(svg, {
      title: choice.title,
      subtitle: choice.subtitle,
      headerColor: choice.showHeader ? header.color : undefined,
      headerTextColor: header.textColor,
      showLegend: choice.showLegend,
      showMarkerLegend: choice.showMarkerLegend,
      showMetadata: choice.showMetadata,
      showLegalBases: choice.showLegalBases,
      colors: data.colors,
      markers: data.markers,
      legalBases: data.legalBases,
      metadata: { createdOn: new Date().toLocaleDateString('de-DE'), editor: ctx.author() || '–', version: model.info?.version ?? '1' },
    })
  }

  const WRITERS: Partial<Record<ExportFormat, Writer>> = {
    svg: async (_xml, svg, model, choice, name) => download(blob(decorate(await svg(), model, choice), 'image/svg+xml'), fileName(name, 'svg')),
    png: async (_xml, svg, model, choice, name) => download(await svgToPng(decorate(await svg(), model, choice)), fileName(name, 'png')),
    pdf: async (_xml, svg, model, choice, name) => {
      const image = await svgToJpeg(decorate(await svg(), model, choice))
      const pdf = imageToPdf(image, { format: choice.pageFormat, orientation: choice.orientation, title: choice.showHeader ? undefined : choice.title })
      download(new Blob([pdf.buffer as ArrayBuffer], { type: 'application/pdf' }), fileName(name, 'pdf'))
    },
    bpmn: async (xml, _svg, _model, _choice, name) => download(blob(xml, 'application/xml'), fileName(name, 'bpmn')),
    myst: async (xml, _svg, _model, choice, name) => copyToClipboard(buildMystSnippet({ title: choice.title, name, id: ctx.diagramId() ?? null, xml })),
    'prozesstabelle-csv': async (_xml, _svg, model, _choice, name) => download(blob(toCsv(processTable(model), PROCESS_TABLE_COLUMNS, { bom: true }), 'text/csv'), fileName(`${name}_Prozesstabelle`, 'csv')),
    'prozesstabelle-myst': async (_xml, _svg, model, choice) => copyToClipboard(toMyst(processTable(model), PROCESS_TABLE_COLUMNS, { title: choice.title })),
    'rcm-csv': async (_xml, _svg, model, _choice, name) => download(blob(toCsv(riskControlMatrix(model), undefined, { bom: true }), 'text/csv'), fileName(`${name}_RCM`, 'csv')),
    'feststellungen-csv': async (_xml, _svg, model, _choice, name) => download(blob(toCsv(findingsList(model), undefined, { bom: true }), 'text/csv'), fileName(`${name}_Feststellungen`, 'csv')),
  }

  async function run(choice: ExportChoice): Promise<ExportResult> {
    const original = await ctx.editor.exportXml()
    const neutralization = choice.neutral ? neutralize(original, { profile: ctx.profile(), replacements: ctx.replacements() }) : undefined
    const xml = neutralization?.xml ?? original
    const model = neutralization ? modelFromDefinitions((await loadDefinitions(xml)).definitions) : ctx.editor.model()
    const svg = () => (neutralization ? renderOffscreen(ctx.factory, xml, ctx.profile()) : ctx.editor.exportSvg())
    const writer = WRITERS[choice.format]
    const copied = writer ? await writer(xml, svg, model, choice, ctx.name()) : undefined
    return { format: choice.format, neutralization, copied: typeof copied === 'boolean' ? copied : undefined }
  }

  return { run, decorate }
}
