/**
 * Domain rules (`BPMN-F…`): legal bases, markers, audit references, key
 * references, actors and diagram info.
 */

import { isStructured } from '../model/legalBasis'
import type { ModelElement } from '../model/processModel'
import { criterionKnown, keyRequirement, keyRequirements, roleOf, roleProvided } from '../profile/profile'
import { roleAppliesTo, type Role } from '../schema/roles'
import type { AuditReference, DiagramInfo, LegalBasis } from '../schema/types'
import { AUDIT_TYPES, CONFIDENTIALITY, DIAGRAM_STATUS, MARKERS, VARIANTS, label } from '../schema/vocabulary'
import { TASK_TYPES, localType } from '../model/processModel'
import type { RuleContext } from './context'

const CROSS_REFERENCE_KINDS = ['prueffeld', 'feststellung_ref', 'register']
const COLOR = /^#[0-9A-Fa-f]{6}$/

export function checkLegalBases(ctx: RuleContext, id: string | null | undefined, name: string, list: LegalBasis[]): void {
  for (const basis of list) if (isStructured(basis) && !basis.act) ctx.report('BPMN-F010', id, { name })
}

function availableRange(ctx: RuleContext): string {
  const numbers = keyRequirements(ctx.profile).map((entry) => entry.number)
  return numbers.length ? `${Math.min(...numbers)}–${Math.max(...numbers)}` : 'keine'
}

function isKnownRequirement(ctx: RuleContext, number: number): boolean {
  if (!Number.isInteger(number)) return false
  return ctx.profile ? Boolean(keyRequirement(ctx.profile, number)) : number >= 1
}

/** KA/BK consistency of one audit reference (unknown KA, BK of another KA, BK not in catalogue). */
function checkRequirement(ctx: RuleContext, id: string | null | undefined, name: string, ref: AuditReference): void {
  const number = Number(String(ref.keyRequirement ?? '').trim())
  if (!isKnownRequirement(ctx, number)) {
    ctx.report('BPMN-F023', id, { ka: ref.keyRequirement ?? '', name, profil: ctx.profile?.id ?? '–', vorhanden: availableRange(ctx) })
    return
  }
  const criterion = ref.assessmentCriterion
  if (!criterion) return
  if (!criterion.trim().startsWith(`${number}.`)) ctx.report('BPMN-F024', id, { bk: criterion, ka: number, name })
  else if (criterionKnown(ctx.profile, number, criterion) === false) ctx.report('BPMN-F025', id, { bk: criterion, name })
}

export function checkAuditReferences(ctx: RuleContext, id: string | null | undefined, name: string, list: AuditReference[]): void {
  for (const ref of list) {
    checkRequirement(ctx, id, name, ref)
    if (ref.auditType && !(ref.auditType in AUDIT_TYPES)) ctx.report('BPMN-F026', id, { wert: ref.auditType, name })
  }
}

function checkActor(ctx: RuleContext, element: ModelElement): void {
  const kind = element.type === 'bpmn:Participant' ? 'Pool' : 'Lane'
  const actor = element.extensions.actor
  const name = ctx.name(element)
  if (!actor?.role) {
    ctx.report('BPMN-F020', element.id, { art: kind, art_en: kind, name })
    return
  }
  const role = roleOf(ctx.profile, actor.role)
  if (!role) {
    ctx.report('BPMN-F021', element.id, { rolle: actor.role, name, profil: ctx.profile?.id ?? '–' })
    return
  }
  checkRolePeriod(ctx, element, role, actor.role)
}

/** Role outside the profile or outside the programming period. */
function checkRolePeriod(ctx: RuleContext, element: ModelElement, role: Role, code: string): void {
  const period = ctx.model.info?.programmingPeriod || ctx.profile?.programming_period || null
  const provided = ctx.profile ? roleProvided(ctx.profile, code) : true
  if (provided && roleAppliesTo(role, period)) return
  ctx.report('BPMN-F022', element.id, {
    rolle: code,
    bezeichnung: label(role.label),
    bezeichnung_en: label(role.label, 'en'),
    name: ctx.name(element),
    periode: period ?? '?',
  })
}

function checkElement(ctx: RuleContext, element: ModelElement, requiredFor: Set<string>): void {
  const ext = element.extensions
  const name = ctx.name(element)
  if (requiredFor.has(localType(element.type)) && !ext.legalBases.length) ctx.report('BPMN-F001', element.id, { name })
  checkLegalBases(ctx, element.id, name, ext.legalBases)
  checkMarkers(ctx, element, name)
  checkAuditReferences(ctx, element.id, name, ext.auditReferences)
  for (const ref of ext.crossReferences) {
    if (!CROSS_REFERENCE_KINDS.includes(ref.kind ?? '') || !ref.key) ctx.report('BPMN-F027', element.id, { name, wert: ref.kind ?? '' })
  }
  if (element.type === 'bpmn:Participant' || element.type === 'bpmn:Lane') checkActor(ctx, element)
}

