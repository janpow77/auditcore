/**
 * Form model of the “audit attributes” tab: one field per property
 * definition of the profile that applies to the element type, with the
 * current values of the element. Shared by the Vue and React panels.
 */

import {
  propertyActive,
  propertyDefinitionsFor,
  propertyOptions,
  propertySeparator,
  splitPropertyValue,
  yesValue,
  localized,
  type Locale,
  type NamedProperty,
  type ProfileData,
  type PropertyDefinitionData,
  type PropertyKind,
  type PropertyPatch,
} from '../index'

export interface PropertyFieldOption {
  value: string
  label: string
  /** `false` for a stored value that is not in the profile's list. */
  known: boolean
}

export interface PropertyField {
  name: string
  label: string
  help: string
  kind: PropertyKind
  options: PropertyFieldOption[]
  /** Current values (split for `multi_choice`). */
  selected: string[]
  text: string
  /** `false` if the condition (`depends_on`) does not hold. */
  active: boolean
  separator: string
  /** Value stored for “yes” (`yes_no`). */
  yes: string
}

function valueMap(entries: NamedProperty[]): Record<string, string> {
  const values: Record<string, string> = {}
  for (const entry of entries) if (!(entry.name in values)) values[entry.name] = entry.value
  return values
}

function fieldOptions(definition: PropertyDefinitionData, selected: string[], locale: Locale): PropertyFieldOption[] {
  const options = propertyOptions(definition, locale).map((option) => ({ ...option, known: true }))
  const unknown = selected.filter((value) => !options.some((option) => option.value === value))
  return [...options, ...unknown.map((value) => ({ value, label: value, known: false }))]
}

function toField(definition: PropertyDefinitionData, values: Record<string, string>, all: PropertyDefinitionData[], locale: Locale): PropertyField {
  const text = values[definition.name] ?? ''
  const separator = propertySeparator(definition)
  const selected = definition.kind === 'multi_choice' ? splitPropertyValue(text, separator) : text.trim() ? [text.trim()] : []
  return {
    name: definition.name,
    label: localized(definition.label, locale) || definition.name,
    help: localized(definition.help, locale),
    kind: definition.kind,
    options: definition.kind === 'text' ? [] : fieldOptions(definition, selected, locale),
    selected,
    text,
    active: propertyActive(definition, values, all),
    separator,
    yes: yesValue(definition),
  }
}

export function propertyFields(profile: ProfileData | null | undefined, type: string | null | undefined, entries: NamedProperty[], locale: Locale = 'de'): PropertyField[] {
  const definitions = propertyDefinitionsFor(profile, type)
  const values = valueMap(entries)
  return definitions.map((definition) => toField(definition, values, definitions, locale))
}

/** Patch for a text or single choice (empty removes the property). */
export function textPatch(field: PropertyField, value: string): PropertyPatch {
  return { [field.name]: value.trim() }
}

/** Patch after toggling one value of a `multi_choice` (order follows the option list). */
export function togglePatch(field: PropertyField, value: string): PropertyPatch {
  const chosen = new Set(field.selected)
  if (chosen.has(value)) chosen.delete(value)
  else chosen.add(value)
  const ordered = field.options.map((option) => option.value).filter((option) => chosen.has(option))
  return { [field.name]: ordered.join(field.separator) }
}

/** Patch for a `yes_no` property: “no” removes the property. */
export function yesNoPatch(field: PropertyField, yes: boolean): PropertyPatch {
  return { [field.name]: yes ? field.yes : '' }
}

/** Whether a `yes_no` field is set (its stored value equals the “yes” value). */
export function isYes(field: PropertyField): boolean {
  return field.selected[0] === field.yes
}
