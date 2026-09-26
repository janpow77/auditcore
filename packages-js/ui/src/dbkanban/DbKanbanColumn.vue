<script setup lang="ts">
import { dbKanbanMessages, type DbColumnView } from '@auditcore/ui-core'
import FaButton from '../base/FaButton.vue'
import { useId } from '../composables/useId'
import { useI18n } from '../i18n'
import DbKanbanCard from './DbKanbanCard.vue'

const props = withDefaults(defineProps<{
  column: DbColumnView
  editable?: boolean
  canAdd?: boolean
  dragging?: string | null
  over?: boolean
  hintId?: string
}>(), { editable: true, canAdd: false, dragging: null, over: false, hintId: undefined })

const emit = defineEmits<{
  'card-drag': [id: string | null]
  'card-step': [id: string, direction: 1 | -1]
  'card-drop': [id: string, column: string]
  'column-over': [column: string | null]
  'card-add': [column: string]
}>()
const { t } = useI18n(dbKanbanMessages)
const headingId = useId('fa-db-kanban-column')

function onDragOver(event: DragEvent): void {
  if (!props.editable) return
  event.preventDefault()
  if (!props.over) emit('column-over', props.column.value)
}

function onDrop(event: DragEvent): void {
  if (!props.editable) return
  event.preventDefault()
  const id = event.dataTransfer?.getData('text/plain') || props.dragging
  if (id) emit('card-drop', id, props.column.value)
}
</script>

<template>
  <section
    class="fa-db-kanban-column"
    :class="{ 'fa-db-kanban-column--over': over, 'fa-db-kanban-column--empty-value': column.value === '' }"
    :aria-labelledby="headingId"
    :data-column="column.value"
    @dragover="onDragOver"
    @dragleave.self="emit('column-over', null)"
    @drop="onDrop"
  >
    <header class="fa-db-kanban-column__head">
      <h3 :id="headingId" class="fa-db-kanban-column__name">{{ column.label }}</h3>
      <span class="fa-db-kanban-column__count">{{ column.countText }}</span>
    </header>
    <ul class="fa-db-kanban-column__list" :aria-labelledby="headingId">
      <DbKanbanCard
        v-for="card in column.cards"
        :key="card.id"
        :card="card"
        :column-label="column.label"
        :editable="editable"
        :dragging="dragging === card.id"
        :described-by="hintId"
        @card-drag="emit('card-drag', $event)"
        @card-step="(id, direction) => emit('card-step', id, direction)"
      />
    </ul>
    <p v-if="column.cards.length === 0" class="fa-db-kanban-column__empty">{{ t('columnEmpty') }}</p>
    <FaButton
      v-if="editable && canAdd"
      class="fa-db-kanban-column__add"
      size="sm"
      variant="ghost"
      icon="plus"
      :aria-label="t('addCardIn', { label: column.label })"
      @click="emit('card-add', column.value)"
    >{{ t('addCard') }}</FaButton>
  </section>
</template>
