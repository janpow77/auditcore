<script setup lang="ts">
import { computed } from 'vue'
import FaIcon from '../base/FaIcon.vue'
import { baseMessages, useI18n, type Locale } from '../i18n'
import { ariaSort, nextSort, sortRows, type SortState, type TableColumn, type TableRow } from './sort'

const props = withDefaults(defineProps<{
  columns?: readonly TableColumn[]
  rows?: readonly TableRow[]
  rowKey?: string
  caption?: string
  emptyText?: string
  /** Zeilen sind anklickbar (Maus und Enter) und lösen `row-click` aus. */
  clickable?: boolean
  locale?: Locale
}>(), { columns: () => [], rows: () => [], rowKey: 'id', caption: '', emptyText: '', clickable: false, locale: undefined })

const emit = defineEmits<{ 'row-click': [row: TableRow]; 'sort-change': [sort: SortState | null] }>()
const sort = defineModel<SortState | null>('sort', { default: null })
const { t, locale: activeLocale } = useI18n(baseMessages, () => props.locale)

const sortedRows = computed(() => sortRows(props.rows, sort.value, activeLocale.value))

function cellText(column: TableColumn, row: TableRow): string {
  const value = row[column.key]
  if (column.format) return column.format(value, row)
  return value === null || value === undefined ? '' : String(value)
}

function toggleSort(column: TableColumn): void {
  if (!column.sortable) return
  sort.value = nextSort(sort.value, column.key)
  emit('sort-change', sort.value)
}

function sortIcon(key: string): 'sort' | 'sort-asc' | 'sort-desc' {
  const state = ariaSort(sort.value, key)
  return state === 'ascending' ? 'sort-asc' : state === 'descending' ? 'sort-desc' : 'sort'
}

function keyOf(row: TableRow, index: number): string {
  const value = row[props.rowKey]
  return typeof value === 'string' || typeof value === 'number' ? String(value) : `row-${index}`
}
</script>

<template>
  <div class="fa-table-wrap">
    <table class="fa-table" :class="{ 'fa-table--clickable': clickable }">
      <caption v-if="caption" class="fa-table__caption">{{ caption }}</caption>
      <thead>
        <tr>
          <th
            v-for="column in columns"
            :key="column.key"
            scope="col"
            :class="`fa-table__cell--${column.align ?? 'start'}`"
            :aria-sort="column.sortable ? ariaSort(sort, column.key) : undefined"
          >
            <button
              v-if="column.sortable"
              type="button"
              class="fa-table__sort"
              :aria-label="t('sortBy', { column: column.label })"
              @click="toggleSort(column)"
            >
              <span>{{ column.label }}</span>
              <FaIcon :name="sortIcon(column.key)" :size="14" />
            </button>
            <span v-else>{{ column.label }}</span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="sortedRows.length === 0">
          <td class="fa-table__empty" :colspan="columns.length">{{ emptyText || t('tableEmpty') }}</td>
        </tr>
        <tr
          v-for="(row, index) in sortedRows"
          :key="keyOf(row, index)"
          :tabindex="clickable ? 0 : undefined"
          @click="clickable && emit('row-click', row)"
          @keydown.enter="clickable && emit('row-click', row)"
        >
          <td v-for="column in columns" :key="column.key" :class="`fa-table__cell--${column.align ?? 'start'}`">
            <slot :name="`cell-${column.key}`" :row="row" :value="row[column.key]">{{ cellText(column, row) }}</slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style>
.fa-table-wrap { overflow-x: auto; border: 1px solid var(--fa-color-border); border-radius: var(--fa-radius); background: var(--fa-color-surface); }
.fa-table { width: 100%; border-collapse: collapse; font: var(--fa-font-size-sm) / var(--fa-line-height) var(--fa-font-sans); color: var(--fa-color-text); }
.fa-table__caption { caption-side: top; text-align: start; padding: var(--fa-space-3) var(--fa-space-4); font-weight: 600; }
.fa-table th, .fa-table td { padding: var(--fa-space-2) var(--fa-space-4); border-bottom: 1px solid var(--fa-color-border); }
.fa-table th { background: var(--fa-color-surface-raised); font-size: var(--fa-font-size-xs); font-weight: 600; color: var(--fa-color-text-muted); text-transform: uppercase; letter-spacing: 0.04em; }
.fa-table tbody tr:last-child td { border-bottom: none; }
.fa-table--clickable tbody tr { cursor: pointer; }
.fa-table--clickable tbody tr:hover { background: var(--fa-color-surface-sunken); }
.fa-table tbody tr:focus-visible { outline: none; box-shadow: inset var(--fa-focus-ring); }
.fa-table__cell--end { text-align: end; font-variant-numeric: tabular-nums; }
.fa-table__cell--center { text-align: center; }
.fa-table__sort { display: inline-flex; align-items: center; gap: var(--fa-space-1); padding: 0; border: 0; background: none; color: inherit; font: inherit; text-transform: inherit; letter-spacing: inherit; cursor: pointer; }
.fa-table__sort:focus-visible { outline: none; box-shadow: var(--fa-focus-ring); border-radius: var(--fa-radius-sm); }
.fa-table__empty { text-align: center; color: var(--fa-color-text-muted); padding: var(--fa-space-5); }
</style>
