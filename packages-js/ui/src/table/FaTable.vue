<script setup lang="ts">
import { computed } from 'vue'
import FaIcon from '../base/FaIcon.vue'
import { baseMessages, useI18n, type Locale } from '../i18n'
import { cellAlignClass, cellText, rowKeyOf, sortIcon } from '@flowaudit/ui-core'
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

function toggleSort(column: TableColumn): void {
  if (!column.sortable) return
  sort.value = nextSort(sort.value, column.key)
  emit('sort-change', sort.value)
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
            :class="cellAlignClass(column)"
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
              <FaIcon :name="sortIcon(sort, column.key)" :size="14" />
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
          :key="rowKeyOf(row, rowKey, index)"
          :tabindex="clickable ? 0 : undefined"
          @click="clickable && emit('row-click', row)"
          @keydown.enter="clickable && emit('row-click', row)"
        >
          <td v-for="column in columns" :key="column.key" :class="cellAlignClass(column)">
            <slot :name="`cell-${column.key}`" :row="row" :value="row[column.key]">{{ cellText(column, row) }}</slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
