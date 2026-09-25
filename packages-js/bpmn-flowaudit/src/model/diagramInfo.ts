/**
 * Diagram info (`flowaudit:diagrammInfo`): read, write and migrate from the
 * audit_designer data model (`flowstat_bpmn_diagrams`).
 */

import type { Canvas, ModdleElement, ModdleFactory, Modeling } from '../diagram/services'
import { FLOWAUDIT_SCHEMA_VERSION } from '../schema/descriptor'
import type { DiagramInfo } from '../schema/types'
import { definitionsOf, mainElement, readDiagramInfo } from './buildModel'
import { setExtensionsDirect, writeExtensions } from './extensions'
import { forWriting } from './legalBasis'

export const DEFAULT_HEADER_COLOR = '#1976d2'
export const DEFAULT_HEADER_TEXT_COLOR = '#ffffff'

function isBlank(value: unknown): boolean {
  if (value === undefined || value === null) return true
  if (typeof value === 'string') return !value.trim()
  return Array.isArray(value) && value.length === 0
}

/** Drops empty values, sets the schema version, fills legal basis texts. */
export function cleanInfo(info: DiagramInfo): DiagramInfo {
  const entries = Object.entries(info)
    .filter(([, value]) => !isBlank(value))
    .map(([key, value]) => [key, typeof value === 'string' ? value.trim() : value])
  const result = Object.fromEntries(entries) as DiagramInfo
  result.schemaVersion = FLOWAUDIT_SCHEMA_VERSION
  if (result.legalBases) result.legalBases = result.legalBases.map(forWriting)
  return result
}

/** Headless: sets the diagram info at the main element. */
export function setDiagramInfo(definitions: ModdleElement, info: DiagramInfo, factory: ModdleFactory): boolean {
  const main = mainElement(definitions)
  if (!main) return false
  setExtensionsDirect(main, { diagramInfo: cleanInfo(info) }, factory)
  return true
}

/** Editor: writes the diagram info through `modeling` (one undo step). */
export function writeDiagramInfo(services: { canvas: Canvas; modeling: Modeling; moddle: ModdleFactory }, info: DiagramInfo): void {
  const root = services.canvas.getRootElement()
  if (root?.businessObject) writeExtensions(root, { diagramInfo: cleanInfo(info) }, services)
}

/** Editor: reads the diagram info (collaboration, otherwise first process). */
export function readDiagramInfoFromEditor(services: { canvas: Canvas }): DiagramInfo | null {
  const definitions = definitionsOf(services.canvas)
  return definitions ? readDiagramInfo(definitions) : null
}

export interface Header {
  title: string
  subtitle: string
  color: string
  textColor: string
}

export function headerOf(info: DiagramInfo | null | undefined, fallbackTitle = ''): Header {
  return {
    title: info?.title?.trim() || fallbackTitle,
    subtitle: info?.subtitle?.trim() || '',
    color: info?.headerColor || DEFAULT_HEADER_COLOR,
    textColor: info?.headerTextColor || DEFAULT_HEADER_TEXT_COLOR,
  }
}

/** Record of the audit_designer (`BpmnDiagram`), as far as needed for migration. */
export interface LegacyDiagram {
  name?: string | null
  description?: string | null
  process_owner?: string | null
  process_type?: string | null
  version?: number | string | null
  is_archived?: boolean | null
  header_title?: string | null
  header_subtitle?: string | null
  header_color?: string | null
  header_text_color?: string | null
}

const orUndefined = (value: string | null | undefined) => value || undefined

/**
 * Migrates the legacy columns into diagram info. Data present in the XML
 * wins – the XML is the authoritative source.
 */
export function infoFromLegacy(legacy: LegacyDiagram, present: DiagramInfo | null = null): DiagramInfo {
  const migrated: DiagramInfo = {
    title: orUndefined(legacy.header_title) ?? orUndefined(legacy.name),
    subtitle: orUndefined(legacy.header_subtitle),
    description: orUndefined(legacy.description),
    processOwner: orUndefined(legacy.process_owner),
    processType: orUndefined(legacy.process_type),
    version: legacy.version === null || legacy.version === undefined ? undefined : String(legacy.version),
    status: legacy.is_archived ? 'archiviert' : undefined,
    headerColor: orUndefined(legacy.header_color),
    headerTextColor: orUndefined(legacy.header_text_color),
  }
  const presentEntries = Object.entries(present ?? {}).filter(([, value]) => !isBlank(value))
  return cleanInfo({ ...migrated, ...Object.fromEntries(presentEntries) })
}

/** Diagram info back into the legacy columns (for applications in transition). */
export function legacyFromInfo(info: DiagramInfo): LegacyDiagram {
  return {
    header_title: info.title ?? null,
    header_subtitle: info.subtitle ?? null,
    header_color: info.headerColor ?? DEFAULT_HEADER_COLOR,
    header_text_color: info.headerTextColor ?? DEFAULT_HEADER_TEXT_COLOR,
    process_owner: info.processOwner ?? null,
    process_type: info.processType ?? null,
    description: info.description ?? null,
    is_archived: info.status === 'archiviert',
  }
}
