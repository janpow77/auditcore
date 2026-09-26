/**
 * Logic of the editor dialogs: enrichment groups and texts, element search,
 * export choice defaults and formats, diagram info (funds, lists), ESI
 * status table and loading.
 */

import { citation, DEFAULT_EXPORT_CHOICE, displayName, normalizeEsiResponse, shortCitation, type DiagramInfo, type EsiPort, type EsiRequirementResult, type EsiStatus, type ExportChoice, type ExportData, type ExportFormat, type LegalBasis, type ProcessModel, type Suggestion } from '../index'
import type { DescribedListKey } from './descriptors'

export function groupSuggestions(suggestions: Suggestion[]): [string, Suggestion[]][] {
  const map = new Map<string, Suggestion[]>()
  for (const item of suggestions) map.set(item.elementId, [...(map.get(item.elementId) ?? []), item])
  return [...map.entries()]
}

export function describeSuggestion(item: Suggestion): string {
  const value = item.value
  if (typeof value === 'string') return value
  if (item.kind === 'legalBasis') return `${shortCitation(value as LegalBasis)} – ${citation(value as LegalBasis)}`
  return Object.values(value).filter(Boolean).join(' · ')
}

export function toggleInSet<T>(set: ReadonlySet<T>, value: T): Set<T> {
  const next = new Set(set)
  if (next.has(value)) next.delete(value)
  else next.add(value)
  return next
}

type Element = ProcessModel['elements'][number]

function haystack(element: Element): string {
  const ext = element.extensions
  return [
    element.id,
    element.name,
    element.actor?.role,
    element.actor?.displayName,
    ...ext.auditReferences.flatMap((r) => [`KA ${r.keyRequirement}`, `BK ${r.assessmentCriterion}`]),
    ...ext.crossReferences.map((r) => r.key),
    ...ext.findings.map((f) => f.reference),
  ]
    .filter(Boolean)
    .join(' ')
    .toLocaleLowerCase('de')
}

/** Elements matching name, id, role or domain key (no flows, at most 50). */
export function searchElements(model: ProcessModel | null, query: string): Element[] {
  const needle = query.trim().toLocaleLowerCase('de')
  if (!model || !needle) return []
  return model.elements.filter((element) => !element.type.endsWith('Flow') && haystack(element).includes(needle)).slice(0, 50)
}

export const elementNames = (model: ProcessModel | null): Record<string, string> => Object.fromEntries((model?.elements ?? []).map((element) => [element.id, displayName(element)]))

export const IMAGE_FORMATS: ExportFormat[] = ['svg', 'png', 'pdf']
export const DATA_FORMATS: ExportFormat[] = ['bpmn', 'myst', 'prozesstabelle-csv', 'prozesstabelle-myst', 'rcm-csv', 'feststellungen-csv']
export const EXPORT_FORMATS: ExportFormat[] = [...IMAGE_FORMATS, ...DATA_FORMATS]
export const FORMAT_ICONS: Record<string, string> = { svg: 'diagram', png: 'diagram', pdf: 'marker-dokument', bpmn: 'xml', myst: 'marker-dokument', excel: 'analysis' }
export const ORIENTATIONS = ['auto', 'hoch', 'quer'] as const

/** Export options preselected from the data (legends only if there is something to show). */
export function initialExportChoice(defaultTitle: string, subtitle: string | undefined, data: ExportData, confidentiality?: string): Omit<ExportChoice, 'format'> {
  return {
    ...DEFAULT_EXPORT_CHOICE,
    title: defaultTitle,
    subtitle: subtitle ?? '',
    showLegend: data.colors.length > 0,
    showMarkerLegend: data.markers.length > 0,
    showLegalBases: data.legalBases.length > 0,
    neutral: confidentiality === 'vs_nfd',
  }
}

export const EMPTY_EXPORT_DATA: ExportData = { colors: [], markers: [], legalBases: [] }

export const DIAGRAM_LISTS: DescribedListKey[] = ['auditReferences', 'risks', 'findings', 'sources', 'crossReferences']

export const cloneInfo = (info: DiagramInfo | null): DiagramInfo => JSON.parse(JSON.stringify(info ?? {})) as DiagramInfo

export function toggleFund(info: DiagramInfo, code: string): DiagramInfo {
  return { ...info, funds: [...toggleInSet(new Set(info.funds ?? []), code)] }
}

export const infoList = (info: DiagramInfo, key: string): Record<string, unknown>[] => ((info as Record<string, unknown>)[key] as Record<string, unknown>[] | undefined) ?? []

export const ESI_STATUS: Record<EsiStatus, { icon: string; label: string; badge: string }> = {
  fulfilled: { icon: 'check', label: 'esi.fulfilled', badge: 'fa-badge--success' },
  unclear: { icon: 'hint', label: 'esi.unclear', badge: 'fa-badge--warning' },
  missing: { icon: 'close', label: 'esi.missing', badge: 'fa-badge--danger' },
}

export async function loadEsi(port: EsiPort, xml: () => Promise<string>, diagramId?: string): Promise<EsiRequirementResult[]> {
  return normalizeEsiResponse(await port.requirements(await xml(), diagramId))
}
