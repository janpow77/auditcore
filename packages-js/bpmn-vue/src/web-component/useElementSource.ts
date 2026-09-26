/**
 * Data source of the web component in Vue: XML, profile and ports from the
 * element properties, resolved by the framework-free `elementSource`
 * functions of the UI core and reloaded when an input changes.
 */

import { computed, ref, shallowRef, watch } from 'vue'
import { loadSource, persistSource, sourcePorts, sourceRest, sourceStorage, type ElementSourceInput } from '@auditcore/bpmn-flowaudit/ui'
import type { ProfileData } from '@auditcore/bpmn-flowaudit'

export type ElementSourceProps = ElementSourceInput

export function useElementSource(props: ElementSourceProps, onError: (message: string) => void) {
  const xml = ref('')
  const profile = shallowRef<ProfileData | null>(null)
  const rest = computed(() => sourceRest(props))
  const storage = computed(() => sourceStorage(props, rest.value))
  const ports = computed(() => sourcePorts(props, rest.value))

  async function reload(): Promise<void> {
    try {
      const next = await loadSource(props)
      profile.value = next.profile
      if (next.xml) xml.value = next.xml
    } catch (error) {
      onError((error as Error).message)
    }
  }

  watch(() => [props.xml, props.src, props.apiBase, props.diagramId, props.profile, props.profileData, props.storage], reload, { immediate: true })

  return { xml, profile, ports, storage, persist: (content: string) => persistSource(props, content), reload }
}
