/**
 * Option lists for select fields (vocabularies, roles, KA catalogue from the
 * catalogue port or the profile) – the React counterpart of Vue's `useOptions`.
 */

import { useEffect, useMemo, useState } from 'react'
import { kaOptions, loadCatalogue, optionsResolver, profileCatalogue, roleOptions, type FieldDescriptor, type Option } from '@auditcore/bpmn-flowaudit/ui'
import type { KeyRequirementEntry } from '@auditcore/bpmn-flowaudit'
import { useEditorContext } from '../context'
import { useI18n } from '../i18n'

export function useOptions(): (field: FieldDescriptor) => Option[] {
  const { profile, ports } = useEditorContext()
  const { locale } = useI18n()
  const current = profile()
  const [catalogue, setCatalogue] = useState<KeyRequirementEntry[]>(() => profileCatalogue(current, locale))

  useEffect(() => {
    let active = true
    setCatalogue(profileCatalogue(current, locale))
    if (ports.catalogue && current) void loadCatalogue(current, locale, ports.catalogue).then((entries) => active && setCatalogue(entries))
    return () => {
      active = false
    }
  }, [current, locale, ports.catalogue])

  return useMemo(() => optionsResolver(roleOptions(current, locale), kaOptions(catalogue), locale), [current, locale, catalogue])
}
