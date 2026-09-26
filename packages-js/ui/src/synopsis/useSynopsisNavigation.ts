import { computed, ref, watch, type ComputedRef, type Ref } from 'vue'
import { changeIds, positionText, stepChange, type RowView, type SynopsisTranslate } from './viewModel'

export interface UseSynopsisNavigation {
  activeId: Ref<string | null>
  ids: ComputedRef<string[]>
  position: ComputedRef<string>
  canPrev: ComputedRef<boolean>
  canNext: ComputedRef<boolean>
  go: (direction: 1 | -1) => string | null
  onKeydown: (event: KeyboardEvent) => void
}

const NEXT_KEYS = new Set(['n', 'j'])
const PREV_KEYS = new Set(['p', 'k'])

function isEditable(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false
  return target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)
}

function prefersReducedMotion(): boolean {
  return typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/** Zeile fokussieren und sichtbar machen; Zeilen tragen `data-row-id` und `tabindex="-1"`. */
export function focusRow(root: HTMLElement | null, id: string): void {
  const target = Array.from(root?.querySelectorAll<HTMLElement>('[data-row-id]') ?? []).find(
    (element) => element.dataset.rowId === id,
  )
  if (!target) return
  target.focus({ preventScroll: true })
  if (typeof target.scrollIntoView === 'function') {
    target.scrollIntoView({ block: 'center', behavior: prefersReducedMotion() ? 'auto' : 'smooth' })
  }
}

/** Navigation zwischen Änderungen mit Schaltflächen und Tasten N/J bzw. P/K. */
export function useSynopsisNavigation(
  rows: ComputedRef<RowView[]>,
  t: SynopsisTranslate,
  root: Ref<HTMLElement | null>,
  onNavigate: (id: string) => void,
): UseSynopsisNavigation {
  const activeId = ref<string | null>(null)
  const ids = computed(() => changeIds(rows.value))
  const index = computed(() => (activeId.value === null ? -1 : ids.value.indexOf(activeId.value)))
  const position = computed(() => positionText(ids.value, activeId.value, t))
  const canPrev = computed(() => ids.value.length > 0 && index.value !== 0)
  const canNext = computed(() => ids.value.length > 0 && index.value !== ids.value.length - 1)

  watch(ids, (next) => {
    if (activeId.value !== null && !next.includes(activeId.value)) activeId.value = null
  })

  function go(direction: 1 | -1): string | null {
    const next = stepChange(ids.value, activeId.value, direction)
    if (next === null) return null
    activeId.value = next
    focusRow(root.value, next)
    onNavigate(next)
    return next
  }

  function onKeydown(event: KeyboardEvent): void {
    if (event.altKey || event.ctrlKey || event.metaKey || isEditable(event.target)) return
    const key = event.key.toLowerCase()
    if (NEXT_KEYS.has(key)) go(1)
    else if (PREV_KEYS.has(key)) go(-1)
    else return
    event.preventDefault()
  }

  return { activeId, ids, position, canPrev, canNext, go, onKeydown }
}
