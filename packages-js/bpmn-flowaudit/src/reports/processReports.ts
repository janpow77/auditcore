/**
 * Report exports for audit authorities (same content as `auditcore_bpmn`
 * reports): process table, risk-control matrix, findings list and
 * walk-through overview.
 */

import { displayText } from '../model/legalBasis'
import { displayName, isActivity, isFlowNode, localType, type ModelElement, type ProcessModel } from '../model/processModel'
import { ROLES } from '../schema/roles'
import type { Control, Deadline, Risk } from '../schema/types'
import { label } from '../schema/vocabulary'
import type { Columns, Row } from './tables'

/** Flow nodes in flow order (breadth-first from start events), rest afterwards. */
export function flowOrder(model: ProcessModel): ModelElement[] {
  const nodes = model.elements.filter((el) => isFlowNode(el.type))
  const flows = model.elements.filter((el) => el.type === 'bpmn:SequenceFlow')
  const hasIncoming = new Set(flows.map((flow) => flow.targetId))
  const queue = nodes.filter((node) => localType(node.type) === 'startEvent' && !hasIncoming.has(node.id)).map((node) => node.id)
  const seen = new Map<string, ModelElement>()
  while (queue.length) {
    const id = queue.shift() as string
    const element = model.byId.get(id)
    if (seen.has(id) || !element || !isFlowNode(element.type)) continue
    seen.set(id, element)
    queue.push(...flows.filter((flow) => flow.sourceId === id && flow.targetId).map((flow) => flow.targetId as string))
  }
  return [...seen.values(), ...nodes.filter((node) => !seen.has(node.id))]
}

export function actorLabel(element: ModelElement): string {
  const actor = element.actor
  if (!actor?.role) return actor?.sourceName ?? ''
  const role = ROLES[actor.role]
  const roleLabel = role ? label(role.label) : actor.role
  return actor.displayName ? `${roleLabel} (${actor.displayName})` : roleLabel
}

export function deadlineText(deadline: Deadline): string {
  const text = [deadline.value, deadline.unit].filter(Boolean).join(' ')
  return text + (deadline.basis ? ` (${deadline.basis})` : '')
}

function controlText(control: Control): string {
  return (control.label || control.id || 'Kontrolle') + (control.keyControl ? ' (Schlüsselkontrolle)' : '')
}

function evidenceOf(model: ProcessModel, element: ModelElement): { evidence: string[]; systems: string[] } {
  const data = (element.dataObjects ?? []).map((id) => model.byId.get(id)).filter((el): el is ModelElement => Boolean(el))
  const evidence = element.extensions.controls.map((c) => c.evidence).filter((e): e is string => Boolean(e))
  for (const item of data) {
    const places = item.extensions.evidence.map((e) => e.storageLocation).filter(Boolean)
    evidence.push(displayName(item) + (places.length ? ` (${places.join(', ')})` : ''))
  }
  const systems = new Set<string>([
    ...data.flatMap((item) => item.extensions.evidence.map((e) => e.itSystem).filter((s): s is string => Boolean(s))),
    ...element.extensions.markers.filter((m) => m.type === 'system' && m.text).map((m) => m.text as string),
  ])
  return { evidence, systems: [...systems].sort() }
}

export const PROCESS_TABLE_COLUMNS: Columns = {
  nr: 'Nr.',
  schritt: 'Schritt',
  akteur: 'Akteur',
  rechtsgrundlage: 'Rechtsgrundlage',
  kontrolle: 'Kontrolle',
  nachweis: 'Nachweis',
  it_system: 'IT-System',
  frist: 'Frist',
  ka_bk: 'KA/BK',
}

/** Process description in flow order. */
export function processTable(model: ProcessModel, options: { activitiesOnly?: boolean } = {}): Row[] {
  const onlyActivities = options.activitiesOnly ?? true
  return flowOrder(model)
    .filter((element) => !onlyActivities || isActivity(element.type))
    .map((element, index) => {
      const ext = element.extensions
      const { evidence, systems } = evidenceOf(model, element)
      return {
        nr: index + 1,
        schritt: displayName(element),
        typ: localType(element.type),
        akteur: actorLabel(element),
        rechtsgrundlage: ext.legalBases.map(displayText).join('; '),
        kontrolle: ext.controls.map(controlText).join('; '),
        nachweis: evidence.filter(Boolean).join('; '),
        it_system: systems.join('; '),
        frist: ext.deadlines.map(deadlineText).join('; '),
        ka_bk: ext.auditReferences
          .map((ref) => [ref.keyRequirement ? `KA ${ref.keyRequirement}` : '', ref.assessmentCriterion ? `BK ${ref.assessmentCriterion}` : ''].filter(Boolean).join(' · '))
          .join('; '),
        element_id: element.id,
      }
    })
}

