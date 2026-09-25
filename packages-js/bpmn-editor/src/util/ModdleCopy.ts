/**
 * Tiefe Kopie von moddle-Elementen – auch über moddle-Instanzen hinweg
 * (Kopieren/Einfügen zwischen Diagrammen) und einschließlich unbekannter
 * Erweiterungen (`$attrs`, generische Elemente wie `flowaudit:*` ohne
 * Beschreibung).
 */

/* eslint-disable @typescript-eslint/no-explicit-any */

export interface CopyOptions {
  /** Eigenschaften, die nicht kopiert werden (auf oberster Ebene). */
  exclude?: string[]
  /** Nur diese Eigenschaften kopieren (auf oberster Ebene). */
  only?: string[]
  /** Umsetzung von Referenzen; `undefined` = Referenz entfällt. */
  mapReference?: (value: any, property: string) => any
  /** Wird für jedes neu erzeugte Element aufgerufen (z. B. neue ID). */
  onCreate?: (copy: any, original: any) => void
}

const ALWAYS_SKIP = new Set(['id', 'incoming', 'outgoing', 'lanes', 'di'])

function isModdleElement(value: any): boolean {
  return !!value && typeof value === 'object' && typeof value.$type === 'string'
}

function hasValue(element: any, name: string): boolean {
  if (!Object.prototype.hasOwnProperty.call(element, name)) return false
  const value = element[name]
  if (value === undefined) return false
  if (Array.isArray(value)) return value.length > 0
  return true
}

/** Liefert eine vollständige Kopie eines moddle-Elements im Ziel-Modell. */
export function cloneModdleElement(moddle: any, element: any, options: CopyOptions = {}, parent?: any): any {
  if (!isModdleElement(element)) return element
  const descriptor = element.$descriptor

  if (descriptor && descriptor.isGeneric) {
    const copy = moddle.createAny(element.$type, descriptor.ns?.uri, {})
    for (const key of Object.keys(element)) {
      if (key === '$type') continue
      const value = element[key]
      copy[key] = cloneValue(moddle, value, options, copy)
    }
    if (parent) copy.$parent = parent
    options.onCreate?.(copy, element)
    return copy
  }

  let copy: any
  try {
    copy = moddle.create(element.$type)
  } catch {
    // Typ im Ziel-Modell unbekannt: als generisches Element übernehmen.
    copy = moddle.createAny(element.$type, descriptor?.ns?.uri, {})
  }
  copyProperties(moddle, element, copy, options)
  if (parent) copy.$parent = parent
  options.onCreate?.(copy, element)
  return copy
}

/** Kopiert Eigenschaften von `source` nach `target` (beide moddle-Elemente). */
export function copyProperties(moddle: any, source: any, target: any, options: CopyOptions = {}): void {
  const descriptor = source.$descriptor
  const targetDescriptor = target.$descriptor
  const exclude = new Set(options.exclude || [])
  const only = options.only ? new Set(options.only) : null
  const nested: CopyOptions = { mapReference: options.mapReference, onCreate: options.onCreate }

  for (const property of descriptor?.properties || []) {
    const name = property.name
    if (property.isVirtual || ALWAYS_SKIP.has(name) || exclude.has(name)) continue
    if (only && !only.has(name)) continue
    if (!hasValue(source, name)) continue
    if (targetDescriptor && !targetDescriptor.isGeneric && !targetDescriptor.propertiesByName?.[name]) continue

    const value = source[name]
    if (property.isReference) {
      const mapped = mapRef(value, name, options)
      if (mapped === undefined || (Array.isArray(mapped) && mapped.length === 0)) continue
      target.set(name, mapped)
      continue
    }
    if (Array.isArray(value)) {
      const list = target.get(name)
      for (const item of value) list.push(cloneValue(moddle, item, nested, target))
    } else {
      target.set(name, cloneValue(moddle, value, nested, target))
    }
  }

  // Unbekannte Attribute (z. B. flowaudit:…, ältere Kurzattribute) übernehmen.
  if (source.$attrs && (!only || only.has('$attrs'))) {
    for (const [key, value] of Object.entries(source.$attrs)) {
      if (!exclude.has(key)) target.$attrs[key] = value
    }
  }
}

function mapRef(value: any, name: string, options: CopyOptions): any {
  if (!options.mapReference) return value
  if (Array.isArray(value)) {
    return value.map((item) => options.mapReference!(item, name)).filter((item) => item !== undefined)
  }
  return options.mapReference(value, name)
}

function cloneValue(moddle: any, value: any, options: CopyOptions, parent: any): any {
  if (Array.isArray(value)) return value.map((item) => cloneValue(moddle, item, options, parent))
  if (isModdleElement(value)) return cloneModdleElement(moddle, value, options, parent)
  if (value && typeof value === 'object') return JSON.parse(JSON.stringify(value))
  return value
}
