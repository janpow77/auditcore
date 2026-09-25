/**
 * Tiefe Kopie von moddle-Elementen – auch über moddle-Instanzen hinweg
 * (Kopieren/Einfügen zwischen Diagrammen) und einschließlich unbekannter
 * Erweiterungen (`$attrs`, generische Elemente wie `flowaudit:*` ohne
 * Beschreibung).
 */

import type { Moddle, ModdleElement, ModdlePropertyDescriptor } from '../types'

export interface CopyOptions {
  /** Eigenschaften, die nicht kopiert werden (auf oberster Ebene). */
  exclude?: string[]
  /** Umsetzung von Referenzen; `undefined` = Referenz entfällt. */
  mapReference?: (value: ModdleElement, property: string) => ModdleElement | undefined
  /** Wird für jedes neu erzeugte Element aufgerufen (z. B. neue ID). */
  onCreate?: (copy: ModdleElement, original: ModdleElement) => void
}

const ALWAYS_SKIP = new Set(['id', 'incoming', 'outgoing', 'lanes', 'di'])

function isModdleElement(value: unknown): value is ModdleElement {
  return !!value && typeof value === 'object' && typeof (value as ModdleElement).$type === 'string'
}

function hasValue(element: ModdleElement, name: string): boolean {
  if (!Object.prototype.hasOwnProperty.call(element, name)) return false
  const value: unknown = element[name as keyof ModdleElement]
  if (value === undefined) return false
  return !Array.isArray(value) || value.length > 0
}

function createInstance(moddle: Moddle, element: ModdleElement): ModdleElement {
  const uri = element.$descriptor?.ns?.uri
  if (element.$descriptor?.isGeneric) return moddle.createAny(element.$type, uri, {})
  try {
    return moddle.create(element.$type)
  } catch {
    // Typ im Ziel-Modell unbekannt: als generisches Element übernehmen.
    return moddle.createAny(element.$type, uri, {})
  }
}

function copyGeneric(moddle: Moddle, source: ModdleElement, target: ModdleElement, options: CopyOptions): void {
  const record = target as unknown as Record<string, unknown>
  for (const key of Object.keys(source)) {
    if (key === '$type') continue
    record[key] = cloneValue(moddle, (source as unknown as Record<string, unknown>)[key], options, target)
  }
}

/** Liefert eine vollständige Kopie eines moddle-Elements im Ziel-Modell. */
export function cloneModdleElement(moddle: Moddle, element: ModdleElement, options: CopyOptions = {}, parent?: ModdleElement): ModdleElement {
  const copy = createInstance(moddle, element)
  if (copy.$descriptor?.isGeneric) copyGeneric(moddle, element, copy, options)
  else copyProperties(moddle, element, copy, options)
  if (parent) copy.$parent = parent
  options.onCreate?.(copy, element)
  return copy
}

function copyReference(source: ModdleElement, target: ModdleElement, property: ModdlePropertyDescriptor, options: CopyOptions): void {
  const value: unknown = source.get(property.name)
  const mapped = mapReference(value, property.name, options)
  if (mapped === undefined || (Array.isArray(mapped) && mapped.length === 0)) return
  target.set(property.name, mapped)
}

function isCopyable(property: ModdlePropertyDescriptor, source: ModdleElement, target: ModdleElement, options: CopyOptions): boolean {
  if (property.isVirtual || ALWAYS_SKIP.has(property.name)) return false
  if (options.exclude?.includes(property.name)) return false
  if (!hasValue(source, property.name)) return false
  const targetDescriptor = target.$descriptor
  return !targetDescriptor || !!targetDescriptor.isGeneric || !!targetDescriptor.propertiesByName?.[property.name]
}

/** Enthaltene Werte (auch Listen) werden tief kopiert. */
function copyContainment(moddle: Moddle, source: ModdleElement, target: ModdleElement, name: string, options: CopyOptions): void {
  const value: unknown = source.get(name)
  if (!Array.isArray(value)) {
    target.set(name, cloneValue(moddle, value, options, target))
    return
  }
  const list = target.get<unknown[]>(name)
  for (const item of value) list.push(cloneValue(moddle, item, options, target))
}

/** Kopiert Eigenschaften von `source` nach `target` (beide moddle-Elemente). */
export function copyProperties(moddle: Moddle, source: ModdleElement, target: ModdleElement, options: CopyOptions = {}): void {
  const nested: CopyOptions = { mapReference: options.mapReference, onCreate: options.onCreate }
  for (const property of source.$descriptor?.properties || []) {
    if (!isCopyable(property, source, target, options)) continue
    if (property.isReference) copyReference(source, target, property, options)
    else copyContainment(moddle, source, target, property.name, nested)
  }
  // Unbekannte Attribute (z. B. flowaudit:…, ältere Kurzattribute) übernehmen.
  for (const [key, value] of Object.entries(source.$attrs || {})) {
    if (!options.exclude?.includes(key)) target.$attrs[key] = value
  }
}

function mapReference(value: unknown, name: string, options: CopyOptions): unknown {
  const map = options.mapReference
  if (!map) return value
  if (Array.isArray(value)) {
    return value.filter(isModdleElement).map((item) => map(item, name)).filter((item) => item !== undefined)
  }
  return isModdleElement(value) ? map(value, name) : value
}

function cloneValue(moddle: Moddle, value: unknown, options: CopyOptions, parent: ModdleElement): unknown {
  if (Array.isArray(value)) return value.map((item) => cloneValue(moddle, item, options, parent))
  if (isModdleElement(value)) return cloneModdleElement(moddle, value, options, parent)
  if (value && typeof value === 'object') return JSON.parse(JSON.stringify(value))
  return value
}
