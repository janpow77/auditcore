import { createToastQueue, type Toast, type ToastInput, type ToastQueue } from '@auditcore/common'
import { createContext, createElement, useContext, useSyncExternalStore, type ReactNode } from 'react'

let sharedQueue: ToastQueue | null = null

/** Anwendungsweite Warteschlange (einmal je Seite), wenn kein `ToastProvider` gesetzt ist. */
export function sharedToastQueue(): ToastQueue {
  sharedQueue ??= createToastQueue()
  return sharedQueue
}

const ToastContext = createContext<ToastQueue | null>(null)

/** Stellt eine eigene Warteschlange für den Teilbaum bereit (z. B. je Mandant oder im Test). */
export function ToastProvider({ queue, children }: { queue: ToastQueue; children?: ReactNode }) {
  return createElement(ToastContext.Provider, { value: queue }, children)
}

export interface UseToast {
  toasts: readonly Toast[]
  push: (input: ToastInput) => number
  success: (message: string, title?: string) => number
  error: (message: string, title?: string) => number
  info: (message: string, title?: string) => number
  warning: (message: string, title?: string) => number
  dismiss: (id: number) => void
  clear: () => void
}

/** Toasts über der framework-freien Warteschlange aus `@auditcore/common` (Provider, sonst gemeinsame Warteschlange). */
export function useToast(queue?: ToastQueue): UseToast {
  const context = useContext(ToastContext)
  const active = queue ?? context ?? sharedToastQueue()
  const toasts = useSyncExternalStore(active.subscribe, active.list, active.list)
  return {
    toasts,
    push: active.push,
    success: active.success,
    error: active.error,
    info: active.info,
    warning: active.warning,
    dismiss: active.dismiss,
    clear: active.clear,
  }
}
