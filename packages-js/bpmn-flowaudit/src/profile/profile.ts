/**
 * Profiles: named, versioned catalogues per programming period (roles,
 * alias list, funds, key requirements/assessment criteria, frequent legal
 * bases, segregation-of-duties rules, templates).
 *
 * `ProfileData` is the file format `auditcore_bpmn.profile/1` of the Python
 * package (JSON keys in snake_case). The profile files are not duplicated:
 * they are read at build time from
 * `packages/auditcore_bpmn/src/auditcore_bpmn/profiles/data/`
 * (`bundled.ts`) or delivered by the application through the profile port.
 */

import { ROLES, roleAppliesTo, type Role } from '../schema/roles'
import { label, type Label, type Locale } from '../schema/vocabulary'

export const PROFILE_SCHEMA = 'auditcore_bpmn.profile/1'
export const DEFAULT_PROFILE = 'foerderperiode-2021-2027'

export type LocalizedText = Partial<Label> | string

export interface CriterionData {
  code: string
  title?: LocalizedText
}

export interface KeyRequirementData {
  number: number
  title: LocalizedText
  bodies?: LocalizedText
  scope?: LocalizedText
  footnote?: LocalizedText
  assessment_criteria?: CriterionData[]
}

export interface LegalBasisTemplateData {
  act: string
  article?: string
  annex?: string
  short_title?: LocalizedText
  celex?: string
  eli?: string
}

export interface SelectionData {
  markers?: string[]
  audit_types?: string[]
}

export type SegregationKind = 'separate_bodies' | 'excluded_role' | 'four_eyes'

export interface SegregationRuleData {
  id: string
  kind: SegregationKind | string
  severity: 'fehler' | 'warnung' | 'hinweis' | string
  title: LocalizedText
  a?: SelectionData
  b?: SelectionData
  selection?: SelectionData
  roles?: string[]
}

export interface TemplateData {
  id: string
  title: LocalizedText
  file: string
  origin?: string
}

export interface CustomRoleData {
  labels: LocalizedText
  from_year?: number
  until_year?: number
  /** Optional presentation (UI only). */
  short?: string
  color?: { fill: string; stroke: string }
  icon?: string
}

export interface CatalogueBlock<T> {
  source?: Record<string, unknown>
  entries: T[]
}

export interface ProfileData {
  schema: string
  id: string
  version: string
  title: LocalizedText
  programming_period?: string | null
  roles: string[]
  funds?: string[]
  key_requirements?: CatalogueBlock<KeyRequirementData> & { assessment_criteria_note?: LocalizedText }
  role_aliases?: RoleAlias[]
  segregation_rules?: SegregationRuleData[]
  templates?: TemplateData[]
  legal_bases?: CatalogueBlock<LegalBasisTemplateData>
  custom_roles?: Record<string, CustomRoleData>
}

export interface RoleAlias {
  pattern: string
  role: string
}

export function localized(value: LocalizedText | undefined, locale: Locale = 'de'): string {
  if (!value) return ''
  return typeof value === 'string' ? value : label(value, locale)
}

export function profileReference(profile: ProfileData): string {
  return `${profile.id}@${profile.version}`
}

/** Compares versions such as `2026.09.1` numerically part by part. */
export function compareProfileVersions(a: string, b: string): number {
  const x = a.split(/[^0-9]+/).filter(Boolean).map(Number)
  const y = b.split(/[^0-9]+/).filter(Boolean).map(Number)
  for (let i = 0; i < Math.max(x.length, y.length); i += 1) {
    const difference = (x[i] ?? 0) - (y[i] ?? 0)
    if (difference) return difference
  }
  return 0
}

function toLabel(value: LocalizedText, fallback: string): Label {
  if (typeof value === 'string') return { de: value, en: value }
  return { de: value.de ?? fallback, en: value.en ?? value.de ?? fallback }
}

