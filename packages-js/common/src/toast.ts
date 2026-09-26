// Framework-freie Warteschlange für Benachrichtigungen (Toasts). Vue
// (`useToast` in `@flowaudit/ui`) und React (`useToast` in
// `@flowaudit/ui-react`) abonnieren dieselbe Warteschlange.

/** Art eines Toasts (bestimmt Farbe und Standarddauer). */
export type ToastKind = 'success' | 'error' | 'info' | 'warning'

/** Sichtbarer Toast. */
export interface Toast {
  id: number
  kind: ToastKind
  message: string
  title?: string
  /** Anzeigedauer in ms; 0 = bleibt bis zum Schließen. */
  durationMs: number
}

/** Eingabe für `push`; `kind` Standard `info`. */
export interface ToastInput {
  kind?: ToastKind
  message: string
  title?: string
  durationMs?: number
}

/** Dauer und Höchstzahl der Warteschlange. */
export interface ToastQueueOptions {
  /** Anzeigedauer für success/info/warning (Standard 4000 ms). */
  defaultMs?: number
  /** Anzeigedauer für Fehler (Standard 8000 ms). */
  errorMs?: number
  /** Höchstzahl gleichzeitig sichtbarer Toasts (Standard 5, älteste fallen weg). */
  max?: number
}

/** Rückruf mit dem neuen Stand der Warteschlange. */
export type ToastListener = (toasts: readonly Toast[]) => void

/** Framework-freie Warteschlange; Vue und React abonnieren sie. */
export interface ToastQueue {
  push(input: ToastInput): number
  success(message: string, title?: string): number
  error(message: string, title?: string): number
  info(message: string, title?: string): number
  warning(message: string, title?: string): number
  dismiss(id: number): void
  clear(): void
  /** Aktueller, unveränderlicher Stand (gleiche Referenz bis zur nächsten Änderung). */
  list(): readonly Toast[]
  subscribe(listener: ToastListener): () => void
}

/** Neue Warteschlange mit selbstständigem Ausblenden nach `durationMs`. */
export function createToastQueue(options: ToastQueueOptions = {}): ToastQueue {
  const listeners = new Set<ToastListener>()
  const timers = new Map<number, ReturnType<typeof setTimeout>>()
  let toasts: readonly Toast[] = []
  let nextId = 1
  const emit = (next: readonly Toast[]): void => {
    toasts = next
    listeners.forEach((listener) => listener(toasts))
  }
  const dismiss = (id: number): void => {
    clearTimeout(timers.get(id))
    timers.delete(id)
    if (toasts.some((toast) => toast.id === id)) emit(toasts.filter((toast) => toast.id !== id))
  }
  const push = (input: ToastInput): number => {
    const kind = input.kind ?? 'info'
    const durationMs = input.durationMs ?? (kind === 'error' ? (options.errorMs ?? 8000) : (options.defaultMs ?? 4000))
    const toast: Toast = { id: nextId++, kind, message: input.message, title: input.title, durationMs }
    const kept = [...toasts, toast]
    kept.slice(0, Math.max(0, kept.length - (options.max ?? 5))).forEach((old) => dismiss(old.id))
    emit([...toasts, toast])
    if (durationMs > 0) timers.set(toast.id, setTimeout(() => dismiss(toast.id), durationMs))
    return toast.id
  }
  const shortcut = (kind: ToastKind) => (message: string, title?: string): number => push({ kind, message, title })
  return {
    push,
    success: shortcut('success'),
    error: shortcut('error'),
    info: shortcut('info'),
    warning: shortcut('warning'),
    dismiss,
    clear() {
      timers.forEach((timer) => clearTimeout(timer))
      timers.clear()
      emit([])
    },
    list: () => toasts,
    subscribe(listener) {
      listeners.add(listener)
      return () => listeners.delete(listener)
    },
  }
}
