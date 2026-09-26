import { ariaSort, nextSort, sortRows, type SortState, type TableRow } from '@auditcore/common'
import { computed, ref, toValue, type ComputedRef, type MaybeRefOrGetter, type Ref } from 'vue'

export interface UseSortOptions {
  initial?: SortState | null
  locale?: string
  /** `tri` (Standard) oder `bi`, siehe `nextSort`. */
  cycle?: 'bi' | 'tri'
}

export interface UseSort<R extends TableRow> {
  sort: Ref<SortState | null>
  sorted: ComputedRef<R[]>
  toggle: (key: string) => void
  ariaSortFor: (key: string) => 'ascending' | 'descending' | 'none'
}

/** Sortierzustand und sortierte Zeilen für eigene Tabellen (FaTable sortiert selbst). */
export function useSort<R extends TableRow>(rows: MaybeRefOrGetter<readonly R[]>, options: UseSortOptions = {}): UseSort<R> {
  const sort = ref<SortState | null>(options.initial ?? null)
  const sorted = computed(() => sortRows(toValue(rows), sort.value, options.locale))
  return {
    sort,
    sorted,
    toggle: (key) => {
      sort.value = nextSort(sort.value, key, { cycle: options.cycle })
    },
    ariaSortFor: (key) => ariaSort(sort.value, key),
  }
}
