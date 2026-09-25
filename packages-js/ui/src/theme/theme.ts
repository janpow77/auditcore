import { onScopeDispose, ref, type Ref } from 'vue'

export type ThemeMode = 'light' | 'dark' | 'system'

const ATTRIBUTE = 'data-fa-theme'

/** Setzt das Farbschema am Element (Standard: Dokumentwurzel); 'system' folgt dem Betriebssystem. */
export function applyTheme(mode: ThemeMode, element: HTMLElement = document.documentElement): void {
  if (mode === 'system') element.removeAttribute(ATTRIBUTE)
  else element.setAttribute(ATTRIBUTE, mode)
}

/** Liest das explizit gesetzte Farbschema; ohne Attribut 'system'. */
export function readTheme(element: HTMLElement = document.documentElement): ThemeMode {
  const value = element.getAttribute(ATTRIBUTE)
  return value === 'light' || value === 'dark' ? value : 'system'
}

/** Tatsächlich wirksames Schema, auch wenn 'system' gewählt ist. */
export function resolvedTheme(element: HTMLElement = document.documentElement): 'light' | 'dark' {
  const mode = readTheme(element)
  if (mode !== 'system') return mode
  const query = typeof window.matchMedia === 'function' ? window.matchMedia('(prefers-color-scheme: dark)') : null
  return query?.matches ? 'dark' : 'light'
}

export interface UseTheme {
  mode: Ref<ThemeMode>
  setMode: (mode: ThemeMode) => void
  toggle: () => void
}

/** Composable: reaktives Farbschema, synchron mit dem Attribut am Element. */
export function useTheme(element: HTMLElement = document.documentElement): UseTheme {
  const mode = ref<ThemeMode>(readTheme(element))
  const observer = new MutationObserver(() => {
    mode.value = readTheme(element)
  })
  observer.observe(element, { attributes: true, attributeFilter: [ATTRIBUTE] })
  onScopeDispose(() => observer.disconnect())
  function setMode(next: ThemeMode): void {
    applyTheme(next, element)
    mode.value = next
  }
  function toggle(): void {
    setMode(resolvedTheme(element) === 'dark' ? 'light' : 'dark')
  }
  return { mode, setMode, toggle }
}
