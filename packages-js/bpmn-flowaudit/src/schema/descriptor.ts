/**
 * moddle descriptor of the `flowaudit` extension (schema 1.0 and 1.1).
 *
 * Namespace, prefix and `tagAlias` are unchanged since 1.0, so existing
 * diagrams with `<flowaudit:rechtsgrundlage>` and `<flowaudit:interneNotiz>`
 * keep loading. Types are generated from `spec.ts`.
 *
 * moddle writes child elements by their type name (with `tagAlias:
 * lowerCase`, `Schlagwort` becomes `<flowaudit:schlagwort>`) and resolves
 * them on read by property name first, then by type. List properties may
 * therefore carry a plural name and still read `<flowaudit:schlagwort>`.
 */

import { TEXT_TYPES, TYPES, type FieldSpec } from './spec'

export const FLOWAUDIT_NAMESPACE = 'https://flowaudit.de/bpmn/schema/1.0'
export const FLOWAUDIT_PREFIX = 'flowaudit'
export const FLOWAUDIT_SCHEMA_VERSION = '1.1'

interface ModdleProperty {
  name: string
  type: string
  isAttr?: boolean
  isBody?: boolean
  isMany?: boolean
}

interface ModdleType {
  name: string
  superClass: string[]
  properties: ModdleProperty[]
}

const PROPERTY_BUILDERS: Record<FieldSpec['kind'], (field: FieldSpec) => ModdleProperty> = {
  attr: (field) => ({ name: field.xml, type: 'String', isAttr: true }),
  list: (field) => ({ name: field.xml, type: 'String', isAttr: true }),
  // `value` as in the audit_designer descriptor (1.0).
  body: () => ({ name: 'value', type: 'String', isBody: true }),
  text: (field) => ({ name: field.xml, type: TEXT_TYPES[field.xml] }),
  texts: (field) => ({ name: field.key, type: TEXT_TYPES[field.xml], isMany: true }),
  elements: (field) => ({ name: field.key, type: TYPES[field.type as string].moddle, isMany: true }),
}

function buildTypes(): ModdleType[] {
  const structured = Object.values(TYPES).map((spec) => ({
    name: spec.moddle,
    superClass: ['Element'],
    properties: spec.fields.map((field) => PROPERTY_BUILDERS[field.kind](field)),
  }))
  const textTypes = Object.values(TEXT_TYPES).map((name) => ({
    name,
    superClass: ['Element'],
    properties: [{ name: 'value', type: 'String', isBody: true }],
  }))
  return [...structured, ...textTypes]
}

/** For `moddleExtensions: { flowaudit: flowauditModdleDescriptor }`. */
export const flowauditModdleDescriptor = {
  name: 'FlowAudit',
  uri: FLOWAUDIT_NAMESPACE,
  prefix: FLOWAUDIT_PREFIX,
  xml: { tagAlias: 'lowerCase' },
  associations: [] as unknown[],
  types: buildTypes(),
}

/** Type names as in the audit_designer (`flowauditModdle.ts`). */
export const TYPE_LEGAL_BASIS = 'flowaudit:Rechtsgrundlage'
export const TYPE_INTERNAL_NOTE = 'flowaudit:InterneNotiz'

/** Element types offering the 1.0 metadata (legal basis, internal note). */
export const METADATA_TYPES = [
  'bpmn:Task',
  'bpmn:UserTask',
  'bpmn:ManualTask',
  'bpmn:ServiceTask',
  'bpmn:ScriptTask',
  'bpmn:BusinessRuleTask',
  'bpmn:SendTask',
  'bpmn:ReceiveTask',
  'bpmn:SubProcess',
  'bpmn:CallActivity',
] as const
