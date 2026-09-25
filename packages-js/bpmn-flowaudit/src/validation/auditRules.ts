/**
 * Audit authority rules (`BPMN-P…`): controls, risks, audit trail,
 * deadlines, test steps and findings.
 */

import { localType, type ModelElement } from '../model/processModel'
import type { AuditFinding, Control, Risk } from '../schema/types'
import {
  EXECUTION_MODES,
  CONTROL_TYPES,
  DEADLINE_UNITS,
  FINDING_TYPES,
  FINDING_SEVERITIES,
  FINDING_STATUS,
  RISK_CATEGORIES,
  RISK_LEVELS,
  SOURCE_TYPES,
  TEST_RESULTS,
} from '../schema/vocabulary'
import type { RuleContext } from './context'
import { checkAuditReferences } from './domainRules'

const DATA_TYPES = ['dataObjectReference', 'dataStoreReference', 'dataObject', 'dataStore']

function duplicateIds(ctx: RuleContext): void {
  const seen = new Map<string, number>()
  const count = (id?: string) => id && seen.set(id, (seen.get(id) ?? 0) + 1)
  for (const element of ctx.model.elements) {
    const ext = element.extensions
    for (const item of [...ext.controls, ...ext.risks, ...ext.auditSteps, ...ext.findings]) count(item.id)
  }
  for (const item of [...(ctx.model.info?.risks ?? []), ...(ctx.model.info?.findings ?? [])]) count(item.id)
  for (const [id, n] of seen) if (n > 1) ctx.report('BPMN-P008', null, { id })
}

function controlIndex(ctx: RuleContext): Map<string, ModelElement> {
  const index = new Map<string, ModelElement>()
  for (const element of ctx.model.elements) for (const control of element.extensions.controls) if (control.id) index.set(control.id, element)
  return index
}

function isTested(ctx: RuleContext, element: ModelElement, control: Control): boolean {
  if (element.extensions.auditSteps.some((step) => step.control === undefined || step.control === control.id)) return true
  return ctx.model.elements.some((other) => other.extensions.auditSteps.some((step) => step.control === control.id))
}

function checkControl(ctx: RuleContext, element: ModelElement, control: Control): void {
  const name = ctx.name(element)
  const controlLabel = control.label || control.id || 'Kontrolle'
  if (!control.evidence && !element.hasDataAssociation) ctx.report('BPMN-P001', element.id, { kontrolle: controlLabel, name })
  if (control.keyControl && !isTested(ctx, element, control)) ctx.report('BPMN-P004', element.id, { kontrolle: controlLabel, name })
  ctx.checkValue(element.id, name, 'art', control.controlType, CONTROL_TYPES)
  ctx.checkValue(element.id, name, 'durchfuehrung', control.execution, EXECUTION_MODES)
}

export function checkRisk(ctx: RuleContext, id: string | null | undefined, name: string, risk: Risk, controls: Map<string, ModelElement>): void {
  const riskLabel = risk.label || risk.id || 'Risiko'
  if (!(risk.controls ?? []).length) ctx.report('BPMN-P005', id, { risiko: riskLabel, name })
  for (const controlId of risk.controls ?? []) {
    if (!controls.has(controlId)) ctx.report('BPMN-P006', id, { risiko: riskLabel, kontrolle: controlId })
  }
  ctx.checkValue(id, name, 'kategorie', risk.category, RISK_CATEGORIES)
  ctx.checkValue(id, name, 'inhaerent', risk.inherent, RISK_LEVELS)
  ctx.checkValue(id, name, 'kontrollrisiko', risk.controlRisk, RISK_LEVELS)
  ctx.checkValue(id, name, 'restrisiko', risk.residual, RISK_LEVELS)
}

export function checkFinding(ctx: RuleContext, id: string | null | undefined, name: string, finding: AuditFinding): void {
  if (!finding.findingType || !finding.description) ctx.report('BPMN-P009', id, { name })
  ctx.checkValue(id, name, 'art', finding.findingType, FINDING_TYPES)
  ctx.checkValue(id, name, 'einstufung', finding.severity, FINDING_SEVERITIES)
  ctx.checkValue(id, name, 'status', finding.status, FINDING_STATUS)
  if (finding.keyRequirement) checkAuditReferences(ctx, id, name, [{ keyRequirement: finding.keyRequirement, assessmentCriterion: finding.assessmentCriterion }])
}

function checkTestSteps(ctx: RuleContext, element: ModelElement, controls: Map<string, ModelElement>): void {
  const name = ctx.name(element)
  for (const step of element.extensions.auditSteps) {
    const stepLabel = step.id || step.case || 'Prüfschritt'
    ctx.checkValue(element.id, name, 'ergebnis', step.result, TEST_RESULTS)
    if (step.result === 'nicht_erfuellt') ctx.report('BPMN-P010', element.id, { schritt: stepLabel, name })
    if (step.control && !controls.has(step.control)) ctx.report('BPMN-P012', element.id, { schritt: stepLabel, kontrolle: step.control })
  }
}

function checkDeadlines(ctx: RuleContext, element: ModelElement): void {
  const ext = element.extensions
  for (const deadline of ext.deadlines) {
    if (!(deadline.legalBases ?? []).length && !ext.legalBases.length) {
      const text = [deadline.value, deadline.unit].filter(Boolean).join(' ') + (deadline.basis ? ` (${deadline.basis})` : '')
      ctx.report('BPMN-P003', element.id, { frist: text || 'Frist', name: ctx.name(element) })
    }
    ctx.checkValue(element.id, ctx.name(element), 'einheit', deadline.unit, DEADLINE_UNITS)
  }
}

function checkDataObject(ctx: RuleContext, element: ModelElement): void {
  const type = localType(element.type)
  if (!DATA_TYPES.includes(type)) return
  if ((type === 'dataObject' || type === 'dataStore') && ctx.model.elements.some((other) => other.dataRef === element.id)) return
  if (!element.extensions.evidence.some((item) => item.storageLocation)) ctx.report('BPMN-P002', element.id, { name: ctx.name(element) })
}

function checkElement(ctx: RuleContext, element: ModelElement, controls: Map<string, ModelElement>): void {
  const ext = element.extensions
  const name = ctx.name(element)
  for (const control of ext.controls) checkControl(ctx, element, control)
  if (ext.markers.some((marker) => marker.type === 'schluesselkontrolle') && !ext.controls.some((control) => control.keyControl)) {
    ctx.report('BPMN-P011', element.id, { name })
  }
  for (const risk of ext.risks) checkRisk(ctx, element.id, name, risk, controls)
  checkTestSteps(ctx, element, controls)
  for (const finding of ext.findings) checkFinding(ctx, element.id, name, finding)
  checkDeadlines(ctx, element)
  for (const source of ext.sources) ctx.checkValue(element.id, name, 'art', source.sourceType, SOURCE_TYPES)
  checkDataObject(ctx, element)
}

function elements(ctx: RuleContext): void {
  const controls = controlIndex(ctx)
  for (const element of ctx.model.elements) checkElement(ctx, element, controls)
  const info = ctx.model.info
  if (!info) return
  const title = info.title || 'Diagramm'
  for (const risk of info.risks ?? []) checkRisk(ctx, ctx.model.mainId, title, risk, controls)
  for (const finding of info.findings ?? []) checkFinding(ctx, ctx.model.mainId, title, finding)
}

export const AUDIT_RULES = [duplicateIds, elements]
