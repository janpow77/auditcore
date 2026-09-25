/**
 * Reading and writing all FlowAudit data in `bpmn:extensionElements`.
 *
 * Writing replaces only the FlowAudit children of the fields contained in
 * the patch; foreign extensions (camunda, zeebe, …) and untouched FlowAudit
 * children stay. FlowAudit children are ordered by `WRITE_ORDER` so the
 * Python and the JavaScript side produce the same XML.
 *
 * In the editor every change goes through `modeling.updateModdleProperties`,
 * i.e. through the command stack (one undo step per user input). Without an
 * editor (headless, e.g. neutralisation) `setExtensionsDirect` mutates the
 * model.
 */

import type { DiagramElement, ModdleElement, ModdleFactory, Modeling } from '../diagram/services'
import { WRITE_ORDER } from '../schema/spec'
import { emptyExtensions, type Extensions } from '../schema/types'
import { fromModdle, isFlowauditElement, localXmlName, toModdle } from './moddleMapping'

type ExtensionKey = keyof Extensions

interface ExtensionField {
  key: ExtensionKey
  xml: string
  /** Additional local names read (and removed on write) for this field. */
  aliases?: string[]
  many: boolean
}

/** Mapping of `Extensions` keys to XML names (declarative, used both ways). */
export const EXTENSION_FIELDS: ExtensionField[] = [
  { key: 'diagramInfo', xml: 'diagrammInfo', many: false },
  { key: 'actor', xml: 'akteur', many: false },
  { key: 'legalBases', xml: 'rechtsgrundlage', many: true },
  { key: 'internalNote', xml: 'interneNotiz', aliases: ['notiz'], many: false },
  { key: 'markers', xml: 'kennzeichen', many: true },
  { key: 'auditReferences', xml: 'pruefbezug', many: true },
  { key: 'controls', xml: 'kontrolle', many: true },
  { key: 'risks', xml: 'risiko', many: true },
  { key: 'evidence', xml: 'nachweis', many: true },
  { key: 'deadlines', xml: 'frist', many: true },
  { key: 'crossReferences', xml: 'verweis', many: true },
  { key: 'auditSteps', xml: 'pruefschritt', many: true },
  { key: 'findings', xml: 'feststellung', many: true },
  { key: 'sources', xml: 'quelle', many: true },
  { key: 'esi', xml: 'esiAnforderungen', many: false },
]

const FIELD_BY_XML = new Map<string, ExtensionField>(
  EXTENSION_FIELDS.flatMap((field) => [field.xml, ...(field.aliases ?? [])].map((name) => [name, field] as const)),
)
const FIELD_BY_KEY = new Map<ExtensionKey, ExtensionField>(EXTENSION_FIELDS.map((field) => [field.key, field]))

/** All values of `extensionElements` (empty list if there are none). */
export function extensionValues(bo: ModdleElement | undefined | null): ModdleElement[] {
  if (!bo || typeof bo.get !== 'function') return []
  const extension = bo.get('extensionElements') as ModdleElement | undefined
  return ((extension?.get('values') as ModdleElement[] | undefined) ?? []).filter(Boolean)
}

function readSingle(value: ModdleElement, field: ExtensionField): unknown {
  if (field.key === 'internalNote') return fromModdle<{ text?: string }>(value).text
  return fromModdle(value)
}

/** Reads all FlowAudit data of a business object. */
export function readExtensions(bo: ModdleElement | undefined | null): Extensions {
  const result = emptyExtensions() as unknown as Record<string, unknown>
  for (const value of extensionValues(bo)) {
    if (!isFlowauditElement(value)) continue
    const field = FIELD_BY_XML.get(localXmlName(value))
    if (!field) continue
    if (field.many) {
      ;(result[field.key] as object[]).push(fromModdle(value))
    } else if (result[field.key] === undefined) {
      const single = readSingle(value, field)
      if (single !== undefined) result[field.key] = single
    }
  }
  return result as unknown as Extensions
}

