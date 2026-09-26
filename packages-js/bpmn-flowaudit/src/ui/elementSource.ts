/**
 * Data source of the embeddable editor (web component, React component):
 * XML from `xml`, from the storage port (`diagramId` with `apiBase` or a
 * `storage` object) or from a URL (`src`); profile from `profileData`, the
 * REST profile port or the bundled profiles.
 */

import { bundledProfiles, defaultProfile } from '../profile/bundled'
import type { ProfileData, StoragePort, ValidationPort } from '../index'
import type { EditorPorts } from './ports'
import { restPorts } from './rest/restPorts'

export interface ElementSourceInput {
  xml?: string
  src?: string
  apiBase?: string
  diagramId?: string
  profile?: string
  profileData?: ProfileData | null
  storage?: StoragePort
  ports?: EditorPorts & { validation?: ValidationPort }
}

export type RestBundle = ReturnType<typeof restPorts>

export const sourceRest = (input: ElementSourceInput): RestBundle | null => (input.apiBase ? restPorts({ baseUrl: input.apiBase }) : null)
export const sourceStorage = (input: ElementSourceInput, rest: RestBundle | null): StoragePort | undefined => input.storage ?? rest?.storage

export function sourcePorts(input: ElementSourceInput, rest: RestBundle | null): EditorPorts & { validation?: ValidationPort } {
  const fromRest = rest ? { legalSearch: rest.legalSearch, catalogue: rest.catalogue, validation: rest.validation, esi: rest.esi } : {}
  return { ...fromRest, ...(input.ports ?? {}) }
}

export async function fetchSourceXml(input: ElementSourceInput, storage: StoragePort | undefined): Promise<string> {
  if (input.xml) return input.xml
  if (input.diagramId && storage) return storage.loadDiagram(input.diagramId)
  if (!input.src) return ''
  const response = await fetch(input.src, { credentials: 'same-origin' })
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`.trim())
  return response.text()
}

export async function fetchSourceProfile(input: ElementSourceInput, rest: RestBundle | null): Promise<ProfileData | null> {
  if (input.profileData !== undefined) return input.profileData
  const bundled = bundledProfiles().find((entry) => entry.id === input.profile)
  if (input.profile && rest) return rest.profiles.loadProfile(input.profile).catch(() => bundled ?? null)
  return bundled ?? defaultProfile() ?? null
}

/** Loads XML and profile together. */
export async function loadSource(input: ElementSourceInput): Promise<{ xml: string; profile: ProfileData | null }> {
  const rest = sourceRest(input)
  const [xml, profile] = await Promise.all([fetchSourceXml(input, sourceStorage(input, rest)), fetchSourceProfile(input, rest)])
  return { xml, profile }
}

export async function persistSource(input: ElementSourceInput, xml: string): Promise<void> {
  const storage = sourceStorage(input, sourceRest(input))
  if (input.diagramId && storage) await storage.saveDiagram(input.diagramId, xml)
}
