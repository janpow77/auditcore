/**
 * Validation issue of a rule (wire form: `Befund.to_dict()` of
 * `auditcore_bpmn`).
 */

import { RULES, SEVERITY_LABELS, ruleText, type Severity } from './catalog'

export interface ValidationIssue {
  ruleId: string
  severity: Severity
  params: Record<string, unknown>
  elementId?: string
  diagramId?: string
  /** Message template if it differs from the rule id (segregation of duties). */
  templateId?: string
  /** Ready-made message delivered by a server (wins over the template). */
  message?: string
}

export function issue(ruleId: string, elementId?: string | null, params: Record<string, unknown> = {}): ValidationIssue {
  const rule = RULES[ruleId]
  if (!rule) throw new Error(`Unknown rule ${ruleId}`)
  const result: ValidationIssue = { ruleId, severity: rule.severity, params }
  if (elementId) result.elementId = elementId
  return result
}

export function issueMessage(item: ValidationIssue, locale: 'de' | 'en' = 'de'): string {
  if (item.message) return item.message
  const rule = RULES[item.templateId ?? item.ruleId]
  return rule ? ruleText(rule, locale, item.params) : item.ruleId
}

export function severityLabel(severity: Severity, locale: 'de' | 'en' = 'de'): string {
  return SEVERITY_LABELS[severity]?.[locale] ?? severity
}

const RANK: Record<Severity, number> = { fehler: 0, warnung: 1, hinweis: 2 }

export function sortIssues(issues: ValidationIssue[]): ValidationIssue[] {
  return [...issues].sort((a, b) => RANK[a.severity] - RANK[b.severity] || a.ruleId.localeCompare(b.ruleId))
}

export interface IssueCount {
  fehler: number
  warnung: number
  hinweis: number
}

export function countIssues(issues: ValidationIssue[]): IssueCount {
  const count: IssueCount = { fehler: 0, warnung: 0, hinweis: 0 }
  for (const item of issues) count[item.severity] += 1
  return count
}

/** Converts a server issue (`regel_id`, `schwere`, …) into a `ValidationIssue`. */
export function issueFromWire(data: Record<string, unknown>): ValidationIssue {
  const result: ValidationIssue = {
    ruleId: String(data.regel_id ?? data.rule_id ?? data.ruleId ?? ''),
    severity: String(data.schwere ?? data.severity ?? 'hinweis') as Severity,
    params: (data.parameter ?? data.params ?? {}) as Record<string, unknown>,
  }
  const optional: [keyof ValidationIssue, unknown][] = [
    ['elementId', data.element_id ?? data.elementId],
    ['diagramId', data.diagramm_id ?? data.diagram_id ?? data.diagramId],
    ['message', data.meldung ?? data.message],
  ]
  for (const [key, value] of optional) if (typeof value === 'string' && value) (result as unknown as Record<string, unknown>)[key] = value
  return result
}
