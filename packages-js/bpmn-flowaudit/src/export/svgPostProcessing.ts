/**
 * Post-processing of the exported SVG, ported from `svgAufbereitung.ts` of
 * the audit_designer (`bereiteSvgAuf` → `prepareSvg`) and extended by the
 * coloured header (title, subtitle, header colours from the diagram info)
 * and a marker legend.
 *
 * `saveSVG()` delivers the bare diagram with the content bounds as viewBox,
 * drawn in diagram coordinates – footnote marks can therefore be placed
 * exactly at the tasks. Depending on the export dialog it adds a header,
 * colour legend, marker legend, directory of legal bases with numbered
 * marks at the elements and a footer with date, editor and version.
 */

import { type FooterBlock, LINE_HEIGHT, SVG_NS, svgGroup, svgRect, svgText, wrapWords } from './svgBlocks'

export interface LegalBasisNote {
  elementId: string
  name: string
  text: string
  x: number
  y: number
  width: number
}

export interface UsedColor {
  fill: string
  stroke: string
  label: string
  meaning: string
  count: number
}

export interface UsedMarker {
  type: string
  label: string
  count: number
}

export interface SvgTexts {
  colorLegend: string
  markerLegend: string
  legalBases: string
  footer: (meta: { createdOn: string; editor: string; version: string }) => string
  elements: (count: number) => string
}

export const GERMAN_SVG_TEXTS: SvgTexts = {
  colorLegend: 'Farblegende',
  markerLegend: 'Kennzeichen',
  legalBases: 'Rechtsgrundlagen',
  footer: ({ createdOn, editor, version }) => `Erstellt am ${createdOn} · Bearbeitung: ${editor} · Version ${version}`,
  elements: (count) => `${count} Element${count === 1 ? '' : 'e'}`,
}

export interface PrepareSvgOptions {
  title: string
  subtitle?: string
  headerColor?: string
  headerTextColor?: string
  showLegend: boolean
  showMarkerLegend?: boolean
  showMetadata: boolean
  showLegalBases: boolean
  colors: UsedColor[]
  markers?: UsedMarker[]
  legalBases: LegalBasisNote[]
  metadata: { createdOn: string; editor: string; version: string }
  texts?: SvgTexts
}

const MARGIN = 24

function legendBlock(doc: Document, title: string, rows: { swatch?: UsedColor; text: string }[]): FooterBlock {
  const group = svgGroup(doc)
  group.appendChild(svgText(doc, 0, 0, title, { size: 13, bold: true }))
  rows.forEach((row, index) => {
    const y = 14 + index * 22
    if (row.swatch) group.appendChild(svgRect(doc, { x: 0, y, width: 18, height: 14, rx: 2, fill: row.swatch.fill, stroke: row.swatch.stroke }))
    group.appendChild(svgText(doc, row.swatch ? 26 : 0, y + 11, row.text, { size: 11 }))
  })
  return { group, height: 14 + rows.length * 22 + 10 }
}

function legalBasisBlock(doc: Document, title: string, notes: LegalBasisNote[], width: number): FooterBlock {
  const group = svgGroup(doc)
  group.appendChild(svgText(doc, 0, 0, title, { size: 13, bold: true }))
  const chars = Math.max(40, Math.floor(width / 6.2))
  let y = 14
  notes.forEach((note, index) => {
    const lines = wrapWords(`${note.name}: ${note.text}`, chars)
    group.appendChild(svgText(doc, 0, y + 10, `[${index + 1}]`, { size: 11, bold: true }))
    lines.forEach((line, lineIndex) => group.appendChild(svgText(doc, 30, y + 10 + lineIndex * LINE_HEIGHT, line, { size: 11 })))
    y += lines.length * LINE_HEIGHT + 6
  })
  return { group, height: y + 10 }
}

function footnoteMarks(doc: Document, content: SVGGElement, notes: LegalBasisNote[]): void {
  notes.forEach((note, index) => {
    const mark = svgGroup(doc)
    const cx = note.x + note.width - 6
    const cy = note.y + 6
    const circle = doc.createElementNS(SVG_NS, 'circle')
    circle.setAttribute('cx', String(cx))
    circle.setAttribute('cy', String(cy))
    circle.setAttribute('r', '9')
    circle.setAttribute('fill', '#14006e')
    mark.appendChild(circle)
    mark.appendChild(svgText(doc, cx, cy + 4, String(index + 1), { size: 11, bold: true, color: '#ffffff', anchor: 'middle' }))
    content.appendChild(mark)
  })
}

