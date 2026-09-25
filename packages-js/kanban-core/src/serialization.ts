/** JSON-Dokument `auditcore_kanban.board/1` lesen und prüfen (wie serialization.py). */
import { KanbanError } from './errors'
import { isJson, isPlainObject } from './fields'
import { cloneJson, orderedCards, SCHEMA_VERSION, type Attachment, type Board, type Card, type CardLink, type ChecklistItem, type Column, type JsonObject, type Label, type Priority, type Share, type SharePermission, type TransitionPolicy } from './model'

class Reader {
  readonly raw: Readonly<Record<string, unknown>>

  constructor(raw: unknown, readonly path: string) {
    if (!isPlainObject(raw)) throw new KanbanError('INVALID_DOCUMENT', `${path}: Objekt erwartet`)
    this.raw = raw
  }

  private fail(key: string): KanbanError {
    return new KanbanError('INVALID_DOCUMENT', `${this.path}.${key}: ungültiger Wert`)
  }

  private get(key: string): unknown {
    return Object.prototype.hasOwnProperty.call(this.raw, key) ? this.raw[key] : undefined
  }

  text(key: string, fallback?: string): string {
    const value = this.get(key) ?? fallback
    if (typeof value !== 'string') throw this.fail(key)
    return value
  }

  optionalText(key: string): string | null {
    const value = this.get(key)
    return value === null || value === undefined ? null : this.text(key)
  }

  integer(key: string, fallback: number | null = null): number | null {
    const value = this.get(key) ?? fallback
    if (value === null) return null
    if (typeof value !== 'number' || !Number.isInteger(value)) throw this.fail(key)
    return value
  }

  flag(key: string, fallback = false): boolean {
    const value = this.get(key) ?? fallback
    if (typeof value !== 'boolean') throw this.fail(key)
    return value
  }

  texts(key: string): string[] {
    const value = this.get(key) ?? []
    if (!Array.isArray(value) || !value.every((item) => typeof item === 'string')) throw this.fail(key)
    return [...(value as string[])]
  }

  objects(key: string): Reader[] {
    const value = this.get(key) ?? []
    if (!Array.isArray(value)) throw this.fail(key)
    return value.map((item, index) => new Reader(item, `${this.path}.${key}[${index}]`))
  }

  extra(key = 'extra'): JsonObject {
    const value = this.get(key) ?? {}
    if (!isPlainObject(value) || !isJson(value)) throw this.fail(key)
    return cloneJson(value) as JsonObject
  }
}

function columnFrom(r: Reader): Column {
  return {
    id: r.text('id'),
    label: r.text('label'),
    color: r.text('color', '#7c3aed'),
    wip_limit: r.integer('wip_limit'),
    done: r.flag('done'),
    status_aliases: r.texts('status_aliases'),
  }
}

function checklistFrom(r: Reader): ChecklistItem[] {
  return r.objects('checklist').map((item) => ({ text: item.text('text'), done: item.flag('done') }))
}

function linksFrom(r: Reader): CardLink[] {
  return r.objects('links').map((item) => ({ kind: item.text('kind'), target: item.text('target'), title: item.text('title', '') }))
}

function attachmentsFrom(r: Reader): Attachment[] {
  return r.objects('attachments').map((item) => ({
    id: item.text('id'),
    filename: item.text('filename'),
    mime_type: item.text('mime_type', 'application/octet-stream'),
    size: item.integer('size', 0) ?? 0,
  }))
}

function cardFrom(r: Reader): Card {
  return {
    id: r.text('id'), column_id: r.text('column_id'), rank: r.text('rank'), title: r.text('title'),
    description: r.text('description', ''), priority: r.text('priority', 'mittel') as Priority,
    tags: r.texts('tags'), assignees: r.texts('assignees'), due: r.optionalText('due'),
    color: r.optionalText('color'), image: r.optionalText('image'), badge: r.optionalText('badge'),
    checklist: checklistFrom(r), links: linksFrom(r), attachments: attachmentsFrom(r),
    created_at: r.text('created_at', ''), updated_at: r.text('updated_at', ''), extra: r.extra(),
  }
}

