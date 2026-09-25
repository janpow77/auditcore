/**
 * Walk-through mode: go through the diagram step by step and record per
 * step case/operation, voucher, result and remark (`flowaudit:pruefschritt`);
 * control tests per key control with sample size.
 */

import type { ModelAccess } from '../model/access'
import { displayName, isActivity, isGateway, type ModelElement, type ProcessModel } from '../model/processModel'
import { flowOrder } from '../reports/processReports'
import type { AuditStep, Control } from '../schema/types'

export interface WalkthroughStep {
  elementId: string
  name: string
  type: string
  steps: AuditStep[]
  keyControls: Control[]
  status: 'offen' | 'erfuellt' | 'nicht_erfuellt' | 'nicht_anwendbar'
}

function statusOf(steps: AuditStep[]): WalkthroughStep['status'] {
  if (!steps.length) return 'offen'
  if (steps.some((step) => step.result === 'nicht_erfuellt')) return 'nicht_erfuellt'
  if (steps.every((step) => step.result === 'nicht_anwendbar')) return 'nicht_anwendbar'
  return steps.every((step) => step.result === 'erfuellt' || step.result === 'nicht_anwendbar') ? 'erfuellt' : 'offen'
}

function toStep(element: ModelElement): WalkthroughStep {
  return {
    elementId: element.id,
    name: displayName(element),
    type: element.type,
    steps: element.extensions.auditSteps,
    keyControls: element.extensions.controls.filter((control) => control.keyControl),
    status: statusOf(element.extensions.auditSteps),
  }
}

/** Steps of the walk-through in flow order: activities and gateways. */
export function walkthroughSteps(model: ProcessModel, options: { withGateways?: boolean } = {}): WalkthroughStep[] {
  const includeGateways = options.withGateways ?? true
  return flowOrder(model)
    .filter((element) => isActivity(element.type) || (includeGateways && isGateway(element.type)))
    .map(toStep)
}

export interface WalkthroughProgress {
  total: number
  done: number
  met: number
  notMet: number
  open: number
}

export function walkthroughProgress(steps: WalkthroughStep[]): WalkthroughProgress {
  const count = (status: WalkthroughStep['status']) => steps.filter((step) => step.status === status).length
  return {
    total: steps.length,
    done: steps.length - count('offen'),
    met: count('erfuellt'),
    notMet: count('nicht_erfuellt'),
    open: count('offen'),
  }
}

/** Next id for an audit step (`PS1`, `PS2`, …) unique across the diagram. */
export function nextStepId(model: ProcessModel): string {
  const used = new Set(model.elements.flatMap((element) => element.extensions.auditSteps.map((step) => step.id)))
  let n = 1
  while (used.has(`PS${n}`)) n += 1
  return `PS${n}`
}

/** Records or replaces an audit step at an element. */
export function recordStep(access: ModelAccess, elementId: string, step: AuditStep): void {
  const existing = access.read(elementId).auditSteps
  const index = step.id ? existing.findIndex((item) => item.id === step.id) : -1
  const auditSteps = index >= 0 ? existing.map((item, i) => (i === index ? step : item)) : [...existing, step]
  access.write(elementId, { auditSteps })
}

export function removeStep(access: ModelAccess, elementId: string, stepId: string): void {
  access.write(elementId, { auditSteps: access.read(elementId).auditSteps.filter((item) => item.id !== stepId) })
}
