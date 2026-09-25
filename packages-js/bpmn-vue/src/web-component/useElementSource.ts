/**
 * Data source of the web component: XML from the `xml` property, from the
 * storage port (`diagram-id` with `api-base` or a `storage` property) or
 * from a URL (`src`); profile from the `profileData` property, the REST
 * profile port or the bundled profiles.
 */

import { computed, ref, shallowRef, watch } from 'vue'
import { bundledProfiles, defaultProfile } from '@flowaudit/bpmn-flowaudit/profiles'
import type { ProfileData, StoragePort, ValidationPort } from '@flowaudit/bpmn-flowaudit'
import { restPorts } from '../rest/restPorts'
import type { EditorPorts } from '../stores/context'

export interface ElementSourceProps {
  xml?: string
  src?: string
  apiBase?: string
  diagramId?: string
  profile?: string
  profileData?: ProfileData | null
  storage?: StoragePort
  ports?: EditorPorts & { validation?: ValidationPort }
}

export function useElementSource(props: ElementSourceProps, onError: (message: string) => void) {
  const xml = ref('')
  const profile = shallowRef<ProfileData | null>(null)
  const rest = computed(() => (props.apiBase ? restPorts({ baseUrl: props.apiBase }) : null))
  const storage = computed<StoragePort | undefined>(() => props.storage ?? rest.value?.storage)
  const ports = computed(() => ({ ...(rest.value ? { legalSearch: rest.value.legalSearch, catalogue: rest.value.catalogue, validation: rest.value.validation, esi: rest.value.esi } : {}), ...(props.ports ?? {}) }))

  async function fetchXml(): Promise<string> {
    if (props.xml) return props.xml
    if (props.diagramId && storage.value) return storage.value.loadDiagram(props.diagramId)
    if (props.src) {
      const response = await fetch(props.src, { credentials: 'same-origin' })
      if (!response.ok) throw new Error(`${response.status} ${response.statusText}`.trim())
      return response.text()
    }
    return ''
  }

  async function fetchProfile(): Promise<ProfileData | null> {
    if (props.profileData !== undefined) return props.profileData
    const bundled = bundledProfiles().find((entry) => entry.id === props.profile)
    if (props.profile && rest.value) return rest.value.profiles.loadProfile(props.profile).catch(() => bundled ?? null)
    return bundled ?? defaultProfile() ?? null
  }

  async function reload(): Promise<void> {
    try {
      const [nextXml, nextProfile] = await Promise.all([fetchXml(), fetchProfile()])
      profile.value = nextProfile
      if (nextXml) xml.value = nextXml
    } catch (error) {
      onError((error as Error).message)
    }
  }

  async function persist(content: string): Promise<void> {
    if (props.diagramId && storage.value) await storage.value.saveDiagram(props.diagramId, content)
  }

  watch(() => [props.xml, props.src, props.apiBase, props.diagramId, props.profile, props.profileData, props.storage], reload, { immediate: true })

  return { xml, profile, ports, storage, persist, reload }
}
