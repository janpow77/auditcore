/**
 * Name/value properties of the Camunda namespace
 * (`camunda:properties/camunda:property name="…" value="…"`).
 *
 * The descriptor of the Camunda namespace is deliberately not registered:
 * moddle keeps the elements as generic elements, so loading and saving
 * without an edit leaves the XML untouched. Reading and writing work on
 * those generic elements. Writing changes only the properties named in the
 * patch – foreign properties, their order and other extensions stay as they
 * are – and an empty value removes the property instead of storing it empty.
 */

import type { DiagramElement, ModdleElement, ModdleFactory, Modeling } from '../diagram/services'
import { extensionValues } from './extensions'
import { isFlowauditElement } from './moddleMapping'

export const CAMUNDA_NAMESPACE = 'http://camunda.org/schema/1.0/bpmn'
const DEFAULT_PREFIX = 'camunda'

export interface NamedProperty {
  name: string
  value: string
}

/** Patch per property name; `''`, `null` or `undefined` removes the property. */
export type PropertyPatch = Record<string, string | null | undefined>

interface GenericDescriptor {
  ns?: { uri?: string; localName?: string; prefix?: string }
}

function descriptorOf(element: ModdleElement): GenericDescriptor | undefined {
  return (element as { $descriptor?: GenericDescriptor }).$descriptor
}

function isCamunda(element: ModdleElement | undefined, localName: string): boolean {
  const ns = element ? descriptorOf(element)?.ns : undefined
  if (ns?.uri) return ns.uri === CAMUNDA_NAMESPACE && ns.localName === localName
  return Boolean(element && element.$type.endsWith(`:${localName}`) && element.$type.startsWith(`${DEFAULT_PREFIX}:`))
}

function childrenOf(container: ModdleElement): ModdleElement[] {
  return ((container.get('$children') as ModdleElement[] | undefined) ?? []).filter(Boolean)
}

/** All `camunda:properties` containers of a business object. */
export function propertyContainers(bo: ModdleElement | undefined | null): ModdleElement[] {
  return extensionValues(bo).filter((value) => isCamunda(value, 'properties'))
}

/** All properties of a business object in document order. */
export function readNamedProperties(bo: ModdleElement | undefined | null): NamedProperty[] {
  return propertyContainers(bo).flatMap((container) =>
    childrenOf(container)
      .filter((child) => isCamunda(child, 'property'))
      .map((child) => ({ name: String(child.get('name') ?? ''), value: String(child.get('value') ?? '') }))
      .filter((entry) => entry.name),
  )
}

/** Value of the first property with this name (`''` if there is none). */
export function namedPropertyValue(bo: ModdleElement | undefined | null, name: string): string {
  return readNamedProperties(bo).find((entry) => entry.name === name)?.value ?? ''
}

function prefixOf(containers: ModdleElement[]): string {
  const [first] = containers
  return (first && descriptorOf(first)?.ns?.prefix) || DEFAULT_PREFIX
}

function createProperty(factory: ModdleFactory, prefix: string, name: string, value: string): ModdleElement {
  if (!factory.createAny) throw new Error('moddle.createAny fehlt: Eigenschaften lassen sich nicht anlegen.')
  return factory.createAny(`${prefix}:property`, CAMUNDA_NAMESPACE, { name, value })
}

/** New child list of a container after applying the patch (unchanged entries stay the same objects). */
function patchedChildren(children: ModdleElement[], patch: PropertyPatch, pending: Set<string>, create: (name: string, value: string) => ModdleElement): ModdleElement[] {
  const result: ModdleElement[] = []
  for (const child of children) {
    const name = isCamunda(child, 'property') ? String(child.get('name') ?? '') : ''
    if (!name || !(name in patch)) {
      result.push(child)
      continue
    }
    const value = (patch[name] ?? '').trim()
    // Only the first occurrence carries the new value; duplicates of a patched name are dropped.
    if (value && pending.has(name)) result.push(String(child.get('value') ?? '') === value ? child : create(name, value))
    pending.delete(name)
  }
  return result
}

export interface PropertyPlan {
  /** New child lists per existing container (only containers that change). */
  containers: Map<ModdleElement, ModdleElement[]>
  /** Properties that need a new container (no container exists yet). */
  created: ModdleElement[]
  prefix: string
}

