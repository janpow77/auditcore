/**
 * Version comparison, target/actual check and diff colours.
 *
 * - `compareVersions` – element-wise difference of two versions (added,
 *   removed, changed) with synopsis rows.
 * - `checkTargetActual` – per target element a binary result met/not met
 *   with reasons (walk-through against the description of the MCS).
 */

import { displayName, isFlowNode, localType, type ProcessModel } from '../model/processModel'
import { MARKER_COLOR_PRECEDENCE, MARKER_COLORS } from '../schema/vocabulary'
import { bodyLabel, comparable, features, matchElements, neighbours, type Features } from './matching'

export type ChangeKind = 'hinzugefuegt' | 'entfallen' | 'geaendert' | 'unveraendert'

export interface FieldChange {
  field: keyof Features
  before: unknown
  after: unknown
}

export interface Change {
  kind: ChangeKind
  type: string
  name: string
  oldId?: string
  newId?: string
  fields: FieldChange[]
}

export interface Comparison {
  changes: Change[]
}

export const DIFF_COLORS: Record<'hinzugefuegt' | 'entfallen' | 'geaendert', { fill: string; stroke: string }> = {
  hinzugefuegt: { fill: '#e6f4ea', stroke: '#1e8e3e' },
  entfallen: { fill: '#fce8e6', stroke: '#b3261e' },
  geaendert: { fill: '#fef7e0', stroke: '#e37400' },
}

function differences(before: Features, after: Features): FieldChange[] {
  return (Object.keys(before) as (keyof Features)[])
    .filter((key) => JSON.stringify(before[key]) !== JSON.stringify(after[key]))
    .map((field) => ({ field, before: before[field], after: after[field] }))
}

/** Element-wise comparison of two versions of the same diagram. */
export function compareVersions(before: ProcessModel, after: ProcessModel): Comparison {
  const mapping = matchElements(before, after)
  const changes: Change[] = []
  for (const element of comparable(before)) {
    const partner = after.byId.get(mapping.get(element.id) ?? '')
    if (!partner) {
      changes.push({ kind: 'entfallen', type: localType(element.type), name: displayName(element), oldId: element.id, fields: [] })
      continue
    }
    const fields = differences(features(before, element), features(after, partner))
    changes.push({ kind: fields.length ? 'geaendert' : 'unveraendert', type: localType(partner.type), name: displayName(partner), oldId: element.id, newId: partner.id, fields })
  }
  const matched = new Set(mapping.values())
  for (const element of comparable(after).filter((el) => !matched.has(el.id))) {
    changes.push({ kind: 'hinzugefuegt', type: localType(element.type), name: displayName(element), newId: element.id, fields: [] })
  }
  return { changes }
}

export function isUnchanged(comparison: Comparison): boolean {
  return comparison.changes.every((change) => change.kind === 'unveraendert')
}

const CHANGE_LABELS: Record<ChangeKind, string> = { hinzugefuegt: 'hinzugefügt', entfallen: 'entfallen', geaendert: 'geändert', unveraendert: 'unverändert' }

export function changeLabel(kind: ChangeKind): string {
  return CHANGE_LABELS[kind]
}

export function valueText(value: unknown): string {
  if (Array.isArray(value)) return value.map(String).join(', ')
  if (value && typeof value === 'object') return Object.entries(value).map(([key, item]) => `${key}: ${JSON.stringify(item)}`).join('; ')
  return value === null || value === undefined ? '' : String(value)
}

export interface SynopsisRow {
  element: string
  field: string
  before: string
  after: string
  change: string
}

/** Rows „element | before | after | change“ for reports. */
export function synopsis(comparison: Comparison): SynopsisRow[] {
  return comparison.changes.flatMap((change): SynopsisRow[] => {
    if (change.kind === 'unveraendert') return []
    if (change.kind === 'geaendert') {
      return change.fields.map((f) => ({ element: change.name, field: f.field, before: valueText(f.before), after: valueText(f.after), change: CHANGE_LABELS.geaendert }))
    }
    const removed = change.kind === 'entfallen'
    return [{ element: change.name, field: '', before: removed ? change.name : '', after: removed ? '' : change.name, change: CHANGE_LABELS[change.kind] }]
  })
}

