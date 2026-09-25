/**
 * Excerpt of a diagram for the collection: processes, calls, link events,
 * task counts and the index of stable domain keys.
 */

import { isActivity, localType, type ProcessModel } from '../model/processModel'
import type { AuditReference, CrossReference } from '../schema/types'
import { emptyExcerpt, type DiagramExcerpt, type KeyKind } from './collectionData'

class KeyIndex {
  readonly keys: Partial<Record<KeyKind, Record<string, string[]>>> = {}

  add(kind: KeyKind, value: string | undefined, elementId: string): void {
    const key = value?.trim()
    if (!key) return
    const byValue = (this.keys[kind] ??= {})
    const ids = (byValue[key] ??= [])
    if (!ids.includes(elementId)) ids.push(elementId)
  }

  references(list: AuditReference[], elementId: string): void {
    for (const ref of list) {
      this.add('ka', ref.keyRequirement, elementId)
      this.add('bk', ref.assessmentCriterion, elementId)
    }
  }

  crossReferences(list: CrossReference[], elementId: string): void {
    for (const ref of list) {
      if (ref.kind === 'prueffeld' || ref.kind === 'feststellung_ref' || ref.kind === 'register') this.add(ref.kind, ref.key, elementId)
    }
  }
}

function indexKeys(model: ProcessModel): KeyIndex {
  const index = new KeyIndex()
  for (const element of model.elements) {
    const ext = element.extensions
    index.references(ext.auditReferences, element.id)
    for (const finding of ext.findings) {
      index.references([{ keyRequirement: finding.keyRequirement, assessmentCriterion: finding.assessmentCriterion }], element.id)
      index.add('feststellung_ref', finding.reference, element.id)
    }
    index.crossReferences(ext.crossReferences, element.id)
    index.add('rolle', ext.actor?.role, element.id)
    for (const marker of ext.markers) index.add('kennzeichen', marker.type, element.id)
  }
  if (model.info) {
    const where = model.mainId ?? 'diagramm'
    index.references(model.info.auditReferences ?? [], where)
    index.crossReferences(model.info.crossReferences ?? [], where)
  }
  return index
}

function linkEvents(model: ProcessModel, type: string): [string, string][] {
  return model.elements
    .filter((el) => localType(el.type) === type && el.linkName)
    .map((el): [string, string] => [el.id, el.linkName as string])
}

export function excerptFromModel(model: ProcessModel): DiagramExcerpt {
  const activityList = model.elements.filter((el) => isActivity(el.type))
  return {
    ...emptyExcerpt(),
    processIds: model.elements.filter((el) => el.type === 'bpmn:Process').map((el) => el.id),
    calls: model.elements.filter((el) => el.calledElement).map((el): [string, string] => [el.id, el.calledElement as string]),
    linkThrows: linkEvents(model, 'intermediateThrowEvent'),
    linkCatches: linkEvents(model, 'intermediateCatchEvent'),
    tasks: activityList.length,
    tasksWithLegalBasis: activityList.filter((el) => el.extensions.legalBases.length > 0).length,
    keys: indexKeys(model).keys,
  }
}

/** Element ids of the diagram model matching a key (for highlighting). */
export function elementsForKey(model: ProcessModel, kind: KeyKind, value: string): string[] {
  return indexKeys(model).keys[kind]?.[value.trim()] ?? []
}
