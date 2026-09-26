import { ariaSort, bearerHeaders, debounce, isTokenExpired, nextSort, sortRows, type Debounced, type SortState, type TableRow, type TokenStore } from '@auditcore/common'
import { useCallback, useEffect, useMemo, useRef, useState, useSyncExternalStore } from 'react'

export interface UseSortOptions {
  initial?: SortState | null
  locale?: string
  /** `tri` (Standard) oder `bi`, siehe `nextSort`. */
  cycle?: 'bi' | 'tri'
}

export interface UseSort<R extends TableRow> {
  sort: SortState | null
  sorted: R[]
  toggle: (key: string) => void
  setSort: (sort: SortState | null) => void
  ariaSortFor: (key: string) => 'ascending' | 'descending' | 'none'
}

/** Sortierzustand und sortierte Zeilen (Kern `table/sort` aus `@auditcore/common`). */
export function useSort<R extends TableRow>(rows: readonly R[], options: UseSortOptions = {}): UseSort<R> {
  const [sort, setSort] = useState<SortState | null>(options.initial ?? null)
  const { locale, cycle } = options
  const sorted = useMemo(() => sortRows(rows, sort, locale), [rows, sort, locale])
  const toggle = useCallback((key: string) => setSort((current) => nextSort(current, key, { cycle })), [cycle])
  const ariaSortFor = useCallback((key: string) => ariaSort(sort, key), [sort])
  return { sort, sorted, toggle, setSort, ariaSortFor }
}

/**
 * Entprellte, stabile Funktion; ruft immer die neueste `fn` auf und verwirft
 * einen ausstehenden Aufruf beim Unmount.
 */
export function useDebouncedCallback<A extends unknown[]>(fn: (...args: A) => void, ms: number): Debounced<A> {
  const latest = useRef(fn)
  latest.current = fn
  const debounced = useMemo(() => debounce((...args: A) => latest.current(...args), ms), [ms])
  useEffect(() => () => debounced.cancel(), [debounced])
  return debounced
}

export interface UseAuthToken {
  token: string | null
  headers: Record<string, string>
  expired: boolean
  set: (token: string) => void
  clear: () => void
}

/** Zugangstoken aus einem `TokenStore` (`@auditcore/common`), neu gerendert bei jeder Änderung. */
export function useAuthToken(store: TokenStore): UseAuthToken {
  const subscribe = useCallback((notify: () => void) => store.subscribe(notify), [store])
  const token = useSyncExternalStore(subscribe, store.get, store.get)
  return useMemo(
    () => ({
      token,
      headers: bearerHeaders({ get: () => token }),
      expired: token ? isTokenExpired(token) : true,
      set: (value: string) => store.set(value),
      clear: () => store.clear(),
    }),
    [store, token],
  )
}
