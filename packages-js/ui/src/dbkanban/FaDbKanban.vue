<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { createMemoryRecordPort, type RecordPort, type RecordRow, type RecordTable } from '@auditcore/kanban-core'
import { dbKanbanMessages, type DbKanbanError, type RecordMove } from '@auditcore/ui-core'
import FaTextField from '../base/FaTextField.vue'
import { useId } from '../composables/useId'
import { provideLocale, useI18n, type Locale } from '../i18n'
import DbKanbanColumn from './DbKanbanColumn.vue'
import { useDbKanban } from './useDbKanban'

const props = withDefaults(defineProps<{
  /** Datenquelle (Datenbank/REST der Anwendung) mit `load`, `updateCell` und optional `addRow`. */
  port?: RecordPort | null
  /** Ohne Port: Tabelle direkt übergeben; Änderungen kommen als Ereignis `table-change` zurück. */
  table?: RecordTable | null
  /** `false`: nur Ansicht, kein Verschieben und Anlegen. */
  editable?: boolean
  locale?: Locale
}>(), { port: null, table: null, editable: true, locale: undefined })

const emit = defineEmits<{
  'record-move': [move: RecordMove]
  'record-add': [row: RecordRow]
  'table-change': [table: RecordTable]
  error: [error: DbKanbanError]
}>()

/** Eigenschaft, nach der gruppiert wird (`v-model:group-by`); leer: erste Auswahl-Eigenschaft. */
const groupBy = defineModel<string>('groupBy', { default: '' })

const { t, locale: active } = useI18n(dbKanbanMessages, () => props.locale)
provideLocale(active)
const root = ref<HTMLElement | null>(null)
const id = useId('fa-db-kanban')
const source = computed<RecordPort | null>(() => props.port ?? (props.table ? createMemoryRecordPort(props.table, { onChange: (next) => emit('table-change', next) }) : null))
const { controller, state, view } = useDbKanban(
  { port: () => source.value, t: () => t, lang: () => active.value, editable: () => props.editable },
  {
    onMoved: (move) => emit('record-move', move),
    onAdded: (row) => emit('record-add', row),
    onGroupBy: (propertyId) => (groupBy.value = propertyId),
    onError: (error) => emit('error', error),
  },
)
const canAdd = computed(() => Boolean(source.value?.addRow))

watch(source, () => void controller.load(groupBy.value), { immediate: true })
watch(groupBy, (value) => {
  if (value) controller.setGroupBy(value)
})

async function step(rowId: string, direction: 1 | -1): Promise<void> {
  if (await controller.moveBy(rowId, direction)) {
    await nextTick()
    root.value?.querySelector<HTMLElement>(`[data-card-id="${CSS.escape(rowId)}"]`)?.focus()
  }
}
</script>

<template>
  <section ref="root" class="fa-db-kanban" :aria-labelledby="`${id}-title`" :aria-busy="state.busy !== null || undefined">
    <header class="fa-db-kanban__toolbar">
      <h2 :id="`${id}-title`" class="fa-db-kanban__title">{{ t('title') }}</h2>
      <div v-if="view.groupOptions.length" class="fa-db-kanban__group">
        <label :for="`${id}-group`">{{ t('groupByLabel') }}</label>
        <select :id="`${id}-group`" :value="state.groupBy" @change="controller.setGroupBy(($event.target as HTMLSelectElement).value)">
          <option v-for="option in view.groupOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
        </select>
      </div>
      <FaTextField v-if="state.table" class="fa-db-kanban__search" :model-value="state.query" type="search" :label="t('searchLabel')" @update:model-value="controller.setQuery" />
      <span v-if="!editable" class="fa-db-kanban__readonly">{{ t('readOnly') }}</span>
    </header>
    <p :id="`${id}-hint`" class="fa-sr-only">{{ t('moveHint') }}</p>
    <p class="fa-sr-only" role="status" aria-live="polite">{{ view.busyText || state.notice }}</p>
    <p v-if="!source" class="fa-db-kanban__state fa-db-kanban__state--error" role="alert">{{ t('noPort') }}</p>
    <p v-else-if="state.error" class="fa-db-kanban__state fa-db-kanban__state--error" role="alert">{{ state.error.message }}</p>
    <p v-if="view.notice" class="fa-db-kanban__state">{{ view.notice }}</p>
    <p v-if="view.noMatches" class="fa-db-kanban__state">{{ t('noMatches') }}</p>
    <div v-if="view.columns.length" class="fa-db-kanban__columns">
      <DbKanbanColumn
        v-for="column in view.columns"
        :key="column.value"
        :column="column"
        :editable="editable"
        :can-add="canAdd"
        :dragging="state.dragging"
        :over="state.dropTarget === column.value"
        :hint-id="`${id}-hint`"
        @card-drag="controller.startDrag"
        @card-step="step"
        @card-drop="controller.move"
        @column-over="controller.setDropTarget"
        @card-add="controller.addCard"
      />
    </div>
  </section>
</template>
