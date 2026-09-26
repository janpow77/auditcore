import { computed, reactive, ref, shallowRef, watch, type ComputedRef, type Ref, type ShallowRef } from 'vue'
import type { Locale } from '../i18n/i18n'
import { useI18n } from '../i18n/i18n'
import { synopsisMessages } from './messages'
import type { SynopsisPort } from './port'
import { CHANGE_STATUSES, type Comparison, type ComparisonResult, type CompareRow, type RowUpdate } from './types'
import { applyRowOverrides, buildSynopsisView, filterRows, type RowView, type SynopsisTranslate, type SynopsisView } from './viewModel'

/** Eingaben der Komponente, als Getter übergeben (Props bleiben reaktiv). */
export interface SynopsisSource {
  comparison: () => Comparison | null | undefined
  result: () => ComparisonResult | null | undefined
  comparisonId: () => string | undefined
  port: () => SynopsisPort | null | undefined
  title: () => string | undefined
  oldLabel: () => string | undefined
  newLabel: () => string | undefined
  locale: () => Locale | undefined
}

export interface SynopsisFilterState {
  statuses: string[]
  query: string
  onlySelected: boolean
  /** `null`: Vorgabe aus `metadata.highlight_words`. */
  highlight: boolean | null
}

export interface UseSynopsis {
  t: SynopsisTranslate
  locale: ComputedRef<Locale>
  loading: Ref<boolean>
  error: Ref<string>
  filter: SynopsisFilterState
  result: ComputedRef<ComparisonResult | null>
  view: ComputedRef<SynopsisView | null>
  rows: ComputedRef<RowView[]>
  selectedText: ComputedRef<string>
  currentId: ComputedRef<string | undefined>
  loaded: ShallowRef<Comparison | null>
  updateRow: (id: string, patch: Omit<RowUpdate, 'row_id'>) => Promise<RowUpdate>
  toggleStatus: (status: string, enabled: boolean) => void
  setAllChanges: () => void
  reload: () => Promise<void>
}

function useLoader(source: SynopsisSource, t: SynopsisTranslate) {
  const loaded = shallowRef<Comparison | null>(null)
  const loading = ref(false)
  const error = ref('')
  async function reload(): Promise<void> {
    const id = source.comparisonId()
    const port = source.port()
    if (!id || !port || source.comparison() || source.result()) return
    loading.value = true
    error.value = ''
    try {
      loaded.value = await port.load(id)
    } catch {
      error.value = t('loadError')
    } finally {
      loading.value = false
    }
  }
  watch([source.comparisonId, source.port], () => void reload(), { immediate: true })
  return { loaded, loading, error, reload }
}

export function useSynopsis(source: SynopsisSource): UseSynopsis {
  const { t, locale } = useI18n(synopsisMessages, source.locale)
  const { loaded, loading, error, reload } = useLoader(source, t)
  const overrides = reactive(new Map<string, Partial<CompareRow>>())
  const filter = reactive<SynopsisFilterState>({ statuses: [...CHANGE_STATUSES], query: '', onlySelected: false, highlight: null })

  const comparison = computed(() => source.comparison() ?? loaded.value)
  const currentId = computed(() => comparison.value?.id ?? source.comparisonId())
  const base = computed(() => source.result() ?? comparison.value?.result ?? null)
  watch(base, () => overrides.clear())

  const result = computed<ComparisonResult | null>(() => {
    const value = base.value
    return value ? { ...value, rows: applyRowOverrides(value.rows, overrides) } : null
  })
  const view = computed<SynopsisView | null>(() => {
    if (!result.value) return null
    return buildSynopsisView(result.value, t, {
      title: source.title() || comparison.value?.title,
      oldLabel: source.oldLabel(),
      newLabel: source.newLabel(),
      highlight: filter.highlight ?? undefined,
    })
  })
  const rows = computed(() => (view.value ? filterRows(view.value.rows, filter) : []))
  const selectedText = computed(() => {
    const all = view.value?.rows ?? []
    return t('selectedCount', { count: all.filter((row) => row.selected).length, total: all.length })
  })

  async function updateRow(id: string, patch: Omit<RowUpdate, 'row_id'>): Promise<RowUpdate> {
    overrides.set(id, { ...overrides.get(id), ...patch })
    const update: RowUpdate = { row_id: id, ...patch }
    const port = source.port()
    const target = currentId.value
    if (port?.updateRows && target) {
      try {
        await port.updateRows(target, [update])
        error.value = ''
      } catch {
        error.value = t('saveError')
      }
    }
    return update
  }

  function toggleStatus(status: string, enabled: boolean): void {
    const next = new Set(filter.statuses)
    if (enabled) next.add(status)
    else next.delete(status)
    filter.statuses = [...next]
  }

  function setAllChanges(): void {
    filter.statuses = [...CHANGE_STATUSES]
  }

  return { t, locale, loading, error, filter, result, view, rows, selectedText, currentId, loaded, updateRow, toggleStatus, setAllChanges, reload }
}
