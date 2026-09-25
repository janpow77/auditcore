/**
 * Uniform write access to elements – for a running editor (through
 * `modeling`, undoable) and headless on moddle definitions. Enrichment and
 * other bulk operations use this, so they work in both worlds.
 */

import type { EditorServices, ModdleElement, ModdleFactory } from '../diagram/services'
import type { Extensions } from '../schema/types'
import { readExtensions, setExtensionsDirect, writeExtensions } from './extensions'

export interface ModelAccess {
  has(id: string): boolean
  read(id: string): Extensions
  write(id: string, patch: Partial<Extensions>): void
  name(id: string): string
  rename(id: string, name: string): void
  setColor(id: string, color: { fill: string; stroke: string } | null): void
}

export function editorAccess(services: EditorServices): ModelAccess {
  const element = (id: string) => services.elementRegistry.get(id)
  return {
    has: (id) => Boolean(element(id)),
    read: (id) => readExtensions(element(id)?.businessObject),
    write: (id, patch) => {
      const target = element(id)
      if (target) writeExtensions(target, patch, services)
    },
    name: (id) => String(element(id)?.businessObject.get('name') ?? ''),
    rename: (id, name) => {
      const target = element(id)
      if (target) services.modeling.updateProperties(target, { name })
    },
    setColor: (id, color) => {
      const target = element(id)
      if (target) services.modeling.setColor([target], { fill: color?.fill ?? null, stroke: color?.stroke ?? null })
    },
  }
}

function indexById(definitions: ModdleElement): Map<string, ModdleElement> {
  const index = new Map<string, ModdleElement>()
  const visit = (value: unknown, depth: number) => {
    if (depth > 60 || !value || typeof value !== 'object') return
    if (Array.isArray(value)) {
      for (const item of value) visit(item, depth + 1)
      return
    }
    const element = value as ModdleElement
    if (typeof element.$type !== 'string') return
    if (element.id && !index.has(String(element.id))) index.set(String(element.id), element)
    for (const [key, child] of Object.entries(element)) {
      if (!key.startsWith('$') && key !== 'bpmnElement' && !key.endsWith('Ref') && key !== 'di') visit(child, depth + 1)
    }
  }
  visit(definitions, 0)
  return index
}

const BIOC = { fill: 'bioc:fill', stroke: 'bioc:stroke' }
const COLOR = { fill: 'color:background-color', stroke: 'color:border-color' }

function shapeFor(definitions: ModdleElement, id: string): ModdleElement | undefined {
  for (const diagram of (definitions.get('diagrams') as ModdleElement[] | undefined) ?? []) {
    const plane = diagram.get('plane') as ModdleElement | undefined
    const shapes = (plane?.get('planeElement') as ModdleElement[] | undefined) ?? []
    const shape = shapes.find((di) => (di.get('bpmnElement') as ModdleElement | undefined)?.id === id)
    if (shape) return shape
  }
  return undefined
}

export function headlessAccess(definitions: ModdleElement, factory: ModdleFactory): ModelAccess {
  const index = indexById(definitions)
  return {
    has: (id) => index.has(id),
    read: (id) => readExtensions(index.get(id)),
    write: (id, patch) => {
      const target = index.get(id)
      if (target) setExtensionsDirect(target, patch, factory)
    },
    name: (id) => String(index.get(id)?.get('name') ?? ''),
    rename: (id, name) => index.get(id)?.set('name', name),
    setColor: (id, color) => {
      const shape = shapeFor(definitions, id)
      if (!shape) return
      for (const names of [BIOC, COLOR]) {
        shape.set(names.fill, color?.fill)
        shape.set(names.stroke, color?.stroke)
      }
    },
  }
}
