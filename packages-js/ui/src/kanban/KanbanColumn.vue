<script setup lang="ts">
import { computed } from 'vue'
import type { Card } from '@auditcore/kanban-core'
import FaButton from '../base/FaButton.vue'
import { useI18n, type Locale } from '../i18n'
import KanbanCard from './KanbanCard.vue'
import { kanbanMessages } from './messages'
import type { ColumnView } from './useKanbanBoard'

const props = withDefaults(defineProps<{
  view: ColumnView
  doneColumnId: string
  today: string
  canCreate?: boolean
  canToggle?: boolean
  grabbedId?: string | null
  draggingId?: string | null
  instructionsId?: string
  locale?: Locale
}>(), { canCreate: false, canToggle: false, grabbedId: null, draggingId: null, instructionsId: undefined, locale: undefined })

const emit = defineEmits<{
  add: [columnId: string]
  open: [card: Card]
  'toggle-done': [card: Card]
  'card-keydown': [event: KeyboardEvent, card: Card]
  'card-pointerdown': [event: PointerEvent, card: Card]
}>()

const { t } = useI18n(kanbanMessages, () => props.locale)
const headingId = computed(() => `fa-kanban-column-${props.view.column.id}`)
const limit = computed(() => props.view.wip?.limit ?? null)
const countClass = computed(() => ({ 'is-full': props.view.wip?.full, 'is-over': props.view.wip?.over }))
const countLabel = computed(() => (limit.value === null ? t('cardCount', { count: props.view.total }) : t('wipLimit', { count: props.view.total, limit: limit.value })))
</script>

<template>
  <section
    class="fa-kanban-column"
    :class="{ 'fa-kanban-column--over-limit': view.wip?.over }"
    :style="{ '--fa-kanban-column-color': view.column.color }"
    :data-column-id="view.column.id"
    :aria-labelledby="headingId"
  >
    <header class="fa-kanban-column__head">
      <h2 :id="headingId" class="fa-kanban-column__name">
        <span class="fa-kanban-column__dot" aria-hidden="true" />
        {{ view.column.label }}
      </h2>
      <span class="fa-kanban-column__count" :class="countClass" :title="countLabel" :aria-label="countLabel">
        {{ limit === null ? view.total : `${view.total}/${limit}` }}
      </span>
      <FaButton
        v-if="canCreate"
        size="sm"
        variant="ghost"
        icon="plus"
        icon-only
        :label="t('addCardIn', { column: view.column.label })"
        @click="emit('add', view.column.id)"
      />
    </header>
    <div class="fa-kanban-column__list" role="list" :aria-labelledby="headingId" data-card-list>
      <KanbanCard
        v-for="card in view.cards"
        :key="card.id"
        :card="card"
        :done="card.column_id === doneColumnId"
        :today="today"
        :can-toggle="canToggle"
        :grabbed="grabbedId === card.id"
        :dragging="draggingId === card.id"
        :described-by="instructionsId"
        :locale="locale"
        @open="emit('open', $event)"
        @toggle-done="emit('toggle-done', $event)"
        @keydown="emit('card-keydown', $event, card)"
        @pointerdown="emit('card-pointerdown', $event, card)"
      />
      <p v-if="view.cards.length === 0" class="fa-kanban-column__empty">{{ t('emptyColumn') }}</p>
    </div>
    <FaButton v-if="canCreate" class="fa-kanban-column__add" size="sm" variant="ghost" icon="plus" @click="emit('add', view.column.id)">
      {{ t('addCard') }}
    </FaButton>
  </section>
</template>