function checkMarkers(ctx: RuleContext, element: ModelElement, name: string): void {
  const ext = element.extensions
  for (const marker of ext.markers) {
    if (!(marker.type in MARKERS)) ctx.report('BPMN-F011', element.id, { typ: marker.type, name })
  }
  if (ext.markers.some((marker) => marker.type === 'rechtsgrundlage') && !ext.legalBases.length) ctx.report('BPMN-F012', element.id, { name })
}

function validDate(value: string | undefined): string | null {
  if (!value || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null
  const date = new Date(`${value}T00:00:00Z`)
  return Number.isNaN(date.getTime()) || date.toISOString().slice(0, 10) !== value ? null : value
}

function checkDates(ctx: RuleContext, where: string | null, info: DiagramInfo): void {
  const fields: [string, string | undefined][] = [
    ['gueltig_ab', info.validFrom],
    ['gueltig_bis', info.validUntil],
    ['freigegeben_am', info.approvedOn],
    ['vks_stichtag', info.systemCutoffDate],
  ]
  for (const [field, value] of fields) if (value && !validDate(value)) ctx.report('BPMN-F009', where, { feld: field, wert: value })
  const from = validDate(info.validFrom)
  const until = validDate(info.validUntil)
  if (from && until && from > until) ctx.report('BPMN-F007', where, { ab: info.validFrom, bis: info.validUntil })
  if (until && until < ctx.referenceDate) ctx.report('BPMN-F005', where, { datum: info.validUntil, stichtag: ctx.referenceDate })
  if (from && from > ctx.referenceDate) ctx.report('BPMN-F006', where, { datum: info.validFrom, stichtag: ctx.referenceDate })
}

function checkProfileFit(ctx: RuleContext, where: string | null, info: DiagramInfo): void {
  const profile = ctx.profile
  if (!profile) return
  for (const fund of info.funds ?? []) {
    if (!(profile.funds ?? []).includes(fund)) ctx.report('BPMN-F014', where, { wert: fund, profil: profile.id })
  }
  if (info.programmingPeriod && profile.programming_period && info.programmingPeriod !== profile.programming_period) {
    ctx.report('BPMN-F015', where, { wert: info.programmingPeriod, profil: profile.id, periode: profile.programming_period })
  }
  if (info.profile && info.profile !== profile.id) ctx.report('BPMN-F016', where, { wert: info.profile, profil: profile.id })
}

function checkStatus(ctx: RuleContext, where: string | null, info: DiagramInfo): void {
  if (!info.status) ctx.report('BPMN-F003', where)
  else if (!(info.status in DIAGRAM_STATUS)) ctx.report('BPMN-F004', where, { wert: info.status, zulaessig: Object.keys(DIAGRAM_STATUS).join(', ') })
  if (info.status === 'freigegeben' && !(info.approvedBy && info.approvedOn)) ctx.report('BPMN-F008', where)
}

function checkInfoValues(ctx: RuleContext, where: string | null, info: DiagramInfo): void {
  checkStatus(ctx, where, info)
  const colors: [string, string | undefined][] = [
    ['kopfzeilenfarbe', info.headerColor],
    ['kopfzeilen_textfarbe', info.headerTextColor],
  ]
  for (const [field, value] of colors) if (value && !COLOR.test(value)) ctx.report('BPMN-F013', where, { wert: value, feld: field })
  const coded: [string, string | undefined, Record<string, unknown>][] = [
    ['vertraulichkeit', info.confidentiality, CONFIDENTIALITY],
    ['variante', info.variant, VARIANTS],
  ]
  for (const [field, value, vocabulary] of coded) {
    if (value && !(value in vocabulary)) ctx.report('BPMN-F017', where, { wert: value, feld: field, zulaessig: Object.keys(vocabulary).join(', ') })
  }
  if (info.variant === 'ist' && !info.referenceDiagram) ctx.report('BPMN-F018', where)
}

function elements(ctx: RuleContext): void {
  const requiredFor = new Set(ctx.options.legalBasisRequiredFor ?? [...TASK_TYPES])
  for (const element of ctx.model.elements) checkElement(ctx, element, requiredFor)
}

function diagramInfo(ctx: RuleContext): void {
  const info = ctx.model.info
  if (!info) {
    ctx.report('BPMN-F002', null)
    return
  }
  const where = ctx.model.mainId
  checkInfoValues(ctx, where, info)
  checkDates(ctx, where, info)
  checkProfileFit(ctx, where, info)
  checkLegalBases(ctx, where, info.title || 'Diagramm', info.legalBases ?? [])
  checkAuditReferences(ctx, where, info.title || 'Diagramm', info.auditReferences ?? [])
}

export const DOMAIN_RULES = [elements, diagramInfo]
