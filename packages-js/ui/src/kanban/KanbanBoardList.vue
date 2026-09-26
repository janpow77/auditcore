<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { TEMPLATES, type Board, type BoardPort, type BoardSummary } from '@auditcore/kanban-core'
import FaButton from '../base/FaButton.vue'
import FaTextField from '../base/FaTextField.vue'
import { useI18n, type Locale } from '../i18n'
import { relativeTime } from './cardView'
import { kanbanDialogMessages } from './messages'
import { useBoardList } from './useBoardList'

const props = withDefaults(defineProps<{ port?: BoardPort | null; activeId?: string; now?: number; locale?: Locale }>(), { port: null, activeId: '', now: () => Date.now(), locale: undefined })
const emit = defineEmits<{ 'board-select': [boardId: string]; created: [board: Board] }>()
const { t } = useI18n(kanbanDialogMessages, () => props.locale)
const list = useBoardList(() => props.port)
const creating = ref(false)
const title = ref('')
const template = ref('standard')
const confirming = ref<string | null>(null)

onMounted(() => void list.load())
watch(() => props.port, () => void list.load())
defineExpose({ reload: list.load })

function when(summary: BoardSummary): string {
  const age = relativeTime(summary.updated_at, props.now)
  return age ? t(age.key, { count: age.count }) : ''
}

async function create(): Promise<void> {
  const name = title.value.trim()
  if (!name) return
  const chosen = TEMPLATES.find((entry) => entry.key === template.value)
  const board = await list.create(name, chosen?.icon ?? '📋', template.value)
  if (!board) return
  creating.value = false
  title.value = ''
  emit('created', board)
  emit('board-select', board.id)
}

function remove(summary: BoardSummary): void {
  if (confirming.value !== summary.id) {
    confirming.value = summary.id
    return
  }
  confirming.value = null
  void list.remove(summary)
}
</script>

<template>
  <nav class="fa-kanban-boards" :aria-label="t('boardsTitle')">
    <div class="fa-kanban-detail__row" style="justify-content: space-between">
      <strong>{{ t('boardsTitle') }}</strong>
      <FaButton v-if="list.canCreate.value" size="sm" icon="plus" :pressed="creating" @click="creating = !creating">{{ t('newBoard') }}</FaButton>
    </div>
    <form v-if="creating" class="fa-kanban-detail" @submit.prevent="create">
      <FaTextField v-model="title" :label="t('boardTitle')" autofocus required />
      <div class="fa-kanban-boards__templates" role="group" :aria-label="t('template')">
        <button v-for="entry in TEMPLATES" :key="entry.key" type="button" class="fa-kanban-boards__template" :aria-pressed="template === entry.key" @click="template = entry.key">
          <span>{{ entry.icon }} {{ entry.name }}</span>
          <small class="fa-kanban-boards__sub">{{ entry.description }}</small>
        </button>
      </div>
      <FaButton type="submit" variant="primary">{{ t('create') }}</FaButton>
    </form>
    <p v-if="list.error.value" class="fa-field__note" role="alert">{{ list.error.value.message }}</p>
    <template v-for="group in [{ key: 'myBoards', items: list.own.value }, { key: 'sharedBoards', items: list.shared.value }] as const" :key="group.key">
      <p v-if="group.items.length || group.key === 'myBoards'" class="fa-kanban-boards__group">{{ t(group.key) }}</p>
      <p v-if="group.key === 'myBoards' && !group.items.length && !list.loading.value" class="fa-kanban-settings__hint">{{ t('noBoards') }}</p>
      <ul class="fa-kanban-boards__list">
        <li v-for="summary in group.items" :key="summary.id" class="fa-kanban-boards__item" :class="{ 'is-active': summary.id === activeId }">
          <span aria-hidden="true">{{ summary.icon }}</span>
          <button type="button" class="fa-kanban-boards__open" :aria-current="summary.id === activeId ? 'page' : undefined" @click="emit('board-select', summary.id)">
            <span class="fa-kanban-boards__name">{{ summary.title }}</span>
            <span class="fa-kanban-boards__sub">{{ t('tasksDone', { done: summary.stats.done, total: summary.stats.total }) }} · {{ when(summary) }}<template v-if="summary.role !== 'owner'"> · {{ t(`role_${summary.role}` as 'role_edit') }}</template></span>
            <span class="fa-kanban-toolbar__bar" aria-hidden="true"><span :style="{ width: `${summary.stats.progress}%` }" /></span>
          </button>
          <span v-if="summary.role === 'owner'" class="fa-kanban-detail__row">
            <FaButton size="sm" variant="ghost" icon="pin" icon-only :pressed="summary.pinned" :label="summary.pinned ? t('unpin') : t('pin')" @click="list.togglePin(summary)" />
            <FaButton size="sm" :variant="confirming === summary.id ? 'danger' : 'ghost'" icon="trash" :icon-only="confirming !== summary.id" :label="confirming === summary.id ? t('confirmDeleteBoard', { title: summary.title }) : t('deleteBoard', { title: summary.title })" @click="remove(summary)" />
          </span>
        </li>
      </ul>
    </template>
  </nav>
</template>
