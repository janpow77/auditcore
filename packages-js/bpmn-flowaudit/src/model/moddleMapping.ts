/**
 * Conversion between moddle elements of the flowaudit namespace and the
 * TypeScript objects of `schema/types.ts`, driven by `schema/spec.ts`.
 */

import type { ModdleElement, ModdleFactory } from '../diagram/services'
import { TEXT_TYPES, TYPES, typeByModdleName, type FieldKind, type FieldSpec, type TypeSpec } from '../schema/spec'

const PREFIX = 'flowaudit:'

type Plain = Record<string, unknown>

function clean(value: unknown): string | undefined {
  if (typeof value !== 'string') return undefined
  const trimmed = value.trim()
  return trimmed ? trimmed : undefined
}

function toBool(value: unknown): boolean | undefined {
  if (typeof value === 'boolean') return value
  const text = clean(value)?.toLowerCase()
  if (text === 'true' || text === '1' || text === 'ja') return true
  if (text === 'false' || text === '0' || text === 'nein') return false
  return undefined
}

function childValues(element: ModdleElement, name: string): ModdleElement[] {
  return (element.get(name) as ModdleElement[] | undefined) ?? []
}

const READERS: Record<FieldKind, (element: ModdleElement, field: FieldSpec) => unknown> = {
  attr: (element, field) => (field.type === 'bool' ? toBool(element.get(field.xml)) : clean(element.get(field.xml))),
  list: (element, field) => clean(element.get(field.xml))?.split(/\s+/),
  // 1.0 alternative: attribute `value` instead of text content.
  body: (element) => clean(element.get('value')) ?? clean(element.$attrs?.value),
  text: (element, field) => clean((element.get(field.xml) as ModdleElement | undefined)?.get('value')),
  texts: (element, field) => {
    const values = childValues(element, field.key)
      .map((child) => clean(child.get('value')))
      .filter((value): value is string => Boolean(value))
    return values.length ? values : undefined
  },
  elements: (element, field) => {
    const values = childValues(element, field.key).map((child) => fromModdle(child, TYPES[field.type as string]))
    return values.length ? values : undefined
  },
}

/** moddle element → TypeScript object (empty values are dropped). */
export function fromModdle<T = Plain>(element: ModdleElement, spec?: TypeSpec): T {
  const type = spec ?? typeByModdleName(element.$type)
  const result: Plain = {}
  for (const field of type?.fields ?? []) {
    const value = READERS[field.kind](element, field)
    if (value !== undefined) result[field.key] = value
  }
  return result as T
}

function isEmpty(value: unknown): boolean {
  return value === undefined || value === null || value === '' || (Array.isArray(value) && value.length === 0)
}

interface Built {
  attrs: Plain
  children: [string, ModdleElement | ModdleElement[]][]
}

type Writer = (factory: ModdleFactory, field: FieldSpec, value: unknown, built: Built) => void

function textChild(factory: ModdleFactory, xml: string, value: string): ModdleElement {
  return factory.create(PREFIX + TEXT_TYPES[xml], { value })
}

const WRITERS: Record<FieldKind, Writer> = {
  attr: (_factory, field, value, built) => {
    built.attrs[field.xml] = typeof value === 'boolean' ? String(value) : String(value).trim()
  },
  list: (_factory, field, value, built) => {
    built.attrs[field.xml] = (value as string[]).join(' ')
  },
  body: (_factory, _field, value, built) => {
    built.attrs.value = String(value)
  },
  text: (factory, field, value, built) => {
    built.children.push([field.xml, textChild(factory, field.xml, String(value))])
  },
  texts: (factory, field, value, built) => {
    const items = (value as string[]).map((item) => String(item).trim()).filter(Boolean)
    built.children.push([field.key, items.map((item) => textChild(factory, field.xml, item))])
  },
  elements: (factory, field, value, built) => {
    built.children.push([field.key, (value as object[]).map((item) => toModdle(factory, field.type as string, item))])
  },
}

/** TypeScript object → new moddle element (empty values are dropped). */
export function toModdle(factory: ModdleFactory, xmlName: string, data: object): ModdleElement {
  const spec = TYPES[xmlName]
  if (!spec) throw new Error(`Unknown FlowAudit type: ${xmlName}`)
  const source = data as Plain
  const built: Built = { attrs: {}, children: [] }
  for (const field of spec.fields) {
    const value = source[field.key]
    if (!isEmpty(value)) WRITERS[field.kind](factory, field, value, built)
  }
  const element = factory.create(PREFIX + spec.moddle, built.attrs)
  for (const [name, value] of built.children) {
    for (const child of Array.isArray(value) ? value : [value]) child.$parent = element
    element.set(name, value)
  }
  return element
}

export function isFlowauditElement(value: ModdleElement | undefined | null): boolean {
  return Boolean(value && typeof value.$type === 'string' && value.$type.startsWith(PREFIX))
}

/** Local XML name of a flowaudit moddle element, e.g. `kennzeichen`. */
export function localXmlName(value: ModdleElement): string {
  return typeByModdleName(value.$type)?.xml ?? value.$type.slice(PREFIX.length)
}
