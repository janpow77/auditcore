/**
 * Mutable diagram collection with integrity checks on every change (same
 * operations as `Diagrammsammlung` of `auditcore_bpmn`). Each diagram lives
 * in exactly one folder (`folderId`; `null` = top level) and carries any
 * number of tags.
 */

import type { ProcessModel } from '../model/processModel'
import {
  COLLECTION_SCHEMA,
  KEY_KINDS,
  emptyExcerpt,
  isValidId,
  type CollectionData,
  type DiagramEntry,
  type Folder,
  type KeyKind,
  type Tag,
} from './collectionData'
import { excerptFromModel } from './excerpt'

const MESSAGES: Record<string, string> = {
  invalidId: 'Ungültige {what}-ID „{id}“ (erlaubt: Buchstaben, Ziffern, _ . -).',
  exists: '{what} „{id}“ existiert bereits.',
  unknownFolder: 'Ordner „{id}“ ist unbekannt.',
  unknownDiagram: 'Diagramm „{id}“ ist unbekannt.',
  unknownTags: 'Unbekannte Tags: {ids}',
  cycle: 'Ein Ordner kann nicht in sich selbst oder einen Unterordner verschoben werden.',
  notEmpty: 'Ordner „{id}“ ist nicht leer.',
  order: 'Die Reihenfolge muss genau die Diagramme des Ordners enthalten.',
  schema: 'Sammlungsschema {schema} wird nicht unterstützt.',
  unknownKind: 'Unbekannte Schlüsselart „{kind}“.',
  approvedImmutable: 'Version {version} von „{id}“ ist bereits freigegeben; Änderungen erfordern eine neue Version.',
  noApproval: 'Für „{id}“ gibt es keinen freigegebenen Stand.',
}

export class CollectionError extends Error {
  constructor(
    readonly code: string,
    readonly params: Record<string, string> = {},
  ) {
    super((MESSAGES[code] ?? code).replace(/\{(\w+)\}/g, (_m, key: string) => params[key] ?? ''))
  }
}

function byOrder<T extends { order: number; name: string; id: string }>(a: T, b: T): number {
  return a.order - b.order || a.name.localeCompare(b.name, 'de') || a.id.localeCompare(b.id)
}

export interface FolderNode {
  folder: Folder | null
  subfolders: FolderNode[]
  diagrams: DiagramEntry[]
}

export class DiagramCollection {
  id: string
  name: string
  readonly folders = new Map<string, Folder>()
  readonly tags = new Map<string, Tag>()
  readonly diagrams = new Map<string, DiagramEntry>()

  constructor(id = 'sammlung', name = 'Diagrammsammlung') {
    this.id = id
    this.name = name
  }

  // -- folders and tags -----------------------------------------------------
  private checkId(id: string, what: string): void {
    if (!isValidId(id)) throw new CollectionError('invalidId', { id, what })
  }

  private checkFolder(folderId: string | null | undefined): void {
    if (folderId && !this.folders.has(folderId)) throw new CollectionError('unknownFolder', { id: folderId })
  }

  createFolder(id: string, name: string, parentId: string | null = null, description?: string): Folder {
    this.checkId(id, 'Ordner')
    if (this.folders.has(id)) throw new CollectionError('exists', { id, what: 'Ordner' })
    this.checkFolder(parentId)
    const order = 1 + Math.max(-1, ...this.subfolders(parentId).map((f) => f.order))
    const folder: Folder = { id, name, parentId, order, ...(description ? { description } : {}) }
    this.folders.set(id, folder)
    return folder
  }

  renameFolder(id: string, name: string): void {
    this.folder(id).name = name
  }

  private folder(id: string): Folder {
    const folder = this.folders.get(id)
    if (!folder) throw new CollectionError('unknownFolder', { id })
    return folder
  }

  ancestors(folderId: string | null | undefined): string[] {
    const chain: string[] = []
    for (let current = folderId ?? null; current; current = this.folder(current).parentId ?? null) {
      if (chain.includes(current)) throw new CollectionError('cycle', { id: current })
      chain.push(current)
    }
    return chain
  }

  moveFolder(folderId: string, parentId: string | null, position?: number): void {
    const folder = this.folder(folderId)
    this.checkFolder(parentId)
    if (parentId && this.ancestors(parentId).includes(folderId)) throw new CollectionError('cycle')
    folder.parentId = parentId
    const siblings = this.subfolders(parentId).filter((f) => f.id !== folderId)
    siblings.splice(Math.max(0, Math.min(position ?? siblings.length, siblings.length)), 0, folder)
    siblings.forEach((item, index) => (item.order = index))
  }

  removeFolder(folderId: string): void {
    const hasChildren = this.subfolders(folderId).length > 0 || this.inFolder(folderId).length > 0
    if (hasChildren) throw new CollectionError('notEmpty', { id: folderId })
    this.folders.delete(folderId)
  }

  createTag(id: string, name: string, color?: string): Tag {
    this.checkId(id, 'Tag')
    const tag: Tag = { id, name, ...(color ? { color } : {}) }
    this.tags.set(id, tag)
    return tag
  }

  // -- diagrams ---------------------------------------------------------------
  addDiagram(id: string, options: { name?: string; folderId?: string | null; tags?: string[]; model?: ProcessModel } = {}): DiagramEntry {
    this.checkId(id, 'Diagramm')
    if (this.diagrams.has(id)) throw new CollectionError('exists', { id, what: 'Diagramm' })
    this.checkFolder(options.folderId)
    const tags = this.checkTags(options.tags ?? [])
    const order = 1 + Math.max(-1, ...this.inFolder(options.folderId ?? null).map((d) => d.order))
    const entry: DiagramEntry = { id, name: options.name ?? id, folderId: options.folderId ?? null, tags, order, excerpt: emptyExcerpt(), approvals: [] }
    this.diagrams.set(id, entry)
    if (options.model) this.update(id, options.model)
    return entry
  }