function pairs(raw: unknown, path: string): [string, string][] {
  const valid = Array.isArray(raw) && raw.every((pair) => Array.isArray(pair) && pair.length === 2 && pair.every((x) => typeof x === 'string'))
  if (!valid) throw new KanbanError('INVALID_DOCUMENT', `${path}.allowed: ungültiger Wert`)
  return (raw as [string, string][]).map(([from, to]) => [from, to])
}

/** `mode` free ignoriert `allowed`; restricted erlaubt nur die genannten Paare. */
export function policyFromJson(raw: unknown, path = 'transitions'): TransitionPolicy {
  if (raw === null || raw === undefined) return { mode: 'free', allowed: [], locked_columns: [], fixed_order_columns: [] }
  const r = new Reader(raw, path)
  const mode = r.text('mode', 'free')
  if (mode !== 'free' && mode !== 'restricted') throw new KanbanError('INVALID_DOCUMENT', `${path}.mode: ungültiger Wert`)
  return {
    mode,
    allowed: mode === 'restricted' ? pairs(r.raw.allowed ?? [], path) : [],
    locked_columns: r.texts('locked_columns'),
    fixed_order_columns: r.texts('fixed_order_columns'),
  }
}

function wipMode(r: Reader): Board['wip_mode'] {
  const mode = r.text('wip_mode', 'block')
  if (mode !== 'block' && mode !== 'warn') throw new KanbanError('INVALID_DOCUMENT', 'board.wip_mode: ungültiger Wert')
  return mode
}

function sharesFrom(r: Reader): Share[] {
  return r.objects('shares').map((s) => ({
    user_id: s.text('user_id'),
    permission: s.text('permission', 'read') as SharePermission,
    shared_by: s.optionalText('shared_by'),
    created_at: s.optionalText('created_at'),
  }))
}

function labelsFrom(r: Reader): Label[] {
  return r.objects('labels').map((x) => ({ id: x.text('id'), name: x.text('name'), color: x.text('color', '#6b7280') }))
}

/** Liest und prüft ein Board-Dokument strukturell. */
export function boardFromJson(raw: unknown): Board {
  const r = new Reader(raw, 'board')
  const version = r.text('schema_version', SCHEMA_VERSION)
  if (version !== SCHEMA_VERSION) throw new KanbanError('INVALID_DOCUMENT', `Unbekannte Formatversion '${version}'`)
  const columns = r.objects('columns').map(columnFrom)
  if (columns.length === 0) throw new KanbanError('INVALID_DOCUMENT', 'board.columns: mindestens eine Spalte erforderlich')
  return {
    schema_version: SCHEMA_VERSION, id: r.text('id'), title: r.text('title'), owner_id: r.text('owner_id'),
    icon: r.text('icon', '📋'), pinned: r.flag('pinned'), archived: r.flag('archived'),
    version: r.integer('version', 0) ?? 0, created_at: r.text('created_at', ''), updated_at: r.text('updated_at', ''),
    columns, cards: r.objects('cards').map(cardFrom), labels: labelsFrom(r), shares: sharesFrom(r),
    transitions: policyFromJson(r.raw.transitions), wip_mode: wipMode(r), extra: r.extra(),
  }
}

/** Spaltenliste eines Anfragekörpers (Teilangaben erhalten Standardwerte). */
export function columnsFromJson(raw: unknown): Column[] {
  return new Reader({ columns: raw }, 'body').objects('columns').map(columnFrom)
}

/** Board-Dokument mit Karten in Board-Reihenfolge (stabile Ausgabe wie board_to_json). */
export function boardToJson(board: Board): Board {
  return { ...cloneJson(board), cards: orderedCards(board).map((card) => cloneJson(card)) }
}