/** Role by code (own roles of the profile win). */
export function roleOf(profile: ProfileData | null | undefined, code: string | undefined): Role | undefined {
  if (!code) return undefined
  const own = profile?.custom_roles?.[code]
  if (!own) return ROLES[code]
  const base = ROLES[code] ?? ROLES.sonstige
  return {
    code,
    label: toLabel(own.labels, code),
    short: own.short ?? code.toUpperCase(),
    color: own.color ?? base.color,
    icon: own.icon ?? base.icon,
    fromYear: own.from_year,
    untilYear: own.until_year,
  }
}

/** Roles of the profile, filtered by programming period (no profile: full catalogue). */
export function rolesFor(profile: ProfileData | null | undefined, programmingPeriod?: string | null): Role[] {
  const codes = profile ? [...profile.roles, ...Object.keys(profile.custom_roles ?? {})] : Object.keys(ROLES)
  const period = programmingPeriod ?? profile?.programming_period ?? null
  return [...new Set(codes)]
    .map((code) => roleOf(profile, code))
    .filter((role): role is Role => Boolean(role) && roleAppliesTo(role as Role, period))
}

export function roleProvided(profile: ProfileData | null | undefined, code: string | undefined): boolean {
  if (!code) return false
  if (!profile) return code in ROLES
  return profile.roles.includes(code) || Boolean(profile.custom_roles?.[code])
}

/**
 * Role from a lane name or task prefix via the alias list (first hit, case
 * insensitive). Additional aliases – e.g. names of bodies in a programme –
 * are supplied by the application.
 */
export function roleFromText(profile: ProfileData | null | undefined, text: string | undefined | null, extra: RoleAlias[] = []): string | undefined {
  if (!text) return undefined
  const lower = text.toLocaleLowerCase('de')
  return [...extra, ...(profile?.role_aliases ?? [])].find((alias) => lower.includes(alias.pattern.toLocaleLowerCase('de')))?.role
}

export function keyRequirements(profile: ProfileData | null | undefined): KeyRequirementData[] {
  return profile?.key_requirements?.entries ?? []
}

export function keyRequirement(profile: ProfileData | null | undefined, ka: string | number | undefined): KeyRequirementData | undefined {
  const number = Number(String(ka ?? '').trim())
  return Number.isInteger(number) ? keyRequirements(profile).find((entry) => entry.number === number) : undefined
}

/** `true`/`false` against the criteria catalogue of the KA; `undefined` if none exists. */
export function criterionKnown(profile: ProfileData | null | undefined, ka: string | number | undefined, bk: string): boolean | undefined {
  const entry = keyRequirement(profile, ka)
  if (!entry?.assessment_criteria?.length) return undefined
  return entry.assessment_criteria.some((criterion) => criterion.code === bk.trim())
}

/** Profile with injected assessment criteria (e.g. from a catalogue port). */
export function withCriteria(profile: ProfileData, criteria: Record<number, CriterionData[]>): ProfileData {
  if (!profile.key_requirements) return profile
  const entries = profile.key_requirements.entries.map((entry) =>
    criteria[entry.number] ? { ...entry, assessment_criteria: criteria[entry.number] } : entry,
  )
  return { ...profile, key_requirements: { ...profile.key_requirements, entries } }
}

/** Latest version per profile id. */
export function latestProfiles(profiles: ProfileData[]): ProfileData[] {
  const byId = new Map<string, ProfileData>()
  for (const profile of profiles) {
    const previous = byId.get(profile.id)
    if (!previous || compareProfileVersions(profile.version, previous.version) > 0) byId.set(profile.id, profile)
  }
  return [...byId.values()].sort((a, b) => a.id.localeCompare(b.id))
}

export function validateProfile(data: unknown): ProfileData {
  const profile = data as ProfileData
  if (!profile || profile.schema !== PROFILE_SCHEMA) throw new Error(`Profilschema ${String(profile?.schema)} wird nicht unterstützt.`)
  if (!profile.id || !profile.version || !Array.isArray(profile.roles)) throw new Error('Profil unvollständig (id, version, roles).')
  return profile
}
