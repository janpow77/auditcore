import { debounce, throttle, type Debounced } from '@auditcore/common'
import { getCurrentScope, onScopeDispose, readonly, ref, watch, type Ref, type WatchSource } from 'vue'

function cancelOnDispose<A extends unknown[]>(fn: Debounced<A>): Debounced<A> {
  if (getCurrentScope()) onScopeDispose(() => fn.cancel())
  return fn
}

/** Entprellte Funktion; ein ausstehender Aufruf wird beim Abbau der Komponente verworfen. */
export function useDebouncedFn<A extends unknown[]>(fn: (...args: A) => void, ms: number): Debounced<A> {
  return cancelOnDispose(debounce(fn, ms))
}

/** Gedrosselte Funktion; ein ausstehender Aufruf wird beim Abbau der Komponente verworfen. */
export function useThrottledFn<A extends unknown[]>(fn: (...args: A) => void, ms: number): Debounced<A> {
  return cancelOnDispose(throttle(fn, ms))
}

/** Folgt `source` erst nach `ms` Ruhe (z. B. Suchfeld → Anfrage). */
export function useDebouncedRef<T>(source: WatchSource<T>, ms: number, initial: T): Readonly<Ref<T>> {
  const value = ref(initial) as Ref<T>
  const update = useDebouncedFn((next: T) => {
    value.value = next
  }, ms)
  watch(source, (next) => update(next))
  return readonly(value) as Readonly<Ref<T>>
}
