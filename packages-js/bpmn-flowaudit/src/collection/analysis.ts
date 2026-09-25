/**
 * Collection analysis: group overview, references across diagrams,
 * collection rules (`BPMN-K…`) and approvals with SHA-256.
 */

import { DIAGRAM_STATUS } from '../schema/vocabulary'
import { issue, type ValidationIssue } from '../validation/issue'
import { CollectionError, type DiagramCollection } from './collection'
import type { Approval, DiagramEntry } from './collectionData'

export interface GroupOverview {
  count: number
  statusDistribution: Record<string, number>
  tasks: number
  tasksWithLegalBasis: number
  /** Share of activities with legal basis (`null` without activities). */
  legalBasisCoverage: number | null
  expired: string[]
  /** KA number → diagram ids covering it. */
  keyRequirementCoverage: Record<number, string[]>
  diagrams: string[]
}

function statusKey(entry: DiagramEntry): string {
  const status = entry.info?.status
  if (!status) return 'ohne_status'
  return status in DIAGRAM_STATUS ? status : 'unbekannt'
}

function coverage(entries: DiagramEntry[]): Record<number, string[]> {
  const result: Record<number, string[]> = {}
  for (const entry of entries) {
    for (const ka of Object.keys(entry.excerpt.keys.ka ?? {})) {
      const number = Number(ka)
      if (!Number.isInteger(number)) continue
      result[number] ??= []
      if (!result[number].includes(entry.id)) result[number].push(entry.id)
    }
  }
  return result
}

/** Overview of a group (folder, recursive) or a tag. */
export function groupOverview(
  collection: DiagramCollection,
  options: { folderId?: string | null; tagId?: string; recursive?: boolean; referenceDate?: string } = {},
): GroupOverview {
  const entries = options.tagId ? collection.withTag(options.tagId) : collection.diagramsIn(options.folderId ?? null, options.recursive ?? true)
  const day = options.referenceDate ?? new Date().toISOString().slice(0, 10)
  const statusDistribution: Record<string, number> = {}
  for (const entry of entries) statusDistribution[statusKey(entry)] = (statusDistribution[statusKey(entry)] ?? 0) + 1
  const tasks = entries.reduce((sum, e) => sum + e.excerpt.tasks, 0)
  const tasksWithLegalBasis = entries.reduce((sum, e) => sum + e.excerpt.tasksWithLegalBasis, 0)
  return {
    count: entries.length,
    statusDistribution,
    tasks,
    tasksWithLegalBasis,
    legalBasisCoverage: tasks ? Math.round((tasksWithLegalBasis / tasks) * 10000) / 10000 : null,
    expired: entries.filter((e) => e.info?.validUntil && /^\d{4}-\d{2}-\d{2}$/.test(e.info.validUntil) && e.info.validUntil < day).map((e) => e.id),
    keyRequirementCoverage: coverage(entries),
    diagrams: entries.map((e) => e.id),
  }
}

export interface DiagramReference {
  sourceDiagram: string
  sourceElement: string
  kind: 'aufruf' | 'link'
  key: string
  targetDiagram: string | null
  targetElement?: string | null
}

/** Calls (call activity → process) and link events across diagram boundaries. */
export function diagramReferences(collection: DiagramCollection): DiagramReference[] {
  const byProcess = new Map<string, string[]>()
  const catches = new Map<string, [string, string][]>()
  for (const entry of collection.diagrams.values()) {
    for (const processId of entry.excerpt.processIds) byProcess.set(processId, [...(byProcess.get(processId) ?? []), entry.id])
    for (const [elementId, name] of entry.excerpt.linkCatches) catches.set(name, [...(catches.get(name) ?? []), [entry.id, elementId]])
  }
  const result: DiagramReference[] = []
  for (const entry of [...collection.diagrams.values()].sort((a, b) => a.id.localeCompare(b.id))) {
    for (const [elementId, called] of entry.excerpt.calls) {
      const targets = byProcess.get(called) ?? (collection.diagrams.has(called) ? [called] : [])
      result.push({ sourceDiagram: entry.id, sourceElement: elementId, kind: 'aufruf', key: called, targetDiagram: targets[0] ?? null })
    }
    const own = new Set(entry.excerpt.linkCatches.map(([, name]) => name))
    for (const [elementId, name] of entry.excerpt.linkThrows) {
      if (own.has(name)) continue
      const target = (catches.get(name) ?? []).find(([diagramId]) => diagramId !== entry.id)
      result.push({ sourceDiagram: entry.id, sourceElement: elementId, kind: 'link', key: name, targetDiagram: target?.[0] ?? null, targetElement: target?.[1] ?? null })
    }
  }
  return result
}

