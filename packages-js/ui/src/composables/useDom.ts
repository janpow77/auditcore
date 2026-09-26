import { onClickOutside, matchesMediaQuery, subscribeMediaQuery } from '@flowaudit/common/browser'
import { getCurrentScope, onScopeDispose, readonly, ref, toValue, watch, type MaybeRefOrGetter, type Ref } from 'vue'

function dispose(stop: () => void): void {
  if (getCurrentScope()) onScopeDispose(stop)
}

/** Reaktiver Stand einer Media-Query, z. B. `useMediaQuery('(max-width: 768px)')`. */
export function useMediaQuery(query: MaybeRefOrGetter<string>): Readonly<Ref<boolean>> {
  const matches = ref(false)
  let unsubscribe = (): void => undefined
  const stop = watch(
    () => toValue(query),
    (current) => {
      unsubscribe()
      matches.value = matchesMediaQuery(current)
      unsubscribe = subscribeMediaQuery(current, (value) => {
        matches.value = value
      })
    },
    { immediate: true },
  )
  dispose(() => {
    stop()
    unsubscribe()
  })
  return readonly(matches)
}

/** Ruft `handler` bei Klick außerhalb der Elemente (Template-Refs) und bei Escape; abgemeldet beim Aufräumen. */
export function useClickOutside(
  targets: Ref<HTMLElement | null | undefined> | readonly Ref<HTMLElement | null | undefined>[],
  handler: (event: Event) => void,
  options: { escape?: boolean } = {},
): () => void {
  const list = Array.isArray(targets) ? targets : [targets]
  const stop = onClickOutside(list.map((target) => () => target.value), handler, options)
  dispose(stop)
  return stop
}
