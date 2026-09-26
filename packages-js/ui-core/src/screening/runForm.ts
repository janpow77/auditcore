// Formularlogik „Neuer Prüflauf“ (Vue und React): Vorbelegung je Prüfart und
// Aufbau der Anfrage mit Prüfung der Eingaben.

import type { ProfileView, RunRequest, ScreeningKind, SettingsView, SourceView } from './types'
import { parseSubjects, type ViewMessage } from './view'

export const SCREENING_KINDS: readonly ScreeningKind[] = ['sanctions', 'pep']

export interface RunForm {
  kind: ScreeningKind
  profileKey: string
  lists: string[]
  subjectsText: string
  minScore: number | null
  caseReference: string
}

export const profileKeyOf = (profile: Pick<ProfileView, 'id' | 'version'>): string => `${profile.id}@${profile.version}`

export function kindProfiles(settings: SettingsView, kind: ScreeningKind): ProfileView[] {
  return settings.profiles.filter((profile) => profile.kind === kind)
}

export function kindSources(sources: readonly SourceView[], kind: ScreeningKind): SourceView[] {
  return sources.filter((source) => source.kind === kind)
}

export function selectedProfile(settings: SettingsView, form: Pick<RunForm, 'kind' | 'profileKey'>): ProfileView | undefined {
  return kindProfiles(settings, form.kind).find((profile) => profileKeyOf(profile) === form.profileKey)
}

/** Vorbelegung bei Wechsel der Prüfart oder neuen Einstellungen: empfohlenes Profil, alle Listen, Standard-Mindestwert. */
export function runFormDefaults(settings: SettingsView, sources: readonly SourceView[], kind: ScreeningKind): Pick<RunForm, 'profileKey' | 'lists' | 'minScore'> {
  const profiles = kindProfiles(settings, kind)
  const preferred = profiles.find((profile) => profile.recommended) ?? profiles[0]
  return {
    profileKey: preferred ? profileKeyOf(preferred) : '',
    lists: kindSources(sources, kind).map((source) => source.list.key),
    minScore: preferred ? preferred.default_min_score : null,
  }
}

/** Anfrage aus dem Formular; bei Fehlern `request: null` und die Meldungen als Katalogschlüssel. */
export function buildRunRequest(settings: SettingsView, form: RunForm): { request: RunRequest | null; errors: ViewMessage[] } {
  const parsed = parseSubjects(form.subjectsText)
  const profile = selectedProfile(settings, form)
  const errors = [...parsed.errors]
  if (!profile) errors.push({ key: 'errorProfile' })
  if (!form.lists.length) errors.push({ key: 'errorLists' })
  if (errors.length || !profile) return { request: null, errors }
  const request: RunRequest = { kind: form.kind, profile: { id: profile.id, version: profile.version }, subjects: parsed.subjects, lists: form.lists }
  if (form.minScore !== null) request.min_score = form.minScore
  if (form.caseReference.trim()) request.case_reference = form.caseReference.trim()
  return { request, errors }
}