function createForField(factory: ModdleFactory, field: ExtensionField, value: unknown): ModdleElement[] {
  if (field.many) return ((value as object[] | undefined) ?? []).map((item) => toModdle(factory, field.xml, item))
  if (field.key === 'internalNote') {
    const note = typeof value === 'string' ? value.trim() : ''
    return note ? [toModdle(factory, field.xml, { text: note })] : []
  }
  const isFilled = value && typeof value === 'object' && Object.values(value).some((v) => v !== undefined && v !== '')
  return isFilled ? [toModdle(factory, field.xml, value as object)] : []
}

function rank(value: ModdleElement): number {
  if (!isFlowauditElement(value)) return -1
  const field = FIELD_BY_XML.get(localXmlName(value))
  const index = field ? (WRITE_ORDER as readonly string[]).indexOf(field.xml) : -1
  return index === -1 ? WRITE_ORDER.length : index
}

/**
 * New value list of `extensionElements`: foreign entries first (in their
 * order), then FlowAudit entries in schema order.
 */
export function computeValues(previous: ModdleElement[], patch: Partial<Extensions>, factory: ModdleFactory): ModdleElement[] {
  const replaced = new Set<string>()
  const created: ModdleElement[] = []
  for (const [key, value] of Object.entries(patch) as [ExtensionKey, unknown][]) {
    const field = FIELD_BY_KEY.get(key)
    if (!field) continue
    for (const name of [field.xml, ...(field.aliases ?? [])]) replaced.add(name)
    created.push(...createForField(factory, field, value))
  }
  const kept = previous.filter((value) => !(isFlowauditElement(value) && replaced.has(localXmlName(value))))
  const foreign = kept.filter((value) => !isFlowauditElement(value))
  const own = [...kept.filter(isFlowauditElement), ...created]
    .map((value, index) => ({ value, index }))
    .sort((a, b) => rank(a.value) - rank(b.value) || a.index - b.index)
    .map((entry) => entry.value)
  return [...foreign, ...own]
}

function sameList(a: ModdleElement[], b: ModdleElement[]): boolean {
  return a.length === b.length && a.every((value, index) => value === b[index])
}

/**
 * Writes part of the extensions through `modeling` (one undo step). When the
 * last entry disappears, `extensionElements` is removed as well.
 */
export function writeExtensions(
  element: DiagramElement,
  patch: Partial<Extensions>,
  services: { modeling: Modeling; moddle: ModdleFactory },
  bo: ModdleElement = element.businessObject,
): void {
  const { modeling, moddle } = services
  const extension = bo.get('extensionElements') as ModdleElement | undefined
  const previous = extensionValues(bo)
  const values = computeValues(previous, patch, moddle)
  if (sameList(values, previous)) return
  if (!values.length) {
    if (extension) modeling.updateModdleProperties(element, bo, { extensionElements: undefined })
    return
  }
  if (extension) {
    for (const value of values) value.$parent = extension
    modeling.updateModdleProperties(element, extension, { values })
    return
  }
  modeling.updateModdleProperties(element, bo, { extensionElements: createExtensionElements(moddle, bo, values) })
}

function createExtensionElements(factory: ModdleFactory, bo: ModdleElement, values: ModdleElement[]): ModdleElement {
  const extension = factory.create('bpmn:ExtensionElements', { values })
  extension.$parent = bo
  for (const value of values) value.$parent = extension
  return extension
}

/** Like `writeExtensions`, but mutates the model directly (headless). */
export function setExtensionsDirect(bo: ModdleElement, patch: Partial<Extensions>, factory: ModdleFactory): void {
  const extension = bo.get('extensionElements') as ModdleElement | undefined
  const values = computeValues(extensionValues(bo), patch, factory)
  if (!values.length) {
    if (extension) bo.set('extensionElements', undefined)
    return
  }
  if (!extension) {
    bo.set('extensionElements', createExtensionElements(factory, bo, values))
    return
  }
  for (const value of values) value.$parent = extension
  extension.set('values', values)
}
