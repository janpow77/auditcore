/**
 * Shared state of one validation run.
 */

import { displayName, isFlowNode, type ModelElement, type ProcessModel } from '../model/processModel'
import type { ProfileData } from '../profile/profile'
import { roleOf } from '../profile/profile'
import { label, type Vocabulary } from '../schema/vocabulary'
import { issue, type ValidationIssue } from './issue'

export interface ValidationOptions {
  profile?: ProfileData | null
  /** Reference date `YYYY-MM-DD` (default: today). */
  referenceDate?: string
  disabled?: string[]
  /** Local element types for which BPMN-F001 applies (default: all tasks). */
  legalBasisRequiredFor?: string[]
}

export function today(): string {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
}

export class RuleContext {
  readonly issues: ValidationIssue[] = []
  readonly profile: ProfileData | null
  readonly referenceDate: string
  readonly nodes: ModelElement[]
  readonly sequenceFlows: ModelElement[]
  private readonly disabled: Set<string>

  constructor(
    readonly model: ProcessModel,
    readonly options: ValidationOptions,
  ) {
    this.profile = options.profile ?? null
    this.referenceDate = options.referenceDate ?? today()
    this.disabled = new Set(options.disabled ?? [])
    this.nodes = model.elements.filter((el) => isFlowNode(el.type))
    this.sequenceFlows = model.elements.filter((el) => el.type === 'bpmn:SequenceFlow')
  }

  add(item: ValidationIssue): void {
    if (!this.disabled.has(item.ruleId)) this.issues.push(item)
  }

  report(ruleId: string, elementId: string | null | undefined, params: Record<string, unknown> = {}): void {
    this.add(issue(ruleId, elementId, params))
  }

  name(element: ModelElement): string {
    return displayName(element)
  }

  outgoing(id: string): ModelElement[] {
    return this.sequenceFlows.filter((flow) => flow.sourceId === id)
  }

  incoming(id: string): ModelElement[] {
    return this.sequenceFlows.filter((flow) => flow.targetId === id)
  }

  /** Reports BPMN-P007 when `value` is not part of the vocabulary. */
  checkValue(elementId: string | null | undefined, name: string, field: string, value: string | undefined, vocabulary: Vocabulary): void {
    if (value && !(value in vocabulary)) {
      this.report('BPMN-P007', elementId, { wert: value, feld: field, name, zulaessig: Object.keys(vocabulary).join(', ') })
    }
  }

  /**
   * Body of an element for segregation rules: actor (role + display name),
   * otherwise lane/pool. Returns `[key, label]`.
   */
  bodyOf(element: ModelElement): [string, string] | null {
    const actor = element.actor
    if (actor?.role) {
      const role = roleOf(this.profile, actor.role)
      return [`${actor.role}|${actor.displayName ?? ''}`, actor.displayName || (role ? label(role.label) : actor.role)]
    }
    return actor?.sourceId ? [actor.sourceId, actor.sourceName || actor.sourceId] : null
  }
}
