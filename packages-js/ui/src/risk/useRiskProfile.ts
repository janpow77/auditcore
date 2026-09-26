import { computed, watch, type Ref } from 'vue'
import { createRiskController, type Evaluation, type ProfileDetail, type RiskPort } from '@auditcore/ui-core'
import { useStore } from '../composables/useStore'

/**
 * Profilbeschreibung zur Auswertung: die übergebene, sonst über den Port
 * nachgeladen (Profil und Version der Auswertung, nie ein Standardprofil).
 */
export function useRiskProfile(
  evaluation: () => Evaluation | null | undefined,
  given: () => ProfileDetail | null | undefined,
  port: () => RiskPort | null | undefined,
): { profile: Readonly<Ref<ProfileDetail | null>>; error: Readonly<Ref<string>> } {
  const controller = createRiskController()
  const state = useStore(controller.store)
  const inputs = () => ({ evaluation: evaluation(), profile: given(), port: port() })
  watch([evaluation, given, port], () => void controller.loadProfile(inputs(), inputs), { immediate: true })
  return { profile: computed(() => state.value.profile), error: computed(() => state.value.profileError) }
}
