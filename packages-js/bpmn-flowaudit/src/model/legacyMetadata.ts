/**
 * Single text metadata (legal basis, internal note) in `extensionElements`,
 * ported from `extensionElements.ts` of the audit_designer
 * (`leseMetadatum` → `readMetadata`, `schreibeMetadatum` → `writeMetadata`).
 *
 * Behaviour kept: every change goes through `modeling` (one undo step), an
 * empty text removes the entry instead of leaving an empty element, and an
 * empty `extensionElements` disappears with its last entry.
 */

import type { DiagramElement, ModdleElement, ModdleFactory, Modeling } from '../diagram/services'
import { extensionValues } from './extensions'

type Services = { modeling: Pick<Modeling, 'updateModdleProperties'>; bpmnFactory: ModdleFactory }

/** Reads the text value of a flowaudit entry; '' if not maintained. */
export function readMetadata(element: DiagramElement | null | undefined, type: string): string {
  if (!element?.businessObject) return ''
  const hit = extensionValues(element.businessObject).find((value) => value.$type === type)
  const value = hit?.get('value')
  return typeof value === 'string' ? value : ''
}

function removeEntry(element: DiagramElement, existing: ModdleElement, values: ModdleElement[], services: Services): void {
  const bo = element.businessObject
  const extension = bo.get('extensionElements') as ModdleElement
  const rest = values.filter((entry) => entry !== existing)
  if (rest.length === 0) services.modeling.updateModdleProperties(element, bo, { extensionElements: undefined })
  else services.modeling.updateModdleProperties(element, extension, { values: rest })
}

function addEntry(element: DiagramElement, type: string, text: string, values: ModdleElement[], services: Services): void {
  const bo = element.businessObject
  const extension = bo.get('extensionElements') as ModdleElement | undefined
  const entry = services.bpmnFactory.create(type, { value: text })
  if (extension) {
    entry.$parent = extension
    services.modeling.updateModdleProperties(element, extension, { values: [...values, entry] })
    return
  }
  // extensionElements and entry in one step: otherwise one input would
  // produce two undo steps.
  const created = services.bpmnFactory.create('bpmn:ExtensionElements', { values: [entry] })
  created.$parent = bo
  entry.$parent = created
  services.modeling.updateModdleProperties(element, bo, { extensionElements: created })
}

/** Writes (or removes) a flowaudit text entry. */
export function writeMetadata(element: DiagramElement, type: string, value: string, services: Services): void {
  const text = (value ?? '').trim()
  const values = extensionValues(element.businessObject)
  const existing = values.find((entry) => entry.$type === type) ?? null
  if (!text && !existing) return
  if (!text && existing) {
    removeEntry(element, existing, values, services)
    return
  }
  if (existing) {
    services.modeling.updateModdleProperties(element, existing, { value: text })
    return
  }
  addEntry(element, type, text, values, services)
}
