/**
 * Declarative field descriptions of the properties panel. Each list type
 * of the FlowAudit schema is described once; `ListEditor` and `FieldForm`
 * render them. No hand-written form per extension type.
 */

import {
  deadlineText,
  displayText,
  type AuditFinding,
  type AuditReference,
  type AuditStep,
  type Control,
  type CrossReference,
  type Deadline,
  type Evidence,
  type ListExtensionKey,
  type Risk,
  type Source,
  type VocabularyName,
} from '@flowaudit/bpmn-flowaudit'

export type FieldKind = 'text' | 'textarea' | 'select' | 'checkbox' | 'date' | 'number' | 'tokens'

export interface FieldDescriptor {
  key: string
  /** i18n key of the label. */
  label: string
  kind: FieldKind
  /** Options: a vocabulary of the schema, the roles or the KA catalogue. */
  options?: VocabularyName | 'roles' | 'keyRequirements'
  wide?: boolean
  placeholder?: string
}

export interface ListDescriptor<T = Record<string, unknown>> {
  key: ListExtensionKey
  title: string
  fields: FieldDescriptor[]
  summary: (item: T) => string
  /** i18n keys of badges shown next to the summary. */
  badges?: (item: T) => string[]
  create: () => T
}

const f = (key: string, kind: FieldKind = 'text', extra: Partial<FieldDescriptor> = {}): FieldDescriptor => ({ key, label: `field.${key}`, kind, ...extra })
const confidential = f('confidential', 'checkbox', { wide: true })
const join = (...parts: (string | undefined)[]) => parts.filter(Boolean).join(' · ')

export const AUDIT_REFERENCE_LIST: ListDescriptor<AuditReference> = {
  key: 'auditReferences',
  title: 'props.auditReferences',
  fields: [f('keyRequirement', 'select', { options: 'keyRequirements' }), f('assessmentCriterion', 'text', { placeholder: 'z. B. 2.3' }), f('auditType', 'select', { options: 'auditTypes' }), f('note', 'text'), confidential],
  summary: (r) => join(r.keyRequirement ? `KA ${r.keyRequirement}` : undefined, r.assessmentCriterion ? `BK ${r.assessmentCriterion}` : undefined),
  create: () => ({ keyRequirement: '' }),
}

export const CROSS_REFERENCE_LIST: ListDescriptor<CrossReference> = {
  key: 'crossReferences',
  title: 'props.crossReferences',
  fields: [f('kind', 'select', { options: 'crossReferenceKinds' }), f('key'), f('document', 'text', { wide: true }), confidential],
  summary: (r) => join(r.key, r.document),
  create: () => ({ kind: 'prueffeld' }),
}

export const CONTROL_LIST: ListDescriptor<Control> = {
  key: 'controls',
  title: 'props.controls',
  fields: [
    f('id'),
    f('label'),
    f('keyControl', 'checkbox', { wide: true }),
    f('controlType', 'select', { options: 'controlTypes' }),
    f('execution', 'select', { options: 'executionModes' }),
    f('frequency'),
    f('responsible', 'select', { options: 'roles' }),
    f('evidence', 'text', { wide: true }),
    f('description', 'textarea', { wide: true }),
    confidential,
  ],
  summary: (c) => join(c.id, c.label),
  badges: (c) => (c.keyControl ? ['field.keyControl'] : []),
  create: () => ({ id: '' }),
}

export const RISK_LIST: ListDescriptor<Risk> = {
  key: 'risks',
  title: 'props.risks',
  fields: [
    f('id'),
    f('label'),
    f('category', 'select', { options: 'riskCategories' }),
    f('inherent', 'select', { options: 'riskLevels' }),
    f('controlRisk', 'select', { options: 'riskLevels' }),
    f('residual', 'select', { options: 'riskLevels' }),
    f('controls', 'tokens', { wide: true, placeholder: 'K1 K2' }),
    f('description', 'textarea', { wide: true }),
    confidential,
  ],
  summary: (r) => join(r.id, r.label, r.inherent),
  create: () => ({ id: '' }),
}

export const EVIDENCE_LIST: ListDescriptor<Evidence> = {
  key: 'evidence',
  title: 'props.evidence',
  fields: [f('documentType'), f('storageLocation'), f('itSystem'), f('retentionPeriod'), f('note', 'text', { wide: true }), confidential],
  summary: (e) => join(e.documentType, e.storageLocation),
  create: () => ({}),
}

export const DEADLINE_LIST: ListDescriptor<Deadline> = {
  key: 'deadlines',
  title: 'props.deadlines',
  fields: [f('value'), f('unit', 'select', { options: 'deadlineUnits' }), f('basis', 'text', { wide: true }), f('note', 'text', { wide: true })],
  summary: (d) => join(deadlineText(d), (d.legalBases ?? []).map(displayText).join('; ')),
  create: () => ({ unit: 'tage' }),
}

export const FINDING_LIST: ListDescriptor<AuditFinding> = {
  key: 'findings',
  title: 'props.findings',
  fields: [
    f('reference'),
    f('id'),
    f('findingType', 'select', { options: 'findingTypes' }),
    f('severity', 'select', { options: 'findingSeverities' }),
    f('keyRequirement', 'select', { options: 'keyRequirements' }),
    f('assessmentCriterion'),
    f('deadline', 'date'),
    f('status', 'select', { options: 'findingStatus' }),
    f('description', 'textarea', { wide: true }),
    f('recommendation', 'textarea', { wide: true }),
    confidential,
  ],
  summary: (x) => join(x.reference || x.id, x.findingType, x.severity, x.status),
  create: () => ({ status: 'offen' }),
}

export const AUDIT_STEP_LIST: ListDescriptor<AuditStep> = {
  key: 'auditSteps',
  title: 'props.auditSteps',
  fields: [
    f('id'),
    f('case'),
    { ...f('document'), label: 'field.voucher' },
    f('result', 'select', { options: 'testResults' }),
    f('date', 'date'),
    f('tester'),
    f('control'),
    f('sampleSize', 'number'),
    f('population', 'number'),
    f('remark', 'textarea', { wide: true }),
    confidential,
  ],
  summary: (s) => join(s.id, s.case, s.result),
  create: () => ({ result: 'offen' }),
}

export const SOURCE_LIST: ListDescriptor<Source> = {
  key: 'sources',
  title: 'props.sources',
  fields: [f('sourceType', 'select', { options: 'sourceTypes' }), f('date', 'date'), f('location', 'text', { wide: true }), f('reference', 'text', { wide: true }), f('text', 'textarea', { wide: true }), confidential],
  summary: (s) => join(s.location, s.date),
  create: () => ({ sourceType: 'verfahrenshandbuch' }),
}

export const LISTS: Record<string, ListDescriptor> = Object.fromEntries(
  [AUDIT_REFERENCE_LIST, CROSS_REFERENCE_LIST, CONTROL_LIST, RISK_LIST, EVIDENCE_LIST, DEADLINE_LIST, FINDING_LIST, AUDIT_STEP_LIST, SOURCE_LIST].map((list) => [
    list.key,
    list as unknown as ListDescriptor,
  ]),
)