function structureIssues(collection: DiagramCollection): ValidationIssue[] {
  const found: ValidationIssue[] = []
  for (const folder of collection.folders.values()) {
    try {
      collection.ancestors(folder.id)
    } catch {
      found.push(issue('BPMN-K004', null, { ordner: folder.id }))
    }
  }
  for (const entry of collection.diagrams.values()) {
    if (entry.folderId && !collection.folders.has(entry.folderId)) found.push(issue('BPMN-K004', null, { ordner: entry.folderId }))
    for (const tag of entry.tags.filter((t) => !collection.tags.has(t))) found.push(issue('BPMN-K005', null, { diagramm: entry.id, tag }))
    const info = entry.info
    if (info?.variant === 'ist' && info.referenceDiagram && !collection.diagrams.has(info.referenceDiagram)) {
      found.push(issue('BPMN-K007', null, { diagramm: entry.id, bezug: info.referenceDiagram }))
    }
  }
  return found
}

function processOwnerIssues(collection: DiagramCollection): ValidationIssue[] {
  const owners = new Map<string, string[]>()
  for (const entry of collection.diagrams.values()) for (const id of entry.excerpt.processIds) owners.set(id, [...(owners.get(id) ?? []), entry.id])
  return [...owners.entries()]
    .filter(([, ids]) => ids.length > 1)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([prozess, ids]) => issue('BPMN-K003', null, { prozess, diagramme: ids.join(', ') }))
}

function referenceIssues(collection: DiagramCollection): ValidationIssue[] {
  return diagramReferences(collection)
    .filter((ref) => !ref.targetDiagram)
    .map((ref) => {
      const diagramm = collection.diagrams.get(ref.sourceDiagram)?.name ?? ref.sourceDiagram
      const params = ref.kind === 'aufruf' ? { name: ref.sourceElement, diagramm, ziel: ref.key } : { link: ref.key, diagramm }
      return { ...issue(ref.kind === 'aufruf' ? 'BPMN-K001' : 'BPMN-K002', ref.sourceElement, params), diagramId: ref.sourceDiagram }
    })
}

/** Collection rules (`BPMN-K001`–`K007`). */
export function checkCollection(collection: DiagramCollection): ValidationIssue[] {
  return [...structureIssues(collection), ...processOwnerIssues(collection), ...referenceIssues(collection)]
}

/** `[actualId, targetId]` of all linked actual-state diagrams. */
export function targetActualPairs(collection: DiagramCollection): [string, string][] {
  return [...collection.diagrams.values()]
    .filter((e) => e.info?.variant === 'ist' && e.info.referenceDiagram)
    .map((e): [string, string] => [e.id, e.info?.referenceDiagram as string])
    .sort()
}

// ---------------------------------------------------------------------------
// Approvals
// ---------------------------------------------------------------------------

/** SHA-256 over the UTF-8 bytes of the XML exactly as stored (hex). */
export async function sha256Xml(xml: string): Promise<string> {
  const digest = await globalThis.crypto.subtle.digest('SHA-256', new TextEncoder().encode(xml))
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, '0')).join('')
}

/** Records the SHA-256 of an approved version; a version is immutable. */
export async function approve(
  collection: DiagramCollection,
  diagramId: string,
  xml: string,
  version: string,
  meta: Omit<Approval, 'version' | 'sha256'> = {},
): Promise<Approval> {
  const entry = collection.entry(diagramId)
  const sha256 = await sha256Xml(xml)
  const existing = entry.approvals.find((approval) => approval.version === version)
  if (existing && existing.sha256 !== sha256) {
    throw new CollectionError('approvedImmutable', { id: diagramId, version })
  }
  if (existing) return existing
  const approval: Approval = { version, sha256, ...meta }
  entry.approvals.push(approval)
  return approval
}

/** `null` if the XML equals the approved version, otherwise `BPMN-K008`. */
export async function verifyApproval(collection: DiagramCollection, diagramId: string, xml: string, version?: string): Promise<ValidationIssue | null> {
  const entry = collection.entry(diagramId)
  const candidates = entry.approvals.filter((approval) => !version || approval.version === version)
  const approval = candidates[candidates.length - 1]
  if (!approval) throw new CollectionError('noApproval', { id: diagramId })
  if (approval.sha256 === (await sha256Xml(xml))) return null
  return { ...issue('BPMN-K008', null, { version: approval.version, diagramm: entry.name }), diagramId }
}
