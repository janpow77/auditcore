/**
 * Option lists for select fields: schema vocabularies, roles of the profile
 * and the KA catalogue (from the catalogue port if present, else profile).
 */

import { keyRequirements, label, localized, rolesFor, VOCABULARIES, type CataloguePort, type KeyRequirementEntry, type ProfileData, type VocabularyName } from '../index'
import type { FieldDescriptor } from './descriptors'
import type { Option } from './forms'

type Locale = 'de' | 'en'

/** KA catalogue of the profile (fallback without catalogue port). */
export function profileCatalogue(profile: ProfileData | null, locale: Locale): KeyRequirementEntry[] {
  return keyRequirements(profile).map((entry) => ({
    number: entry.number,
    title: localized(entry.title, locale),
    criteria: (entry.assessment_criteria ?? []).map((criterion) => ({ code: criterion.code, title: localized(criterion.title, locale) })),
  }))
}

/** KA catalogue from the port, falling back to the profile. */
export async function loadCatalogue(profile: ProfileData | null, locale: Locale, catalogue?: CataloguePort): Promise<KeyRequirementEntry[]> {
  const fallback = profileCatalogue(profile, locale)
  if (!catalogue || !profile) return fallback
  try {
    return await catalogue.keyRequirements(profile.id, locale)
  } catch {
    return fallback
  }
}

export const roleOptions = (profile: ProfileData | null, locale: Locale): Option[] => rolesFor(profile).map((role) => ({ value: role.code, label: `${role.short} – ${label(role.label, locale)}` }))
export const kaOptions = (entries: KeyRequirementEntry[]): Option[] => entries.map((entry) => ({ value: String(entry.number), label: `KA ${entry.number} – ${entry.title}` }))

export function vocabularyOptions(name: string | undefined, locale: Locale): Option[] {
  const vocabulary = name ? VOCABULARIES[name as VocabularyName] : undefined
  return Object.entries(vocabulary ?? {}).map(([value, text]) => ({ value, label: label(text, locale) }))
}

/** Options resolver for `FieldForm` from roles, KA catalogue and vocabularies. */
export function optionsResolver(roles: Option[], ka: Option[], locale: Locale): (field: FieldDescriptor) => Option[] {
  return (field) => (field.options === 'roles' ? roles : field.options === 'keyRequirements' ? ka : vocabularyOptions(field.options, locale))
}
