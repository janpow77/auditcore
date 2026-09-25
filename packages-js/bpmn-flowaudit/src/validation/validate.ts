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
import { countIssues, type IssueCount, type ValidationIssue } from './issue'
import { SEGREGATION_RULES } from './segregationRules'
import { STRUCTURE_RULES } from './structureRules'

export const RULESET_VERSION = '2026.09.1'

export interface ValidationReport {
  rulesetVersion: string
  profile: string | null
  referenceDate: string
  valid: boolean
  count: IssueCount
  issues: ValidationIssue[]
}

const ALL_RULES = [...STRUCTURE_RULES, ...DOMAIN_RULES, ...AUDIT_RULES, ...SEGREGATION_RULES]

export function validateModel(model: ProcessModel, options: ValidationOptions = {}): ValidationReport {
  const ctx = new RuleContext(model, options)
  for (const rule of ALL_RULES) rule(ctx)
  const count = countIssues(ctx.issues)
  return {
    rulesetVersion: RULESET_VERSION,
    profile: ctx.profile ? profileReference(ctx.profile) : null,
    referenceDate: ctx.referenceDate,
    valid: count.fehler === 0,
    count,
    issues: ctx.issues,
  }
}

export type { ValidationOptions }
