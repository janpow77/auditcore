/**
 * Ports: interfaces supplied by the embedding application.
 *
 * The library never accesses network or database itself. Storage, legal
 * search, KA/BK texts, profiles and a server-side validation come in
 * through these ports. Simple in-memory implementations for demo and tests
 * live in `ports/inMemory.ts`.
 */

import type { CollectionData } from './collection/collectionData'
import type { ProfileData } from './profile/profile'
import type { LegalBasis } from './schema/types'
import type { ValidationIssue } from './validation/issue'

/**
 * Loading and saving of collection, diagrams and approvals – same split as
 * the `Speicher` protocol of `auditcore_bpmn`.
 */
export interface StoragePort {
  loadCollection(): Promise<CollectionData | null>
  saveCollection(collection: CollectionData): Promise<void>
  loadDiagram(diagramId: string): Promise<string>
  saveDiagram(diagramId: string, xml: string): Promise<void>
  deleteDiagram(diagramId: string): Promise<void>
  /** Stores an immutable approved version (optional). */
  saveApproval?(diagramId: string, version: string, xml: string): Promise<void>
  loadApproval?(diagramId: string, version: string): Promise<string>
  /** Comments per element (legacy `comments`, optional). */
  loadComments?(diagramId: string): Promise<Comment[]>
  saveComments?(diagramId: string, comments: Comment[]): Promise<void>
}

/** Comment at an element (as `BpmnComment` in the audit_designer). */
export interface Comment {
  id: string
  elementId: string
  text: string
  author: string
  timestamp: string
  resolved: boolean
}

export interface LegalSearchHit extends LegalBasis {
  /** Article heading or title of the act for display. */
  title?: string
  /** Short excerpt of the text. */
  excerpt?: string
  /** Origin of the hit, e.g. „EUR-Lex“ or „Profil“. */
  origin?: string
}

export interface LegalSearchOptions {
  locale?: 'de' | 'en'
  limit?: number
  profile?: string
  signal?: AbortSignal
}

/** Search help for legal bases (e.g. from auditcore_legal_sources / EUR-Lex). */
export interface LegalSearchPort {
  search(query: string, options?: LegalSearchOptions): Promise<LegalSearchHit[]>
}

export interface KeyRequirementEntry {
  number: number
  title: string
  bodies?: string
  criteria: { code: string; title: string }[]
}

/**
 * KA/BK catalogue. The application supplies the texts (e.g. of the
 * Methodological Note); without a port the key requirements of the profile
 * apply.
 */
export interface CataloguePort {
  keyRequirements(profileId: string, locale?: 'de' | 'en'): Promise<KeyRequirementEntry[]>
}

export interface ProfileSummary {
  id: string
  version: string
  title: string
  fundingPeriod?: string | null
}

export interface ProfilePort {
  profiles(): Promise<ProfileSummary[]>
  loadProfile(profileId: string, version?: string): Promise<ProfileData>
}

/** Server-side validation (e.g. `auditcore_bpmn`), optional. */
export interface ValidationPort {
  validate(xml: string, options?: { profile?: string; referenceDate?: string; locale?: 'de' | 'en' }): Promise<ValidationIssue[]>
}
