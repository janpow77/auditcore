/**
 * Segregation of duties (`BPMN-FT…`): rules come from the profile
 * (`funktionstrennung`), messages from the rule catalogue.
 */

import { isActivity, isGateway, type ModelElement } from '../model/processModel'
import { localized, type SegregationRuleData, type SelectionData } from '../profile/profile'
import { RULES, SEVERITY_LABELS, type Severity } from './catalog'
import type { RuleContext } from './context'

function matches(element: ModelElement, selection: SelectionData | undefined): boolean {
  if (!selection) return false
  const ext = element.extensions
  if (selection.markers?.length && ext.markers.some((marker) => selection.markers?.includes(marker.type))) return true
  return Boolean(selection.audit_types?.length) && ext.auditReferences.some((ref) => selection.audit_types?.includes(ref.auditType ?? ''))
}

function reportRule(ctx: RuleContext, rule: SegregationRuleData, template: string, element: ModelElement, params: Record<string, unknown>): void {
  const severity = (rule.severity in SEVERITY_LABELS ? rule.severity : RULES[template].severity) as Severity
  ctx.add({
    ruleId: `BPMN-${rule.id}`,
    severity,
    params: { titel: localized(rule.title), titel_de: localized(rule.title, 'de'), titel_en: localized(rule.title, 'en'), ...params },
    elementId: element.id,
    templateId: template,
  })
}

function separateBodies(ctx: RuleContext, rule: SegregationRuleData): void {
  const activityNodes = ctx.nodes.filter((node) => isActivity(node.type))
  const groupA = activityNodes.filter((node) => matches(node, rule.a))
  const groupB = activityNodes.filter((node) => matches(node, rule.b))
  for (const a of groupA) {
    const bodyA = ctx.bodyOf(a)
    for (const b of groupB) {
      const bodyB = ctx.bodyOf(b)
      if (a.id !== b.id && bodyA && bodyB && bodyA[0] === bodyB[0]) {
        reportRule(ctx, rule, 'BPMN-FT-STELLEN', a, { a: ctx.name(a), b: ctx.name(b), stelle: bodyA[1] })
      }
    }
  }
}

function excludedRole(ctx: RuleContext, rule: SegregationRuleData): void {
  for (const node of ctx.nodes) {
    const role = node.actor?.role
    if (isActivity(node.type) && matches(node, rule.selection) && role && (rule.roles ?? []).includes(role)) {
      reportRule(ctx, rule, 'BPMN-FT-ROLLE', node, { name: ctx.name(node), rolle: role })
    }
  }
}

/** Follows sequence flows (through gateways) to the next activities. */
function successorActivities(ctx: RuleContext, start: ModelElement): ModelElement[] {
  const queue = ctx.outgoing(start.id).map((flow) => flow.targetId)
  const visited = new Set<string>()
  const found: ModelElement[] = []
  while (queue.length) {
    const id = queue.shift()
    if (!id || visited.has(id)) continue
    visited.add(id)
    const next = ctx.model.byId.get(id)
    if (next && isActivity(next.type)) found.push(next)
    else if (next && isGateway(next.type)) queue.push(...ctx.outgoing(next.id).map((flow) => flow.targetId))
  }
  return found
}

function hasSecondBody(ctx: RuleContext, node: ModelElement): boolean {
  const own = ctx.bodyOf(node)
  const differentBody = successorActivities(ctx, node).some((next) => {
    const body = ctx.bodyOf(next)
    return Boolean(own && body && body[0] !== own[0])
  })
  if (differentBody) return true
  const ownRole = node.actor?.role
  return node.extensions.controls.some((control) => control.responsible && (!ownRole || control.responsible !== ownRole))
}

function fourEyes(ctx: RuleContext, rule: SegregationRuleData): void {
  for (const node of ctx.nodes) {
    if (node.extensions.markers.some((marker) => marker.type === 'vier_augen') && !hasSecondBody(ctx, node)) {
      reportRule(ctx, rule, 'BPMN-FT-VIERAUGEN', node, { name: ctx.name(node) })
    }
  }
}

const HANDLERS: Record<string, (ctx: RuleContext, rule: SegregationRuleData) => void> = {
  separate_bodies: separateBodies,
  excluded_role: excludedRole,
  four_eyes: fourEyes,
}

function segregation(ctx: RuleContext): void {
  for (const rule of ctx.profile?.segregation_rules ?? []) HANDLERS[rule.kind]?.(ctx, rule)
}

export const SEGREGATION_RULES = [segregation]
