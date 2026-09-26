/**
 * Simple in-memory port implementations for demos and tests.
 */

import { citation, shortCitation } from '../model/legalBasis'
import { parseCitation, completeEuAct } from '../enrichment/citations'
import { keyRequirements, localized, type ProfileData } from '../profile/profile'
import type { CollectionData } from '../collection/collectionData'
import type {
  CataloguePort,
  Comment,
  KeyRequirementEntry,
  LegalSearchHit,
  LegalSearchOptions,
  LegalSearchPort,
  ProfilePort,
  ProfileSummary,
  StoragePort,
} from '../ports'

/**
 * Deep copy of JSON data. Unlike `structuredClone` this also accepts
 * framework proxies (e.g. Vue `reactive`) handed in by the application.
 */
function cloneJson<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T
}

export class InMemoryStorage implements StoragePort {
  private collection: CollectionData | null
  private readonly diagrams = new Map<string, string>()
  private readonly approvals = new Map<string, string>()
  private readonly comments = new Map<string, Comment[]>()

  constructor(initial: { collection?: CollectionData; diagrams?: Record<string, string> } = {}) {
    this.collection = initial.collection ? cloneJson(initial.collection) : null
    for (const [id, xml] of Object.entries(initial.diagrams ?? {})) this.diagrams.set(id, xml)
  }

  async loadCollection(): Promise<CollectionData | null> {
    return this.collection ? cloneJson(this.collection) : null
  }

  async saveCollection(collection: CollectionData): Promise<void> {
    this.collection = cloneJson(collection)
  }

  async loadDiagram(id: string): Promise<string> {
    const xml = this.diagrams.get(id)
    if (xml === undefined) throw new Error(`Diagramm „${id}“ ist unbekannt.`)
    return xml
  }

  async saveDiagram(id: string, xml: string): Promise<void> {
    this.diagrams.set(id, xml)
  }

  async deleteDiagram(id: string): Promise<void> {
    this.diagrams.delete(id)
  }

  async saveApproval(id: string, version: string, xml: string): Promise<void> {
    const key = `${id}@${version}`
    if (this.approvals.has(key) && this.approvals.get(key) !== xml) throw new Error(`Version ${version} ist bereits freigegeben.`)
    this.approvals.set(key, xml)
  }

  async loadApproval(id: string, version: string): Promise<string> {
    const xml = this.approvals.get(`${id}@${version}`)
    if (xml === undefined) throw new Error(`Kein freigegebener Stand ${version}.`)
    return xml
  }

  async loadComments(id: string): Promise<Comment[]> {
    return cloneJson(this.comments.get(id) ?? [])
  }

  async saveComments(id: string, comments: Comment[]): Promise<void> {
    this.comments.set(id, cloneJson(comments))
  }
}

export class StaticProfilePort implements ProfilePort {
  constructor(private readonly profileList: ProfileData[]) {}

  async profiles(): Promise<ProfileSummary[]> {
    return this.profileList.map((p) => ({ id: p.id, version: p.version, title: localized(p.title), programmingPeriod: p.programming_period ?? null }))
  }

  async loadProfile(profileId: string, version?: string): Promise<ProfileData> {
    const found = this.profileList.find((p) => p.id === profileId && (!version || p.version === version))
    if (!found) throw new Error(`Profil „${profileId}“ ist unbekannt.`)
    return found
  }
}

/** KA catalogue from a profile, optionally enriched by criteria texts of the application. */
export class ProfileCataloguePort implements CataloguePort {
  constructor(
    private readonly profilePort: ProfilePort,
    private readonly criteria: Record<string, Record<number, { code: string; title: string }[]>> = {},
  ) {}

  async keyRequirements(profileId: string, locale: 'de' | 'en' = 'de'): Promise<KeyRequirementEntry[]> {
    const profile = await this.profilePort.loadProfile(profileId)
    return keyRequirements(profile).map((entry) => ({
      number: entry.number,
      title: localized(entry.title, locale),
      bodies: localized(entry.bodies, locale),
      criteria:
        this.criteria[profileId]?.[entry.number] ?? (entry.assessment_criteria ?? []).map((c) => ({ code: c.code, title: localized(c.title, locale) })),
    }))
  }
}

/**
 * Legal search over the frequent legal bases of a profile plus parsing of
 * the typed citation. No network access.
 */
export class ProfileLegalSearch implements LegalSearchPort {
  constructor(private readonly profile: ProfileData | null) {}

  async search(query: string, options: LegalSearchOptions = {}): Promise<LegalSearchHit[]> {
    const needle = query.trim().toLocaleLowerCase('de')
    if (!needle) return []
    const parsed = parseCitation(query)
    const typed: LegalSearchHit[] = parsed.act ? [{ ...completeEuAct(parsed), origin: 'Eingabe' }] : []
    const templates = (this.profile?.legal_bases?.entries ?? []).map((entry) => ({
      act: entry.act,
      article: entry.article,
      annex: entry.annex,
      celex: entry.celex,
      eli: entry.eli,
      shortTitle: localized(entry.short_title, options.locale),
      title: localized(entry.short_title, options.locale),
      origin: 'Profil',
    }))
    const matches = templates.filter((hit) =>
      [shortCitation(hit), citation(hit), hit.shortTitle ?? ''].some((text) => text.toLocaleLowerCase('de').includes(needle)),
    )
    return [...typed, ...matches].slice(0, options.limit ?? 20)
  }
}
