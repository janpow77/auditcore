/**
 * Data for the export dialog: used colours (legend), used markers and
 * maintained legal bases with the position of their shape. Ported from
 * `leseExportDaten`/`sammleFarben` of the audit_designer.
 */

import { displayText } from '../model/legalBasis'
import { displayName, type ModelElement, type ProcessModel } from '../model/processModel'
import { MARKER_TYPES, label } from '../schema/vocabulary'
import { PALETTE_COLORS, findPaletteColor, normalizeColor, type PaletteColor } from './colorPalette'
import type { LegalBasisNote, UsedColor, UsedMarker } from './svgPostProcessing'

/**
 * Counts used colours for the legend. Colours outside the palette are kept
 * but labelled „Nicht zugeordnet“ – dropping them silently would present
 * an incomplete legend as complete.
 */
export function collectColors(elements: ModelElement[], palette: readonly PaletteColor[] = PALETTE_COLORS): UsedColor[] {
  const counter = new Map<string, UsedColor>()
  for (const element of elements) {
    const fill = normalizeColor(element.color?.fill)
    if (!fill) continue
    const known = findPaletteColor(fill, palette)
    const entry = counter.get(fill) ?? {
      fill,
      stroke: known?.stroke ?? '#374151',
      label: known?.label ?? 'Nicht zugeordnet',
      meaning: known?.meaning ?? 'Farbe außerhalb der abgestimmten Palette',
      count: 0,
    }
    entry.count += 1
    counter.set(fill, entry)
  }
  const order = palette.map((color) => normalizeColor(color.fill))
  const rank = (fill: string) => (order.indexOf(fill) === -1 ? 99 : order.indexOf(fill))
  return [...counter.values()].sort((a, b) => rank(a.fill) - rank(b.fill))
}

export function collectMarkers(elements: ModelElement[]): UsedMarker[] {
  const counter = new Map<string, number>()
  for (const element of elements) for (const marker of element.extensions.markers) counter.set(marker.type, (counter.get(marker.type) ?? 0) + 1)
  return [...counter.entries()].map(([type, count]) => ({ type, count, label: label(MARKER_TYPES[type]) || type }))
}

export function collectLegalBasisNotes(elements: ModelElement[]): LegalBasisNote[] {
  return elements
    .filter((element) => element.extensions.legalBases.length > 0)
    .map((element) => ({
      elementId: element.id,
      name: displayName(element),
      text: element.extensions.legalBases.map(displayText).join('; '),
      x: element.bounds?.x ?? 0,
      y: element.bounds?.y ?? 0,
      width: element.bounds?.width ?? 0,
    }))
}

export interface ExportData {
  colors: UsedColor[]
  markers: UsedMarker[]
  legalBases: LegalBasisNote[]
}

export function collectExportData(model: ProcessModel, palette?: readonly PaletteColor[]): ExportData {
  const elements = model.elements.filter((element) => !['bpmn:Process', 'bpmn:Collaboration'].includes(element.type))
  return { colors: collectColors(elements, palette), markers: collectMarkers(elements), legalBases: collectLegalBasisNotes(elements) }
}
