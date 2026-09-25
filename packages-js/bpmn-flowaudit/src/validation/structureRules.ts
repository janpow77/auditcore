/**
 * Structure rules (`BPMN-S…`), same logic as `auditcore_bpmn`.
 */

import { isActivity, isGateway, isTask, localType, type ModelElement } from '../model/processModel'
import type { RuleContext } from './context'

function processes(ctx: RuleContext): void {
  const all = ctx.model.elements
  const processList = all.filter((el) => el.type === 'bpmn:Process')
  if (!processList.length && !all.some((el) => el.type === 'bpmn:Participant')) ctx.report('BPMN-S002', null)
  for (const process of processList) {
    const nodes = ctx.nodes.filter((el) => el.parentId === process.id)
    if (!nodes.length) continue
    if (!nodes.some((el) => localType(el.type) === 'startEvent')) ctx.report('BPMN-S010', process.id, { name: ctx.name(process) })
    if (!nodes.some((el) => localType(el.type) === 'endEvent')) ctx.report('BPMN-S011', process.id, { name: ctx.name(process) })
  }
}

function sequenceFlows(ctx: RuleContext): void {
  for (const flow of ctx.sequenceFlows) {
    if (!flow.sourceId || !flow.targetId) ctx.report('BPMN-S020', flow.id, { id: flow.id })
    for (const ref of [flow.sourceId, flow.targetId]) {
      if (ref && !ctx.model.byId.has(ref)) ctx.report('BPMN-S021', flow.id, { id: flow.id, ref })
    }
    const source = ctx.model.byId.get(flow.sourceId ?? '')
    const target = ctx.model.byId.get(flow.targetId ?? '')
    if (source && target && source.parentId !== target.parentId) ctx.report('BPMN-S022', flow.id, { id: flow.id })
  }
}

function poolOf(element: ModelElement): string | undefined {
  return element.type === 'bpmn:Participant' ? element.id : element.poolId
}

function messageFlows(ctx: RuleContext): void {
  for (const flow of ctx.model.elements.filter((el) => el.type === 'bpmn:MessageFlow')) {
    const source = ctx.model.byId.get(flow.sourceId ?? '')
    const target = ctx.model.byId.get(flow.targetId ?? '')
    if (!source || !target) ctx.report('BPMN-S024', flow.id, { id: flow.id })
    else if (poolOf(source) && poolOf(source) === poolOf(target)) ctx.report('BPMN-S023', flow.id, { id: flow.id })
  }
  for (const association of ctx.model.elements.filter((el) => el.type === 'bpmn:Association')) {
    for (const ref of [association.sourceId, association.targetId]) {
      if (ref && !ctx.model.byId.has(ref)) ctx.report('BPMN-S071', association.id, { id: association.id, ref })
    }
  }
}

function isExempt(ctx: RuleContext, node: ModelElement): boolean {
  const parent = ctx.model.byId.get(node.parentId ?? '')
  return (parent !== undefined && localType(parent.type) === 'adHocSubProcess') || Boolean(node.isCompensation)
}

function connectedByMessage(ctx: RuleContext): Set<string> {
  const flows = ctx.model.elements.filter((el) => el.type === 'bpmn:MessageFlow')
  return new Set(flows.flatMap((flow) => [flow.sourceId, flow.targetId]).filter((id): id is string => Boolean(id)))
}

interface NodeFlows {
  type: string
  ins: number
  outs: number
}

/** Start events without incoming and end events without outgoing flows. */
function eventDirections(ctx: RuleContext, node: ModelElement, flows: NodeFlows): void {
  if (flows.type === 'startEvent' && flows.ins) ctx.report('BPMN-S015', node.id, { name: ctx.name(node) })
  if (flows.type === 'endEvent' && flows.outs) ctx.report('BPMN-S016', node.id, { name: ctx.name(node) })
}

function isOrphan(ctx: RuleContext, node: ModelElement, flows: NodeFlows, messages: Set<string>): boolean {
  if (flows.ins || flows.outs || messages.has(node.id)) return false
  const inEventSubProcess = Boolean(ctx.model.byId.get(node.parentId ?? '')?.isEventSubProcess)
  return !(flows.type === 'startEvent' && inEventSubProcess)
}

/** Missing incoming/outgoing flows (link events connect without flows). */
function missingFlows(ctx: RuleContext, node: ModelElement, flows: NodeFlows): void {
  const isLink = node.linkName !== undefined
  const linkCatch = flows.type === 'intermediateCatchEvent' && isLink
  const linkThrow = flows.type === 'intermediateThrowEvent' && isLink
  if (!flows.ins && flows.type !== 'startEvent' && !linkCatch) ctx.report('BPMN-S013', node.id, { name: ctx.name(node) })
  if (!flows.outs && flows.type !== 'endEvent' && !linkThrow) ctx.report('BPMN-S014', node.id, { name: ctx.name(node) })
}