/** Colours for the graphical diff: `[before, after]` by element id. */
export function diffColors(comparison: Comparison): [Map<string, ChangeKind>, Map<string, ChangeKind>] {
  const before = new Map<string, ChangeKind>()
  const after = new Map<string, ChangeKind>()
  for (const change of comparison.changes) {
    if (change.kind === 'entfallen' && change.oldId) before.set(change.oldId, 'entfallen')
    if (change.kind === 'hinzugefuegt' && change.newId) after.set(change.newId, 'hinzugefuegt')
    if (change.kind === 'geaendert' && change.oldId && change.newId) {
      before.set(change.oldId, 'geaendert')
      after.set(change.newId, 'geaendert')
    }
  }
  return [before, after]
}

// ---------------------------------------------------------------------------
// Target/actual check
// ---------------------------------------------------------------------------

export interface TargetActualResult {
  targetId: string
  name: string
  met: boolean
  actualId?: string
  reasons: string[]
}

export interface TargetActualCheck {
  results: TargetActualResult[]
  additionalInActual: string[]
  met: number
  notMet: number
}

function reasonsFor(target: ProcessModel, actual: ProcessModel, targetId: string, actualId: string): string[] {
  const element = target.byId.get(targetId)
  const partner = actual.byId.get(actualId)
  if (!element || !partner) return ['Im Ist nicht vorhanden.']
  const reasons: string[] = []
  if (partner.type !== element.type) reasons.push(`Elementtyp abweichend: Soll ${localType(element.type)}, Ist ${localType(partner.type)}.`)
  const want = bodyLabel(element)
  const have = bodyLabel(partner)
  if (want && want !== have) reasons.push(`Andere Stelle: Soll „${want}“, Ist „${have ?? '–'}“.`)
  const missing = element.extensions.controls
    .filter((c) => !partner.extensions.controls.some((x) => (x.id && x.id === c.id) || (x.label && x.label === c.label)))
    .map((c) => c.label || c.id || 'Kontrolle')
  if (missing.length) reasons.push(`Kontrolle fehlt im Ist: ${missing.join(', ')}.`)
  const have2 = new Set(neighbours(actual, partner, 'out'))
  const lacking = neighbours(target, element, 'out').filter((name) => !have2.has(name))
  if (lacking.length) reasons.push(`Nachfolger fehlen im Ist: ${[...new Set(lacking)].sort().join(', ')}.`)
  if (partner.extensions.auditSteps.some((step) => step.result === 'nicht_erfuellt')) reasons.push('Prüfschritt im Ist nicht erfüllt.')
  return reasons
}

/**
 * Per activity, gateway and event of the target: present in the actual
 * state, same body, controls and successors. „Met“ is binary; the reasons
 * name each deviation. A working aid – the assessment stays with the auditor.
 */
export function checkTargetActual(target: ProcessModel, actual: ProcessModel): TargetActualCheck {
  const mapping = matchElements(target, actual)
  const results = target.elements
    .filter((element) => isFlowNode(element.type))
    .map((element): TargetActualResult => {
      const actualId = mapping.get(element.id)
      const reasons = actualId ? reasonsFor(target, actual, element.id, actualId) : ['Im Ist nicht vorhanden.']
      return { targetId: element.id, name: displayName(element), met: reasons.length === 0, ...(actualId ? { actualId } : {}), reasons }
    })
  const matched = new Set(mapping.values())
  const additionalInActual = actual.elements.filter((el) => isFlowNode(el.type) && !matched.has(el.id)).map((el) => el.id)
  const met = results.filter((result) => result.met).length
  return { results, additionalInActual, met, notMet: results.length - met }
}

/** Fill and stroke per element from colouring markers (precedence as in the schema). */
export function colorsFromMarkers(model: ProcessModel): Map<string, { fill: string; stroke: string }> {
  const result = new Map<string, { fill: string; stroke: string }>()
  for (const element of model.elements) {
    const types = new Set(element.extensions.markers.map((marker) => marker.type))
    const winner = MARKER_COLOR_PRECEDENCE.find((type) => types.has(type))
    const color = winner ? MARKER_COLORS[winner] : undefined
    if (color) result.set(element.id, color)
  }
  return result
}
