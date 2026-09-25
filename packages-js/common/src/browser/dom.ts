/** Aktueller Stand einer Media-Query; ohne `matchMedia` (SSR, Tests) `false`. */
export function matchesMediaQuery(query: string): boolean {
  return typeof globalThis.matchMedia === 'function' ? globalThis.matchMedia(query).matches : false
}

/** Abonniert eine Media-Query (`(prefers-color-scheme: dark)`, `(max-width: 768px)`); gibt die Abmeldung zurück. */
export function subscribeMediaQuery(query: string, listener: (matches: boolean) => void): () => void {
  if (typeof globalThis.matchMedia !== 'function') return () => undefined
  const list = globalThis.matchMedia(query)
  const handler = (event: MediaQueryListEvent): void => listener(event.matches)
  list.addEventListener('change', handler)
  return () => list.removeEventListener('change', handler)
}

/** Element oder Getter (z. B. Template-Ref), zum Zeitpunkt des Klicks ausgewertet. */
export type ElementSource = Element | null | undefined | (() => Element | null | undefined)

function resolveElement(source: ElementSource): Element | null {
  const element = typeof source === 'function' ? source() : source
  return element ?? null
}

/**
 * Ruft `handler` bei Zeiger-Klick außerhalb aller Elemente und bei Escape
 * (`escape: true`, Standard); gibt die Abmeldung zurück.
 */
export function onClickOutside(
  targets: ElementSource | readonly ElementSource[],
  handler: (event: Event) => void,
  options: { escape?: boolean } = {},
): () => void {
  if (typeof document === 'undefined') return () => undefined
  const sources = (Array.isArray(targets) ? targets : [targets]) as readonly ElementSource[]
  const onPointer = (event: Event): void => {
    const path = event.composedPath()
    const inside = sources.some((source) => {
      const element = resolveElement(source)
      return element !== null && (path.includes(element) || element.contains(event.target as Node | null))
    })
    if (!inside) handler(event)
  }
  const onKey = (event: KeyboardEvent): void => {
    if (event.key === 'Escape') handler(event)
  }
  document.addEventListener('pointerdown', onPointer, true)
  if (options.escape ?? true) document.addEventListener('keydown', onKey)
  return () => {
    document.removeEventListener('pointerdown', onPointer, true)
    document.removeEventListener('keydown', onKey)
  }
}