  private checkTags(tags: string[]): string[] {
    const unique = [...new Set(tags)]
    const unknown = unique.filter((tag) => !this.tags.has(tag))
    if (unknown.length) throw new CollectionError('unknownTags', { ids: unknown.join(', ') })
    return unique
  }

  entry(id: string): DiagramEntry {
    const entry = this.diagrams.get(id)
    if (!entry) throw new CollectionError('unknownDiagram', { id })
    return entry
  }

  /** Updates info and excerpt from the diagram model. */
  update(id: string, model: ProcessModel): DiagramEntry {
    const entry = this.entry(id)
    entry.info = model.info
    entry.excerpt = excerptFromModel(model)
    if (entry.name === entry.id && model.info?.title) entry.name = model.info.title
    return entry
  }

  rename(id: string, name: string): void {
    this.entry(id).name = name
  }

  remove(id: string): void {
    this.entry(id)
    this.diagrams.delete(id)
  }

  move(id: string, folderId: string | null, position?: number): void {
    const entry = this.entry(id)
    this.checkFolder(folderId)
    entry.folderId = folderId
    const siblings = this.inFolder(folderId).filter((d) => d.id !== id)
    siblings.splice(Math.max(0, Math.min(position ?? siblings.length, siblings.length)), 0, entry)
    siblings.forEach((item, index) => (item.order = index))
  }

  setOrder(folderId: string | null, ids: string[]): void {
    const current = new Set(this.inFolder(folderId).map((d) => d.id))
    if (ids.length !== current.size || !ids.every((id) => current.has(id))) throw new CollectionError('order')
    ids.forEach((id, index) => (this.entry(id).order = index))
  }

  setTags(id: string, tags: string[]): void {
    this.entry(id).tags = this.checkTags(tags)
  }

  // -- queries -----------------------------------------------------------------
  inFolder(folderId: string | null | undefined): DiagramEntry[] {
    return [...this.diagrams.values()].filter((d) => (d.folderId ?? null) === (folderId ?? null)).sort(byOrder)
  }

  subfolders(folderId: string | null | undefined): Folder[] {
    return [...this.folders.values()].filter((f) => (f.parentId ?? null) === (folderId ?? null)).sort(byOrder)
  }

  diagramsIn(folderId: string | null, recursive = true): DiagramEntry[] {
    const own = this.inFolder(folderId)
    return recursive ? [...own, ...this.subfolders(folderId).flatMap((f) => this.diagramsIn(f.id, true))] : own
  }

  withTag(tagId: string): DiagramEntry[] {
    return [...this.diagrams.values()].filter((d) => d.tags.includes(tagId))
  }

  tree(folderId: string | null = null): FolderNode {
    return {
      folder: folderId ? this.folder(folderId) : null,
      subfolders: this.subfolders(folderId).map((f) => this.tree(f.id)),
      diagrams: this.inFolder(folderId),
    }
  }

  /** Full-text search over name, title, subtitle, description and keywords. */
  search(term = '', options: { status?: string; tag?: string } = {}): DiagramEntry[] {
    const needle = term.trim().toLocaleLowerCase('de')
    return [...this.diagrams.values()]
      .filter((d) => !options.status || d.info?.status === options.status)
      .filter((d) => !options.tag || d.tags.includes(options.tag))
      .filter((d) => {
        const info = d.info
        const haystack = [d.name, info?.title, info?.subtitle, info?.description, ...(info?.keywords ?? [])].filter(Boolean).join(' ')
        return haystack.toLocaleLowerCase('de').includes(needle)
      })
      .sort((a, b) => a.name.localeCompare(b.name, 'de') || a.id.localeCompare(b.id))
  }

  /** `[diagramId, elementId]` of all elements carrying the domain key. */
  elementsForKey(kind: KeyKind, value: string): [string, string][] {
    if (!(KEY_KINDS as readonly string[]).includes(kind)) throw new CollectionError('unknownKind', { kind })
    const wanted = value.trim()
    return [...this.diagrams.values()]
      .sort((a, b) => a.id.localeCompare(b.id))
      .flatMap((d) => (d.excerpt.keys[kind]?.[wanted] ?? []).map((elementId): [string, string] => [d.id, elementId]))
  }

  // -- (de)serialisation --------------------------------------------------------
  toData(): CollectionData {
    const sorted = <T extends { id: string }>(values: Iterable<T>) => [...values].sort((a, b) => a.id.localeCompare(b.id))
    return {
      schema: COLLECTION_SCHEMA,
      id: this.id,
      name: this.name,
      folders: sorted(this.folders.values()).map((f) => ({ ...f })),
      tags: sorted(this.tags.values()).map((t) => ({ ...t })),
      diagrams: sorted(this.diagrams.values()).map((d) => structuredClone(d)),
    }
  }

  static fromData(data: CollectionData): DiagramCollection {
    if (data.schema !== COLLECTION_SCHEMA) throw new CollectionError('schema', { schema: String(data.schema) })
    const collection = new DiagramCollection(data.id, data.name)
    for (const folder of data.folders) collection.folders.set(folder.id, { ...folder })
    for (const tag of data.tags) collection.tags.set(tag.id, { ...tag })
    for (const entry of data.diagrams) collection.diagrams.set(entry.id, { ...structuredClone(entry), excerpt: { ...emptyExcerpt(), ...entry.excerpt } })
    for (const id of collection.folders.keys()) collection.ancestors(id)
    return collection
  }
}
