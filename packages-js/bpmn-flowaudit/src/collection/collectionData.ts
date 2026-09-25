/**
 * Data model of the diagram collection (same structure as the collection of
 * `auditcore_bpmn`): nested folders, tags, order, an excerpt from each
 * diagram's XML and immutable approvals. No database in the library;
 * persistence goes through the storage port.
 */

import type { DiagramInfo } from '../schema/types'

export const COLLECTION_SCHEMA = 'auditcore_bpmn.diagrammsammlung/1'

/** Kinds of stable domain keys (checklists and notes link only via these). */
export const KEY_KINDS = ['ka', 'bk', 'prueffeld', 'feststellung_ref', 'register', 'rolle', 'kennzeichen'] as const
export type KeyKind = (typeof KEY_KINDS)[number]

export interface Folder {
  id: string
  name: string
  parentId?: string | null
  order: number
  description?: string
}

export interface Tag {
  id: string
  name: string
  color?: string
}

/** Immutable approved version (new version instead of change). */
export interface Approval {
  version: string
  sha256: string
  cutoffDate?: string
  approvedOn?: string
  approvedBy?: string
}

/** Data derived from the XML (never maintained by hand). */
export interface DiagramExcerpt {
  processIds: string[]
  /** `[elementId, calledElement]` of call activities. */
  calls: [string, string][]
  linkThrows: [string, string][]
  linkCatches: [string, string][]
  tasks: number
  tasksWithLegalBasis: number
  /** Kind → value → element ids. */
  keys: Partial<Record<KeyKind, Record<string, string[]>>>
}

export interface DiagramEntry {
  id: string
  name: string
  folderId?: string | null
  tags: string[]
  order: number
  info?: DiagramInfo | null
  excerpt: DiagramExcerpt
  approvals: Approval[]
  /** Last change (ISO), maintained by the application. */
  updatedAt?: string
}

export interface CollectionData {
  schema: string
  id: string
  name: string
  folders: Folder[]
  tags: Tag[]
  diagrams: DiagramEntry[]
}

export function emptyExcerpt(): DiagramExcerpt {
  return { processIds: [], calls: [], linkThrows: [], linkCatches: [], tasks: 0, tasksWithLegalBasis: 0, keys: {} }
}

export function emptyCollection(id = 'sammlung', name = 'Diagrammsammlung'): CollectionData {
  return { schema: COLLECTION_SCHEMA, id, name, folders: [], tags: [], diagrams: [] }
}

const ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$/

export function isValidId(value: string): boolean {
  return ID_PATTERN.test(value)
}

/** Creates a readable, valid id from a name („Antragsverfahren 2“ → `antragsverfahren-2`). */
export function idFromName(name: string, taken: Set<string>): string {
  const base =
    name
      .toLowerCase()
      .replace(/ä/g, 'ae')
      .replace(/ö/g, 'oe')
      .replace(/ü/g, 'ue')
      .replace(/ß/g, 'ss')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .slice(0, 60) || 'diagramm'
  let candidate = base
  for (let n = 2; taken.has(candidate); n += 1) candidate = `${base}-${n}`
  return candidate
}
