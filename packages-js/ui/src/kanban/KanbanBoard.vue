<script setup lang="ts">
import { computed, onMounted, ref, shallowRef, watch } from 'vue'
import { doneColumn, findCard, MemoryBoardPort, type Attachment, type Board, type BoardPort, type Card, type CardLink, type KanbanError, type SharePermission, type UserRef } from '@auditcore/kanban-core'
import FaIcon from '../base/FaIcon.vue'
import FaButton from '../base/FaButton.vue'
import { useId } from '../composables/useId'
import { useI18n, type Locale } from '../i18n'
import { handleCardKey } from './cardKeys'
import KanbanCard from './KanbanCard.vue'
import KanbanCardDetail from './KanbanCardDetail.vue'
import KanbanColumn from './KanbanColumn.vue'
import KanbanSettingsDialog from './KanbanSettingsDialog.vue'
import KanbanShareDialog from './KanbanShareDialog.vue'
import KanbanToolbar from './KanbanToolbar.vue'
import { kanbanMessages } from './messages'
import { useBoardShortcuts } from './useBoardShortcuts'
import { useKanbanActions } from './useKanbanActions'
import { useKanbanBoard } from './useKanbanBoard'
import { useKanbanFilter } from './useKanbanFilter'
import { useMoveController } from './useMoveController'
import { usePointerDrag } from './usePointerDrag'

const props = withDefaults(defineProps<{
  /** Speicher-/Rechte-Port; ohne Port wird `board` lokal (In-Memory) bearbeitet. */
  port?: BoardPort | null
  boardId?: string
  board?: Board | null
  userId?: string
  users?: readonly UserRef[]
  readOnly?: boolean
  sharedByName?: string
  showFullscreen?: boolean
  today?: string
  locale?: Locale
}>(), { port: null, boardId: '', board: null, userId: '', users: () => [], readOnly: false, sharedByName: '', showFullscreen: true, today: undefined, locale: undefined })

const emit = defineEmits<{
  'board-change': [board: Board]
  error: [error: KanbanError]
  fullscreen: []
  navigate: [link: CardLink, card: Card]
  attachment: [attachment: Attachment, card: Card]
  'card-open': [card: Card]
}>()

const { t } = useI18n(kanbanMessages, () => props.locale)
const root = ref<HTMLElement | null>(null)
const toolbar = ref<InstanceType<typeof KanbanToolbar> | null>(null)
const instructionsId = useId('fa-kanban-help')
const localPort = shallowRef<BoardPort | null>(null)
watch(() => [props.board, props.userId] as const, ([board, userId]) => {
  localPort.value = board ? new MemoryBoardPort({ userId: userId || board.owner_id, boards: [board], users: props.users }) : null
}, { immediate: true })
const port = computed(() => props.port ?? localPort.value)
const boardId = computed(() => props.boardId || props.board?.id || '')

const filter = useKanbanFilter()
const state = useKanbanBoard({
  port: () => port.value, boardId: () => boardId.value, criteria: () => filter.criteria.value,
  readOnly: () => props.readOnly, today: () => props.today,
  onError: (error) => emit('error', error), onChange: (board) => emit('board-change', board),
})
const actions = useKanbanActions(state)
const mover = useMoveController(state, actions, t, root)
const pointer = usePointerDrag(mover, root, () => state.can.value.move)
const { board: current, can, stats, error, loading } = state
const selectedId = ref<string | null>(null)
const selected = computed(() => (current.value && selectedId.value ? findCard(current.value, selectedId.value) ?? null : null))
const dialog = ref<'settings' | 'share' | null>(null)
const doneId = computed(() => (current.value ? doneColumn(current.value).id : ''))
const searchUsers = computed(() => {
  const current = port.value
  return current?.searchUsers ? (query: string) => current.searchUsers?.(query) ?? Promise.resolve([]) : null
})
const readOnlyView = computed(() => current.value !== null && !can.value.edit && !can.value.move)

onMounted(() => void state.load())
useBoardShortcuts(root, (shortcut) => {
  if (shortcut === 'fullscreen') emit('fullscreen')
  else if (shortcut === 'search') toolbar.value?.focusSearch()
  else if (current.value?.columns[0]) void addCard(current.value.columns[0].id)
})

function open(card: Card): void {
  if (pointer.consumeClick()) return
  selectedId.value = card.id
  emit('card-open', card)
}

