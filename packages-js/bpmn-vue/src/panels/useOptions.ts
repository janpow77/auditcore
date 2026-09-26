/**
 * Option lists for select fields: schema vocabularies, roles of the profile
 * and the KA catalogue (from the catalogue port if present, else profile).
 * The lists come from the framework-free UI core.
 */

import { computed, ref, watchEffect, type Ref } from 'vue'
import { kaOptions, loadCatalogue, optionsResolver, profileCatalogue, roleOptions, type Option } from '@auditcore/bpmn-flowaudit/ui'
import type { CataloguePort, KeyRequirementEntry, ProfileData } from '@auditcore/bpmn-flowaudit'
import type { FieldDescriptor } from '@auditcore/bpmn-flowaudit/ui'

export type { Option } from '@auditcore/bpmn-flowaudit/ui'

export interface OptionSources {
  profile: () => ProfileData | null
  catalogue?: CataloguePort
  locale: Ref<'de' | 'en'>
}

export function useKeyRequirementCatalogue(sources: OptionSources): Ref<KeyRequirementEntry[]> {
  const entries = ref<KeyRequirementEntry[]>([])
  watchEffect(async () => {
    const profile = sources.profile()
    const locale = sources.locale.value
    entries.value = profileCatalogue(profile, locale)
    if (sources.catalogue && profile) entries.value = await loadCatalogue(profile, locale, sources.catalogue)
  })
  return entries
}

export function useOptions(sources: OptionSources) {
  const catalogue = useKeyRequirementCatalogue(sources)
  const roles = computed<Option[]>(() => roleOptions(sources.profile(), sources.locale.value))
  const ka = computed<Option[]>(() => kaOptions(catalogue.value))
  const resolver = computed(() => optionsResolver(roles.value, ka.value, sources.locale.value))
  const optionsFor = (field: FieldDescriptor): Option[] => resolver.value(field)
  return { optionsFor, roleOptions: roles, kaOptions: ka, catalogue }
}