function riskRows(place: string, risk: Risk, controls: Map<string, [ModelElement, Control]>, tests: Map<string, string[]>): Row[] {
  const base = {
    risiko_id: risk.id ?? '',
    risiko: risk.label ?? '',
    kategorie: risk.category ?? '',
    inhaerent: risk.inherent ?? '',
    kontrollrisiko: risk.controlRisk ?? '',
    restrisiko: risk.residual ?? '',
    ort: place,
  }
  if (!(risk.controls ?? []).length) {
    return [{ ...base, kontrolle_id: '', kontrolle: '', schluesselkontrolle: '', art: '', durchfuehrung: '', haeufigkeit: '', nachweis: '', verantwortlich: '', test: '' }]
  }
  return (risk.controls ?? []).map((controlId) => {
    const [element, control] = controls.get(controlId) ?? [undefined, undefined]
    return {
      ...base,
      kontrolle_id: controlId,
      kontrolle: control ? control.label ?? '' : '(unbekannt)',
      schluesselkontrolle: control?.keyControl ? 'ja' : 'nein',
      art: control?.controlType ?? '',
      durchfuehrung: control?.execution ?? '',
      haeufigkeit: control?.frequency ?? '',
      nachweis: control?.evidence ?? '',
      verantwortlich: control?.responsible ?? '',
      test: (tests.get(controlId) ?? []).join(', '),
      ort: element ? displayName(element) : place,
    }
  })
}

/** One row per risk and linked control (risks without control once). */
export function riskControlMatrix(model: ProcessModel): Row[] {
  const controls = new Map<string, [ModelElement, Control]>()
  const tests = new Map<string, string[]>()
  for (const element of model.elements) {
    for (const control of element.extensions.controls) if (control.id) controls.set(control.id, [element, control])
    for (const step of element.extensions.auditSteps) if (step.control) tests.set(step.control, [...(tests.get(step.control) ?? []), step.result || 'offen'])
  }
  const risks: [string, Risk][] = model.elements.flatMap((element) => element.extensions.risks.map((risk): [string, Risk] => [displayName(element), risk]))
  for (const risk of model.info?.risks ?? []) risks.push(['Diagramm', risk])
  return risks.flatMap(([place, risk]) => riskRows(place, risk, controls, tests))
}

export function findingsList(model: ProcessModel): Row[] {
  const items: [string, string, ModelElement['extensions']['findings'][number]][] = model.elements.flatMap((element) =>
    element.extensions.findings.map((finding): [string, string, typeof finding] => [element.id, displayName(element), finding]),
  )
  for (const finding of model.info?.findings ?? []) items.push([model.mainId ?? '', 'Diagramm', finding])
  return items.map(([elementId, name, f]) => ({
    id: f.id ?? '',
    kennung: f.reference ?? '',
    element: name,
    element_id: elementId,
    art: f.findingType ?? '',
    einstufung: f.severity ?? '',
    ka: f.keyRequirement ?? '',
    bk: f.assessmentCriterion ?? '',
    beschreibung: f.description ?? '',
    empfehlung: f.recommendation ?? '',
    frist: f.deadline ?? '',
    status: f.status ?? '',
  }))
}

export interface WalkthroughOverview {
  results: Record<string, number>
  steps: Row[]
  notWalkedThrough: string[]
}

/** Audit steps per flow node; activities without steps separately. */
export function walkthroughOverview(model: ProcessModel): WalkthroughOverview {
  const results: Record<string, number> = {}
  const steps: Row[] = []
  const notWalkedThrough: string[] = []
  for (const element of flowOrder(model)) {
    const list = element.extensions.auditSteps
    if (!list.length && isActivity(element.type)) notWalkedThrough.push(element.id)
    for (const step of list) {
      const result = step.result || 'offen'
      results[result] = (results[result] ?? 0) + 1
      steps.push({
        element: displayName(element),
        element_id: element.id,
        fall: step.case ?? '',
        beleg: step.document ?? '',
        ergebnis: result,
        datum: step.date ?? '',
        kontrolle: step.control ?? '',
        stichprobe: step.sampleSize ?? '',
        bemerkung: step.remark ?? '',
      })
    }
  }
  return { results, steps, notWalkedThrough }
}
