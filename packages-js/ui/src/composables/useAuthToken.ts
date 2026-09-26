import { bearerHeaders, isTokenExpired, type TokenStore } from '@auditcore/common'
import { computed, getCurrentScope, onScopeDispose, readonly, ref, type ComputedRef, type Ref } from 'vue'

export interface UseAuthToken {
  token: Readonly<Ref<string | null>>
  /** `Authorization`-Kopfzeile für Anfragen (leer ohne Token). */
  headers: ComputedRef<Record<string, string>>
  /** Abgelaufen laut `exp` (Stand der letzten Änderung; ohne Token `true`). */
  expired: ComputedRef<boolean>
  set: (token: string) => void
  clear: () => void
}

/** Reaktiver Zugriff auf einen `TokenStore` aus `@auditcore/common`. */
export function useAuthToken(store: TokenStore): UseAuthToken {
  const token = ref<string | null>(store.get())
  const stop = store.subscribe((next) => {
    token.value = next
  })
  if (getCurrentScope()) onScopeDispose(stop)
  return {
    token: readonly(token),
    headers: computed(() => bearerHeaders({ get: () => token.value })),
    expired: computed(() => (token.value ? isTokenExpired(token.value) : true)),
    set: (value) => store.set(value),
    clear: () => store.clear(),
  }
}