function nodeConnections(ctx: RuleContext, node: ModelElement, messages: Set<string>): void {
  const flows: NodeFlows = { type: localType(node.type), ins: ctx.incoming(node.id).length, outs: ctx.outgoing(node.id).length }
  eventDirections(ctx, node, flows)
  if (flows.type === 'boundaryEvent' || isExempt(ctx, node)) return
  if (isOrphan(ctx, node, flows, messages)) ctx.report('BPMN-S012', node.id, { name: ctx.name(node) })
  else missingFlows(ctx, node, flows)
}

function nodes(ctx: RuleContext): void {
  const messages = connectedByMessage(ctx)
  for (const node of ctx.nodes) nodeConnections(ctx, node, messages)
  for (const node of ctx.nodes) {
    if (isTask(node.type) && !node.name.trim()) ctx.report('BPMN-S050', node.id, { id: node.id })
  }
}

function splittingGateway(ctx: RuleContext, node: ModelElement, outs: ModelElement[]): void {
  const conditional = outs.some((flow) => flow.conditional)
  if (conditional && !node.defaultFlow) ctx.report('BPMN-S030', node.id, { name: ctx.name(node) })
  if (!conditional && !node.defaultFlow) ctx.report('BPMN-S032', node.id, { name: ctx.name(node) })
  if (!node.name.trim()) ctx.report('BPMN-S051', node.id, { id: node.id })
}

function gateway(ctx: RuleContext, node: ModelElement): void {
  const type = localType(node.type)
  const outs = ctx.outgoing(node.id)
  if ((type === 'exclusiveGateway' || type === 'inclusiveGateway') && outs.length > 1) splittingGateway(ctx, node, outs)
  if (type === 'parallelGateway' && outs.some((flow) => flow.conditional)) ctx.report('BPMN-S035', node.id, { name: ctx.name(node) })
  if (ctx.incoming(node.id).length === 1 && outs.length === 1) ctx.report('BPMN-S033', node.id, { name: ctx.name(node) })
  if (type === 'eventBasedGateway') eventGatewayTargets(ctx, node, outs)
}

/** An event-based gateway may only lead to catching events or receive tasks. */
function eventGatewayTargets(ctx: RuleContext, node: ModelElement, outs: ModelElement[]): void {
  for (const flow of outs) {
    const target = ctx.model.byId.get(flow.targetId ?? '')
    if (target && !['intermediateCatchEvent', 'receiveTask'].includes(localType(target.type))) {
      ctx.report('BPMN-S034', node.id, { name: ctx.name(node), ziel: ctx.name(target) })
    }
  }
}

function gateways(ctx: RuleContext): void {
  for (const node of ctx.nodes) {
    if (node.defaultFlow && !ctx.outgoing(node.id).some((flow) => flow.id === node.defaultFlow)) {
      ctx.report('BPMN-S031', node.id, { flow: node.defaultFlow, name: ctx.name(node) })
    }
    if (isGateway(node.type)) gateway(ctx, node)
  }
}

function boundaryEvents(ctx: RuleContext): void {
  for (const event of ctx.nodes.filter((node) => localType(node.type) === 'boundaryEvent')) {
    const host = ctx.model.byId.get(event.attachedTo ?? '')
    if (!host || !isActivity(host.type)) ctx.report('BPMN-S042', event.id, { name: ctx.name(event) })
    const compensation = event.eventDefinitions.includes('bpmn:CompensateEventDefinition')
    if (!ctx.outgoing(event.id).length && !compensation) ctx.report('BPMN-S040', event.id, { name: ctx.name(event) })
    if (ctx.incoming(event.id).length) ctx.report('BPMN-S041', event.id, { name: ctx.name(event) })
  }
}

function linksAndCalls(ctx: RuleContext): void {
  const catches = new Set(
    ctx.nodes.filter((node) => localType(node.type) === 'intermediateCatchEvent' && node.linkName !== undefined).map((node) => `${node.processId}|${node.linkName}`),
  )
  for (const node of ctx.nodes) {
    const type = localType(node.type)
    if (type === 'intermediateThrowEvent' && node.linkName !== undefined && !catches.has(`${node.processId}|${node.linkName}`)) {
      ctx.report('BPMN-S060', node.id, { name: ctx.name(node), link: node.linkName })
    }
    if (type === 'callActivity' && !node.calledElement) ctx.report('BPMN-S061', node.id, { name: ctx.name(node) })
  }
}

export const STRUCTURE_RULES = [processes, sequenceFlows, messageFlows, nodes, gateways, boundaryEvents, linksAndCalls]
