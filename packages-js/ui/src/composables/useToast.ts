import { createToastQueue, type Toast, type ToastInput, type ToastQueue } from '@flowaudit/common'
import { getCurrentScope, onScopeDispose, readonly, shallowRef, type Ref } from 'vue'

let sharedQueue: ToastQueue | null = null

/** Anwendungsweite Warteschlange (einmal je Seite). */
export function sharedToastQueue(): ToastQueue {
  sharedQueue ??= createToastQueue()
  return sharedQueue
}

export interface UseToast {
  toasts: Readonly<Ref<readonly Toast[]>>
  push: (input: ToastInput) => number
  success: (message: string, title?: string) => number
  error: (message: string, title?: string) => number
  info: (message: string, title?: string) => number
  warning: (message: string, title?: string) => number
  dismiss: (id: number) => void
  clear: () => void
}

/** Toasts als reaktive Liste über der framework-freien Warteschlange aus `@flowaudit/common`. */
export function useToast(queue: ToastQueue = sharedToastQueue()): UseToast {
  const toasts = shallowRef<readonly Toast[]>(queue.list())
  const stop = queue.subscribe((next) => {
    toasts.value = next
  })
  if (getCurrentScope()) onScopeDispose(stop)
  return {
    toasts: readonly(toasts) as Readonly<Ref<readonly Toast[]>>,
    push: queue.push,
    success: queue.success,
    error: queue.error,
    info: queue.info,
    warning: queue.warning,
    dismiss: queue.dismiss,
    clear: queue.clear,
  }
}
