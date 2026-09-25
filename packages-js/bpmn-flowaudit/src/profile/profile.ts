/**
 * Profiles: named, versioned catalogues per programming period (roles,
 * alias list, funds, key requirements/assessment criteria, frequent legal
 * bases, segregation-of-duties rules, templates).
 *
 * `ProfileData` is the file format `auditcore_bpmn.profil/1` of the Python
 * package (its keys are therefore German). The profile files are not
 * duplicated: they are read at build time from
 * `packages/auditcore_bpmn/…/profildaten/` (`bundled.ts`) or delivered by
 * the application through the profile port.
 */

import { ROLES, roleAppliesTo, type Role } from '../schema/roles'
import { label, type Label, type Locale } from '../schema/vocabulary'

export const PROFILE_SCHEMA = 'auditcore_bpmn.profil/1'
export const DEFAULT_PROFILE = 'foerderperiode-2021-2027'

export type LocalizedText = Partial<Label> | string

export interface CriterionData {
  code: string
  titel?: LocalizedText
}

export interface KeyRequirementData {
  nummer: number
  titel: LocalizedText
  stellen?: LocalizedText
  geltungsbereich?: LocalizedText
  fussnote?: LocalizedText
  bewertungskriterien?: CriterionData[]
}

export interface LegalBasisTemplateData {
  norm: string
  artikel?: string
  paragraph?: string
  kurzbezeichnung?: LocalizedText
  celex?: string
  eli?: string
}

export interface SelectionData {
  kennzeichen?: string[]
  pruefart?: string[]
}

export interface SegregationRuleData {
  id: string
  typ: 'getrennte_stellen' | 'rolle_ausgeschlossen' | 'vier_augen' | string
  schwere: 'fehler' | 'warnung' | 'hinweis' | string
  titel: LocalizedText
  a?: SelectionData
  b?: SelectionData
  auswahl?: SelectionData
  rollen?: string[]
}

export interface TemplateData {
  id: string
  titel: LocalizedText
  datei: string
  herkunft?: string
}

export interface OwnRoleData {
  bezeichnung: LocalizedText
  ab_jahr?: number
  bis_jahr?: number
  kurz?: string
  farbe?: { fill: string; stroke: string }
  icon?: string
}

export interface ProfileData {
  schema: string
  id: string
  version: string
  titel: LocalizedText
  foerderperiode?: string | null
  rollen: string[]
  fonds?: string[]
  kernanforderungen?: { quelle?: Record<string, unknown>; eintraege: KeyRequirementData[]; bewertungskriterien_hinweis?: LocalizedText }
  rollen_aliase?: RoleAlias[]
  funktionstrennung?: SegregationRuleData[]
  vorlagen?: TemplateData[]
  rechtsgrundlagen?: { quelle?: Record<string, unknown>; eintraege: LegalBasisTemplateData[] }
  eigene_rollen?: Record<string, OwnRoleData>
}

export interface RoleAlias {
  muster: string
  rolle: string
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
  const own = profile?.eigene_rollen?.[code]
  if (!own) return ROLES[code]
  const base = ROLES[code] ?? ROLES.sonstige
  return {
    code,
    label: toLabel(own.bezeichnung, code),
    short: own.kurz ?? code.toUpperCase(),
    color: own.farbe ?? base.color,
    icon: own.icon ?? base.icon,
    fromYear: own.ab_jahr,
    untilYear: own.bis_jahr,
  }
}

/** Roles of the profile, filtered by programming period (no profile: full catalogue). */
export function rolesFor(profile: ProfileData | null | undefined, fundingPeriod?: string | null): Role[] {
  const codes = profile ? [...profile.rollen, ...Object.keys(profile.eigene_rollen ?? {})] : Object.keys(ROLES)
  const period = fundingPeriod ?? profile?.foerderperiode ?? null
  return [...new Set(codes)]
    .map((code) => roleOf(profile, code))
    .filter((role): role is Role => Boolean(role) && roleAppliesTo(role as Role, period))
}

export function roleProvided(profile: ProfileData | null | undefined, code: string | undefined): boolean {
  if (!code) return false
  if (!profile) return code in ROLES
  return profile.rollen.includes(code) || Boolean(profile.eigene_rollen?.[code])
}

/**
 * Role from a lane name or task prefix via the alias list (first hit, case
 * insensitive). Additional aliases – e.g. names of bodies in a programme –
 * are supplied by the application.
 */
export function roleFromText(profile: ProfileData | null | undefined, text: string | undefined | null, extra: RoleAlias[] = []): string | undefined {
  if (!text) return undefined
  const lower = text.toLocaleLowerCase('de')
  return [...extra, ...(profile?.rollen_aliase ?? [])].find((alias) => lower.includes(alias.muster.toLocaleLowerCase('de')))?.rolle
}

export function keyRequirements(profile: ProfileData | null | undefined): KeyRequirementData[] {
  return profile?.kernanforderungen?.eintraege ?? []
}

export function keyRequirement(profile: ProfileData | null | undefined, ka: string | number | undefined): KeyRequirementData | undefined {
  const number = Number(String(ka ?? '').trim())
  return Number.isInteger(number) ? keyRequirements(profile).find((entry) => entry.nummer === number) : undefined
}

/** `true`/`false` against the criteria catalogue of the KA; `undefined` if none exists. */
export function criterionKnown(profile: ProfileData | null | undefined, ka: string | number | undefined, bk: string): boolean | undefined {
  const entry = keyRequirement(profile, ka)
  if (!entry?.bewertungskriterien?.length) return undefined
  return entry.bewertungskriterien.some((criterion) => criterion.code === bk.trim())
}

/** Profile with injected assessment criteria (e.g. from a catalogue port). */
export function withCriteria(profile: ProfileData, criteria: Record<number, CriterionData[]>): ProfileData {
  if (!profile.kernanforderungen) return profile
  const eintraege = profile.kernanforderungen.eintraege.map((entry) =>
    criteria[entry.nummer] ? { ...entry, bewertungskriterien: criteria[entry.nummer] } : entry,
  )
  return { ...profile, kernanforderungen: { ...profile.kernanforderungen, eintraege } }
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
  if (!profile.id || !profile.version || !Array.isArray(profile.rollen)) throw new Error('Profil unvollständig (id, version, rollen).')
  return profile
}
