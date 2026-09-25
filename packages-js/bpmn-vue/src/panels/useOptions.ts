/**
 * Option lists for select fields: schema vocabularies, roles of the profile
 * and the KA catalogue (from the catalogue port if present, else profile).
 */

import { computed, ref, watchEffect, type Ref } from 'vue'
import {
  VOCABULARIES,
  keyRequirements,
  label,
  localized,
  rolesFor,
  type CataloguePort,
  type KeyRequirementEntry,
  type ProfileData,
  type VocabularyName,
} from '@flowaudit/bpmn-flowaudit'
import type { FieldDescriptor } from './descriptors'

export interface Option {
  value: string
  label: string
}

export interface OptionSources {
  profile: () => ProfileData | null
  catalogue?: CataloguePort
  locale: Ref<'de' | 'en'>
}

export function useKeyRequirementCatalogue(sources: OptionSources): Ref<KeyRequirementEntry[]> {
  const entries = ref<KeyRequirementEntry[]>([])
  watchEffect(async () => {
    const profile = sources.profile()
    const fallback = keyRequirements(profile).map((entry) => ({
      number: entry.number,
      title: localized(entry.title, sources.locale.value),
      criteria: (entry.assessment_criteria ?? []).map((criterion) => ({ code: criterion.code, title: localized(criterion.title, sources.locale.value) })),
    }))
    entries.value = fallback
    if (sources.catalogue && profile) {
      try {
        entries.value = await sources.catalogue.keyRequirements(profile.id, sources.locale.value)
      } catch {
        entries.value = fallback
      }
    }
  })
  return entries
}

export function useOptions(sources: OptionSources) {
  const catalogue = useKeyRequirementCatalogue(sources)
  const roleOptions = computed<Option[]>(() => rolesFor(sources.profile()).map((role) => ({ value: role.code, label: `${role.short} – ${label(role.label, sources.locale.value)}` })))
  const kaOptions = computed<Option[]>(() => catalogue.value.map((entry) => ({ value: String(entry.number), label: `KA ${entry.number} – ${entry.title}` })))

  function optionsFor(field: FieldDescriptor): Option[] {
    if (field.options === 'roles') return roleOptions.value
    if (field.options === 'keyRequirements') return kaOptions.value
    const vocabulary = field.options ? VOCABULARIES[field.options as VocabularyName] : undefined
    return Object.entries(vocabulary ?? {}).map(([value, text]) => ({ value, label: label(text, sources.locale.value) }))
  }

  return { optionsFor, roleOptions, kaOptions, catalogue }
}
