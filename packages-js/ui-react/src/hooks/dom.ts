import { matchesMediaQuery, onClickOutside, subscribeMediaQuery } from '@flowaudit/common/browser'
import { useCallback, useEffect, useRef, useSyncExternalStore, type RefObject } from 'react'

/** Stand einer Media-Query, z. B. `useMediaQuery('(max-width: 768px)')`; serverseitig `false`. */
export function useMediaQuery(query: string): boolean {
  const subscribe = useCallback((notify: () => void) => subscribeMediaQuery(query, notify), [query])
  const snapshot = useCallback(() => matchesMediaQuery(query), [query])
  return useSyncExternalStore(subscribe, snapshot, () => false)
}

/** Ruft `handler` bei Klick außerhalb der Elemente und bei Escape; abgemeldet beim Unmount. */
export function useClickOutside(
  refs: RefObject<Element | null> | readonly RefObject<Element | null>[],
  handler: (event: Event) => void,
  options: { escape?: boolean; enabled?: boolean } = {},
): void {
  const latest = useRef(handler)
  latest.current = handler
  const list = Array.isArray(refs) ? refs : [refs]
  const { escape, enabled = true } = options
  useEffect(() => {
    if (!enabled) return undefined
    return onClickOutside(
      list.map((ref) => () => ref.current),
      (event) => latest.current(event),
      { escape },
    )
    // Ref-Objekte sind stabil; neu abonnieren nur bei geänderten Optionen.
  }, [escape, enabled])
}
