/** JSON-Felder einer Karte prüfen und in Werte übersetzen (deklarative Feldtabelle wie card_fields.py). */
import { KanbanError } from './errors'
import { cloneJson, type Attachment, type Card, type CardLink, type ChecklistItem, type JsonObject, type JsonValue } from './model'
import { normalizeDue, validateBadge, validateDescription, validatePriority, validateTags, validateTitle, type Limits } from './validation'

export type CardFieldName =
  | 'title'
  | 'description'
  | 'priority'
  | 'tags'
  | 'assignees'
  | 'due'
  | 'color'
  | 'image'
  | 'badge'
  | 'checklist'
  | 'links'
  | 'attachments'
  | 'extra'

/** Geprüfte Teiländerung einer Karte. */
export type CardPatch = Partial<Pick<Card, CardFieldName>>

type FieldTable = { readonly [K in CardFieldName]: (name: string, value: unknown, limits: Limits) => Card[K] }

export function invalidField(name: string): KanbanError {
  return new KanbanError('INVALID_REQUEST', `Feld '${name}' hat einen ungültigen Typ`)
}

export function asString(name: string, value: unknown): string {
  if (typeof value !== 'string') throw invalidField(name)
  return value
}

export function asOptionalString(name: string, value: unknown): string | null {
  return value === null || value === undefined ? null : asString(name, value)
}

function asBool(name: string, value: unknown): boolean {
  if (typeof value !== 'boolean') throw invalidField(name)
  return value
}

function asStrings(name: string, value: unknown): string[] {
  if (!Array.isArray(value)) throw invalidField(name)
  return value.map((item) => asString(name, item))
}

function asObjects(name: string, value: unknown): Record<string, unknown>[] {
  if (!Array.isArray(value) || !value.every(isPlainObject)) throw invalidField(name)
  return value
}

export function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

export function isJson(value: unknown): value is JsonValue {
  if (value === null || ['string', 'boolean'].includes(typeof value)) return true
  if (typeof value === 'number') return Number.isFinite(value)
  if (Array.isArray(value)) return value.every(isJson)
  return isPlainObject(value) && Object.values(value).every(isJson)
}

function asJsonObject(name: string, value: unknown): JsonObject {
  if (!isPlainObject(value) || !isJson(value)) throw invalidField(name)
  return cloneJson(value) as JsonObject
}

function checklist(name: string, value: unknown, limits: Limits): ChecklistItem[] {
  const items = asObjects(name, value)
  if (items.length > limits.checklist_max) throw new KanbanError('VALIDATION_ERROR', 'Zu viele Checklisten-Einträge')
  return items.map((item) => ({ text: asString(name, item.text), done: asBool(name, item.done ?? false) }))
}

function links(name: string, value: unknown): CardLink[] {
  return asObjects(name, value).map((item) => ({
    kind: asString(name, item.kind),
    target: asString(name, item.target),
    title: asString(name, item.title ?? ''),
  }))
}

function size(name: string, value: unknown): number {
  if (typeof value !== 'number' || !Number.isInteger(value) || value < 0) throw invalidField(name)
  return value
}

function attachments(name: string, value: unknown): Attachment[] {
  return asObjects(name, value).map((item) => ({
    id: asString(name, item.id),
    filename: asString(name, item.filename),
    mime_type: asString(name, item.mime_type ?? 'application/octet-stream'),
    size: size(name, item.size ?? 0),
  }))
}

/** Text, bei dem auch "" löscht (Original card_color / card_image). */
function cleared(name: string, value: unknown): string | null {
  return asOptionalString(name, value) || null
}

/** Feldtabelle: JSON-Name → Prüfer. `column_id` behandelt die Verschiebelogik. */
export const CARD_FIELDS: FieldTable = {
  title: (n, v, lim) => validateTitle(asString(n, v), lim),
  description: (n, v, lim) => validateDescription(asString(n, v), lim),
  priority: (n, v) => validatePriority(asString(n, v)),
  tags: (n, v, lim) => validateTags(asStrings(n, v), lim),
  assignees: (n, v) => asStrings(n, v),
  due: (n, v) => normalizeDue(asOptionalString(n, v)),
  color: cleared,
  image: cleared,
  badge: (n, v, lim) => validateBadge(asOptionalString(n, v), lim),
  checklist,
  links: (n, v) => links(n, v),
  attachments: (n, v) => attachments(n, v),
  extra: (n, v) => asJsonObject(n, v),
}

/** Geprüfte Werte der bekannten Felder, die in `fields` vorkommen. */
export const CARD_FIELD_NAMES = Object.keys(CARD_FIELDS) as CardFieldName[]

function parseField<K extends CardFieldName>(patch: CardPatch, name: K, value: unknown, limits: Limits): void {
  patch[name] = CARD_FIELDS[name](name, value, limits)
}

export function parseCardFields(fields: Readonly<Record<string, unknown>>, limits: Limits): CardPatch {
  const patch: CardPatch = {}
  for (const name of CARD_FIELD_NAMES) {
    if (Object.prototype.hasOwnProperty.call(fields, name)) parseField(patch, name, fields[name], limits)
  }
  return patch
}
