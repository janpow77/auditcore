import { ref, watch, type Ref } from 'vue'
import type { RiskPort } from './port'
import type { Evaluation, ProfileDetail } from './types'

/**
 * Profilbeschreibung zur Auswertung: die übergebene, sonst über den Port
 * nachgeladen (Profil und Version der Auswertung, nie ein Standardprofil).
 */
export function useRiskProfile(
  evaluation: () => Evaluation | null | undefined,
  given: () => ProfileDetail | null | undefined,
  port: () => RiskPort | null | undefined,
): { profile: Ref<ProfileDetail | null>; error: Ref<string> } {
  const profile = ref<ProfileDetail | null>(null)
  const error = ref('')
  watch([evaluation, given, port], async ([current, explicit, source]) => {
    error.value = ''
    profile.value = explicit ?? null
    const reference = current?.profile
    if (explicit || !source || !reference?.id) return
    try {
      const loaded = await source.profile(reference.id, reference.version)
      if (evaluation()?.profile.fingerprint === reference.fingerprint) profile.value = loaded
    } catch (failure) {
      error.value = failure instanceof Error ? failure.message : String(failure)
    }
  }, { immediate: true })
  return { profile, error }
}
