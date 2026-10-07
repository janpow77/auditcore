/**
 * Property definitions of a profile: name/value properties that the
 * properties panel offers per element (stored as `camunda:property`, see
 * `model/camundaProperties.ts`). The profile names the properties, their
 * kind and value lists; the library knows no fixed list.
 *
 * Profile block (JSON, snake_case like the rest of `auditcore_bpmn.profile/1`):
 *
 *   "properties": {
 *     "title": { "de": "Prüfungsmerkmale" },
 *     "entries": [
 *       { "name": "pb_art", "label": { "de": "Art der Prüfungshandlung" },
 *         "kind": "choice", "values": ["Planung", "Durchlauftest", …] },
 *       { "name": "pb_coso", "label": { "de": "COSO-Komponente" }, "kind": "multi_choice",
 *         "values": […], "depends_on": { "property": "pb_art", "values": ["Durchlauftest", "Kontrolltest"] } },
 *       { "name": "pb_gj", "label": { "de": "Geschäftsjahr" }, "kind": "text", "applies_to": ["event"] }
 *     ]
 *   }
 */

import { isActivity, isEvent, isGateway } from '../model/processModel'
import type { Locale } from '../schema/vocabulary'
import { localized, type LocalizedText, type ProfileData } from './profile'

export type PropertyKind = 'text' | 'choice' | 'multi_choice' | 'yes_no'

export interface PropertyOptionData {
  value: string
  label?: LocalizedText
}

export interface PropertyConditionData {
  /** Name of the property the condition looks at. */
  property: string
  /** The definition applies if that property holds one of these values. */
  values: string[]
}

export interface PropertyDefinitionData {
  name: string
  label: LocalizedText
  kind: PropertyKind
  /** Value list (`choice`, `multi_choice`); for `yes_no` the first value is stored for “yes” (default `ja`). */
  values?: (string | PropertyOptionData)[]
  /**
   * Element kinds: `activity`, `event`, `gateway`, `data`, `participant`,
   * `lane`, `process`, `sequence_flow` or a BPMN type such as `bpmn:Task`.
   * Default: activities.
   */
  applies_to?: string[]
  help?: LocalizedText
  depends_on?: PropertyConditionData
  /** Separator of several values (default `;`). */
  separator?: string
}

export interface PropertyCatalogue {
  title?: LocalizedText
  source?: Record<string, unknown>
  entries: PropertyDefinitionData[]
}

export interface PropertyOption {
  value: string
  label: string
}

const DATA_TYPES = ['bpmn:DataObjectReference', 'bpmn:DataStoreReference', 'bpmn:DataObject', 'bpmn:DataStore']
const KIND_TESTS: Record<string, (type: string) => boolean> = {
  activity: isActivity,
  event: isEvent,
  gateway: isGateway,
  data: (type) => DATA_TYPES.includes(type),
  participant: (type) => type === 'bpmn:Participant',
  lane: (type) => type === 'bpmn:Lane',
  process: (type) => type === 'bpmn:Process',
  sequence_flow: (type) => type === 'bpmn:SequenceFlow',
}

export function propertyDefinitions(profile: ProfileData | null | undefined): PropertyDefinitionData[] {
  return (profile?.properties?.entries ?? []).filter((entry) => entry && entry.name)
}

export function propertyAppliesTo(definition: PropertyDefinitionData, type: string): boolean {
  const kinds = definition.applies_to?.length ? definition.applies_to : ['activity']
  return kinds.some((kind) => (KIND_TESTS[kind] ? KIND_TESTS[kind](type) : kind === type))
}

/** Definitions offered for an element type. */
export function propertyDefinitionsFor(profile: ProfileData | null | undefined, type: string | null | undefined): PropertyDefinitionData[] {
  return type ? propertyDefinitions(profile).filter((definition) => propertyAppliesTo(definition, type)) : []
}

export function propertySeparator(definition: PropertyDefinitionData): string {
  return definition.separator || ';'
}

/** `"a; b;"` → `['a', 'b']`. */
export function splitPropertyValue(value: string | undefined, separator = ';'): string[] {
  return (value ?? '')
    .split(separator)
    .map((part) => part.trim())
    .filter(Boolean)
}

export function propertyOptions(definition: PropertyDefinitionData, locale: Locale = 'de'): PropertyOption[] {
  return (definition.values ?? []).map((entry) =>
    typeof entry === 'string' ? { value: entry, label: entry } : { value: entry.value, label: localized(entry.label, locale) || entry.value },
  )
}

/** Value stored for “yes” of a `yes_no` property. */
export function yesValue(definition: PropertyDefinitionData): string {
  const [first] = propertyOptions(definition)
  return first?.value ?? 'ja'
}

/** Whether the condition of a definition holds for the current values (no condition: always). */
export function propertyActive(definition: PropertyDefinitionData, values: Record<string, string>, all: PropertyDefinitionData[] = []): boolean {
  const condition = definition.depends_on
  if (!condition) return true
  const base = all.find((entry) => entry.name === condition.property)
  const current = splitPropertyValue(values[condition.property], base ? propertySeparator(base) : ';')
  return current.some((value) => condition.values.includes(value))
}