/** Computes the changes without touching the model. */
export function planPropertyPatch(bo: ModdleElement, patch: PropertyPatch, factory: ModdleFactory): PropertyPlan {
  const containers = propertyContainers(bo)
  const prefix = prefixOf(containers)
  const create = (name: string, value: string) => createProperty(factory, prefix, name, value)
  const pending = new Set(Object.keys(patch))
  const changed = new Map<ModdleElement, ModdleElement[]>()
  for (const container of containers) {
    const before = childrenOf(container)
    const after = patchedChildren(before, patch, pending, create)
    if (after.length !== before.length || after.some((child, index) => child !== before[index])) changed.set(container, after)
  }
  const additions = [...pending].filter((name) => (patch[name] ?? '').trim()).map((name) => create(name, (patch[name] ?? '').trim()))
  const [first] = containers
  if (first && additions.length) changed.set(first, [...(changed.get(first) ?? childrenOf(first)), ...additions])
  return { containers: changed, created: first ? [] : additions, prefix }
}

function createContainer(factory: ModdleFactory, prefix: string, children: ModdleElement[]): ModdleElement {
  if (!factory.createAny) throw new Error('moddle.createAny fehlt: Eigenschaften lassen sich nicht anlegen.')
  const container = factory.createAny(`${prefix}:properties`, CAMUNDA_NAMESPACE, {})
  container.set('$children', children)
  for (const child of children) child.$parent = container
  return container
}

/** Extension values after the plan: emptied containers disappear, a new container goes after the foreign entries. */
function valuesAfter(bo: ModdleElement, plan: PropertyPlan, factory: ModdleFactory): ModdleElement[] {
  const emptied = new Set([...plan.containers].filter(([, children]) => !children.length).map(([container]) => container))
  const values = extensionValues(bo).filter((value) => !emptied.has(value))
  if (!plan.created.length) return values
  const container = createContainer(factory, plan.prefix, plan.created)
  const firstOwn = values.findIndex(isFlowauditElement)
  return firstOwn === -1 ? [...values, container] : [...values.slice(0, firstOwn), container, ...values.slice(firstOwn)]
}

function setValues(element: DiagramElement, bo: ModdleElement, values: ModdleElement[], services: { modeling: Modeling; moddle: ModdleFactory }): void {
  const { modeling, moddle } = services
  const extension = bo.get('extensionElements') as ModdleElement | undefined
  if (!values.length) {
    if (extension) modeling.updateModdleProperties(element, bo, { extensionElements: undefined })
  } else if (extension) {
    for (const value of values) value.$parent = extension
    modeling.updateModdleProperties(element, extension, { values })
  } else {
    const created = moddle.create('bpmn:ExtensionElements', { values })
    created.$parent = bo
    for (const value of values) value.$parent = created
    modeling.updateModdleProperties(element, bo, { extensionElements: created })
  }
}

/**
 * Writes properties through `modeling` (undoable). Changes inside existing
 * containers are one command per container; a new or emptied container
 * changes the extension list.
 */
export function writeNamedProperties(
  element: DiagramElement,
  patch: PropertyPatch,
  services: { modeling: Modeling; moddle: ModdleFactory },
  bo: ModdleElement = element.businessObject,
): void {
  const plan = planPropertyPatch(bo, patch, services.moddle)
  for (const [container, children] of plan.containers) {
    if (!children.length) continue
    for (const child of children) child.$parent = container
    services.modeling.updateModdleProperties(element, container, { $children: children })
  }
  const emptied = [...plan.containers.values()].some((children) => !children.length)
  if (emptied || plan.created.length) setValues(element, bo, valuesAfter(bo, plan, services.moddle), services)
}

/** Like `writeNamedProperties`, but mutates the model directly (headless). */
export function setNamedPropertiesDirect(bo: ModdleElement, patch: PropertyPatch, factory: ModdleFactory): void {
  const plan = planPropertyPatch(bo, patch, factory)
  for (const [container, children] of plan.containers) {
    for (const child of children) child.$parent = container
    container.set('$children', children)
  }
  const emptied = [...plan.containers.values()].some((children) => !children.length)
  if (!emptied && !plan.created.length) return
  const values = valuesAfter(bo, plan, factory)
  let extension = bo.get('extensionElements') as ModdleElement | undefined
  if (!values.length) {
    bo.set('extensionElements', undefined)
    return
  }
  if (!extension) {
    extension = factory.create('bpmn:ExtensionElements', { values })
    extension.$parent = bo
    bo.set('extensionElements', extension)
  }
  for (const value of values) value.$parent = extension
  extension.set('values', values)
}
