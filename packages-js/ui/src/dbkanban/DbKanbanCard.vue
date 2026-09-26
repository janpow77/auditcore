<script setup lang="ts">
import { computed } from 'vue'
import { dbKanbanMessages, type DbCardView } from '@auditcore/ui-core'
import { useI18n } from '../i18n'

const props = withDefaults(defineProps<{
  card: DbCardView
  columnLabel: string
  editable?: boolean
  dragging?: boolean
  describedBy?: string
}>(), { editable: true, dragging: false, describedBy: undefined })

const emit = defineEmits<{ 'card-drag': [id: string | null]; 'card-step': [id: string, direction: 1 | -1] }>()
const { t } = useI18n(dbKanbanMessages)
const label = computed(() => t('cardLabel', { title: props.card.title, label: props.columnLabel }))

function onDragStart(event: DragEvent): void {
  event.dataTransfer?.setData('text/plain', props.card.id)
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move'
  emit('card-drag', props.card.id)
}

function onKeydown(event: KeyboardEvent): void {
  if (!props.editable || !(event.ctrlKey || event.metaKey)) return
  if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return
  event.preventDefault()
  emit('card-step', props.card.id, event.key === 'ArrowRight' ? 1 : -1)
}
</script>

<template>
  <li
    class="fa-db-kanban-card"
    :class="{ 'fa-db-kanban-card--dragging': dragging }"
    :data-card-id="card.id"
    tabindex="0"
    :draggable="editable ? 'true' : 'false'"
    :aria-label="label"
    :aria-describedby="editable ? describedBy : undefined"
    @dragstart="onDragStart"
    @dragend="emit('card-drag', null)"
    @keydown="onKeydown"
  >
    <p class="fa-db-kanban-card__title">{{ card.title }}</p>
    <dl v-if="card.fields.length" class="fa-db-kanban-card__fields">
      <div v-for="field in card.fields" :key="field.id" class="fa-db-kanban-card__field">
        <dt>{{ field.label }}</dt>
        <dd>{{ field.text }}</dd>
      </div>
    </dl>
  </li>
</template>