async function addCard(columnId: string): Promise<void> {
  if (!can.value.create) return
  const known = new Set(current.value?.cards.map((card) => card.id))
  const result = await actions.addCard(columnId, { title: t('newCardTitle') })
  const created = result?.board.cards.find((card) => !known.has(card.id))
  if (created) selectedId.value = created.id
}

function onCardKey(event: KeyboardEvent, card: Card): void {
  if (handleCardKey(event, card, mover.grabbed.value, mover, open)) event.preventDefault()
}

async function removeCard(card: Card): Promise<void> {
  if (await actions.remove(card.id)) selectedId.value = null
}

async function saveColumns(columns: Parameters<typeof actions.configure>[0]): Promise<void> {
  if (await actions.configure(columns)) dialog.value = null
}

function share(userId: string, permission: SharePermission): void {
  void actions.share(userId, permission)
}

defineExpose({ reload: state.load, board: current })
</script>

<template>
  <div ref="root" class="fa-kanban" :aria-busy="loading || undefined">
    <p :id="instructionsId" class="fa-sr-only">{{ t('moveInstructions') }}</p>
    <p class="fa-sr-only" role="status" aria-live="polite" aria-atomic="true">{{ mover.announcement.value }}</p>
    <div v-if="readOnlyView" class="fa-kanban__banner"><FaIcon name="lock" :size="16" /> {{ sharedByName ? `${t('sharedBy', { name: sharedByName })} – ` : '' }}{{ t('readOnly') }}</div>
    <div v-if="error" class="fa-kanban__error" role="alert">
      {{ t('errorPrefix', { message: error.message }) }}
      <FaButton v-if="!current" size="sm" @click="state.load()">{{ t('retry') }}</FaButton>
    </div>
    <p v-if="loading && !current" class="fa-kanban__loading">{{ t('loading') }}</p>
    <template v-if="current">
      <KanbanToolbar
        ref="toolbar"
        :title="current.title"
        :stats="stats"
        :filter="filter.state"
        :filter-active="filter.active.value"
        :can-rename="can.rename"
        :can-share="can.share"
        :can-configure="can.configure"
        :show-fullscreen="showFullscreen"
        :locale="locale"
        @rename="actions.rename"
        @share="dialog = 'share'"
        @settings="dialog = 'settings'"
        @fullscreen="emit('fullscreen')"
        @reset-filter="filter.reset"
        @filter-change="Object.assign(filter.state, $event)"
      />
      <div class="fa-kanban__columns" :aria-label="t('board')" role="group">
        <KanbanColumn
          v-for="view in mover.columns.value"
          :key="view.column.id"
          :view="view"
          :done-column-id="doneId"
          :today="state.today.value"
          :can-create="can.create"
          :can-toggle="can.move"
          :grabbed-id="mover.grabbed.value"
          :dragging-id="pointer.drag.value.active ? pointer.drag.value.card?.id ?? null : null"
          :instructions-id="instructionsId"
          :locale="locale"
          @add="addCard"
          @open="open"
          @toggle-done="actions.toggle"
          @card-keydown="onCardKey"
          @card-pointerdown="pointer.onPointerDown"
        />
      </div>
      <KanbanCard
        v-if="pointer.drag.value.active && pointer.drag.value.card"
        class="fa-kanban-card--ghost"
        aria-hidden="true"
        :card="pointer.drag.value.card"
        :today="state.today.value"
        :locale="locale"
        :style="{ left: `${pointer.drag.value.x - pointer.drag.value.offsetX}px`, top: `${pointer.drag.value.y - pointer.drag.value.offsetY}px`, width: `${pointer.drag.value.width}px` }"
      />
      <KanbanCardDetail
        :card="selected"
        :columns="current.columns"
        :read-only="!can.edit"
        :can-delete="can.delete"
        :locale="locale"
        @close="selectedId = null"
        @update="selected && actions.editCard(selected.id, $event)"
        @delete="removeCard"
        @navigate="selected && emit('navigate', $event, selected)"
        @attachment="selected && emit('attachment', $event, selected)"
      >
        <template #extra="{ card }"><slot name="card-extra" :card="card" /></template>
      </KanbanCardDetail>
      <KanbanSettingsDialog :open="dialog === 'settings'" :columns="current.columns" :locale="locale" @close="dialog = null" @save="saveColumns" />
      <KanbanShareDialog
        :open="dialog === 'share'"
        :shares="current.shares"
        :search="searchUsers"
        :users="users"
        :locale="locale"
        @close="dialog = null"
        @share="share"
        @revoke="actions.revoke"
      />
    </template>
  </div>
</template>
