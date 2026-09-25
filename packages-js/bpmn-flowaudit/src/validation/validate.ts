/**
 * Validation in the browser – same rule ids, severities and logic as
 * `auditcore_bpmn` (structure, domain data, audit authority functions,
 * segregation of duties from the profile). Applications may additionally
 * run the server validation through the `ValidationPort`.
 */

import type { ProcessModel } from '../model/processModel'
import { profileReference } from '../profile/profile'
import { AUDIT_RULES } from './auditRules'
import { RuleContext, type ValidationOptions } from './context'
import { DOMAIN_RULES } from './domainRules'
import { countIssues, issueMessage, severityLabel, type IssueCount, type ValidationIssue } from './issue'
import { SEGREGATION_RULES } from './segregationRules'
import { STRUCTURE_RULES } from './structureRules'

export const RULESET_VERSION = '2026.09.1'
export const REPORT_SCHEMA = 'auditcore_bpmn.validation-report/1'

export interface ValidationReport {
  rulesetVersion: string
  profile: string | null
  referenceDate: string
  valid: boolean
  counts: IssueCount
  issues: ValidationIssue[]
}

const ALL_RULES = [...STRUCTURE_RULES, ...DOMAIN_RULES, ...AUDIT_RULES, ...SEGREGATION_RULES]

export function validateModel(model: ProcessModel, options: ValidationOptions = {}): ValidationReport {
  const ctx = new RuleContext(model, options)
  for (const rule of ALL_RULES) rule(ctx)
  const counts = countIssues(ctx.issues)
  return {
    rulesetVersion: RULESET_VERSION,
    profile: ctx.profile ? profileReference(ctx.profile) : null,
    referenceDate: ctx.referenceDate,
    valid: counts.fehler === 0,
    counts,
    issues: ctx.issues,
  }
}

/** Report as JSON of `auditcore_bpmn` (`validation-report-1.schema.json`). */
export function reportToWire(report: ValidationReport, locale: 'de' | 'en' = 'de'): Record<string, unknown> {
  return {
    schema: REPORT_SCHEMA,
    ruleset_version: report.rulesetVersion,
    profile: report.profile,
    reference_date: report.referenceDate,
    valid: report.valid,
    counts: report.counts,
    issues: report.issues.map((item) => ({
      rule_id: item.ruleId,
      severity: item.severity,
      severity_label: severityLabel(item.severity, locale),
      message: issueMessage(item, locale),
      params: item.params,
      ...(item.elementId ? { element_id: item.elementId } : {}),
      ...(item.diagramId ? { diagram_id: item.diagramId } : {}),
    })),
  }
}

export type { ValidationOptions }