function footerBlocks(doc: Document, options: PrepareSvgOptions, texts: SvgTexts, width: number): FooterBlock[] {
  const blocks: FooterBlock[] = []
  if (options.showLegend && options.colors.length) {
    const rows = options.colors.map((color) => ({ swatch: color, text: `${color.label} — ${color.meaning} (${texts.elements(color.count)})` }))
    blocks.push(legendBlock(doc, texts.colorLegend, rows))
  }
  if (options.showMarkerLegend && options.markers?.length) {
    blocks.push(legendBlock(doc, texts.markerLegend, options.markers.map((m) => ({ text: `${m.label} (${texts.elements(m.count)})` }))))
  }
  if (options.showLegalBases && options.legalBases.length) blocks.push(legalBasisBlock(doc, texts.legalBases, options.legalBases, width))
  if (options.showMetadata) {
    const group = svgGroup(doc)
    group.appendChild(svgText(doc, 0, 12, texts.footer(options.metadata), { size: 10, color: '#4b5563' }))
    blocks.push({ group, height: 26 })
  }
  return blocks
}

function headerHeight(options: PrepareSvgOptions): number {
  if (!options.title.trim()) return 0
  return options.subtitle?.trim() ? 66 : 46
}

function drawHeader(doc: Document, svg: Element, options: PrepareSvgOptions, box: { minX: number; minY: number; width: number }): void {
  const top = box.minY - MARGIN - headerHeight(options)
  const colored = Boolean(options.headerColor)
  if (colored) svg.appendChild(svgRect(doc, { x: box.minX - MARGIN, y: top, width: box.width + 2 * MARGIN, height: headerHeight(options) - 8, fill: options.headerColor as string }))
  const color = colored ? options.headerTextColor ?? '#ffffff' : '#111827'
  svg.appendChild(svgText(doc, box.minX, top + 28, options.title.trim(), { size: 20, bold: true, color }))
  if (options.subtitle?.trim()) svg.appendChild(svgText(doc, box.minX, top + 48, options.subtitle.trim(), { size: 13, color }))
}

function readViewBox(svg: Element | null): number[] | null {
  if (!svg || svg.nodeName.toLowerCase() !== 'svg') return null
  const viewBox = (svg.getAttribute('viewBox') ?? '').split(/\s+/).map(Number)
  return viewBox.length === 4 && viewBox.every((value) => Number.isFinite(value)) ? viewBox : null
}

/** Wraps the content in a group; <defs> stays on top so arrow markers keep working. */
function wrapContent(doc: Document, svg: Element): SVGGElement {
  const content = svgGroup(doc)
  content.setAttribute('class', 'flowaudit-diagramm')
  for (const child of Array.from(svg.childNodes)) {
    if (child.nodeName.toLowerCase() === 'defs') continue
    svg.removeChild(child)
    content.appendChild(child)
  }
  return content
}

/** Adds header, legends and directory of legal bases to the exported SVG. */
export function prepareSvg(source: string, options: PrepareSvgOptions): string {
  const doc = new DOMParser().parseFromString(source, 'image/svg+xml')
  const svg = doc.documentElement
  const viewBox = readViewBox(svg)
  if (!viewBox) return source
  const [minX, minY, width, height] = viewBox
  const texts = options.texts ?? GERMAN_SVG_TEXTS
  const content = wrapContent(doc, svg)
  if (options.showLegalBases) footnoteMarks(doc, content, options.legalBases)

  const head = headerHeight(options)
  const blocks = footerBlocks(doc, options, texts, width)
  const footer = blocks.reduce((sum, block) => sum + block.height, 0)
  const totalWidth = width + 2 * MARGIN
  const totalHeight = height + 2 * MARGIN + head + (footer > 0 ? footer + MARGIN : 0)
  svg.setAttribute('viewBox', `${minX - MARGIN} ${minY - MARGIN - head} ${totalWidth} ${totalHeight}`)
  svg.setAttribute('width', String(Math.round(totalWidth)))
  svg.setAttribute('height', String(Math.round(totalHeight)))
  // White ground: otherwise the image is transparent in Word.
  svg.insertBefore(svgRect(doc, { x: minX - MARGIN, y: minY - MARGIN - head, width: totalWidth, height: totalHeight, fill: '#ffffff' }), svg.firstChild)
  svg.appendChild(content)
  if (head) drawHeader(doc, svg, options, { minX, minY, width })

  let offset = minY + height + MARGIN
  for (const block of blocks) {
    block.group.setAttribute('transform', `translate(${minX}, ${offset})`)
    svg.appendChild(block.group)
    offset += block.height
  }
  return new XMLSerializer().serializeToString(doc)
}
