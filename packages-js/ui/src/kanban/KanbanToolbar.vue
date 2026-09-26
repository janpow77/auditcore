<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { DUE_STATES, PRIORITIES, type BoardStats } from '@auditcore/kanban-core'
import FaButton from '../base/FaButton.vue'
import FaTextField from '../base/FaTextField.vue'
import { useI18n, type Locale } from '../i18n'
import { kanbanMessages } from './messages'
import type { KanbanFilterState } from './useKanbanFilter'

const props = withDefaults(defineProps<{
  title: string
  stats: BoardStats | null
  filter: KanbanFilterState
  filterActive?: boolean
  canRename?: boolean
  canShare?: boolean
  canConfigure?: boolean
  showFullscreen?: boolean
  locale?: Locale
}>(), { filterActive: false, canRename: false, canShare: false, canConfigure: false, showFullscreen: true, locale: undefined })

const emit = defineEmits<{ rename: [title: string]; share: []; settings: []; fullscreen: []; 'reset-filter': []; 'filter-change': [patch: Partial<KanbanFilterState>] }>()
const { t } = useI18n(kanbanMessages, () => props.locale)
const editing = ref(false)
const draft = ref('')
const input = ref<HTMLInputElement | null>(null)
const search = ref<InstanceType<typeof FaTextField> | null>(null)

async function startRename(): Promise<void> {
  if (!props.canRename) return
  draft.value = props.title
  editing.value = true
  await nextTick()
  input.value?.select()
}

function commitRename(): void {
  if (!editing.value) return
  editing.value = false
  const value = draft.value.trim()
  if (value && value !== props.title) emit('rename', value)
}

function focusSearch(): void {
  ;(search.value?.$el as HTMLElement | undefined)?.querySelector('input')?.focus()
}

defineExpose({ focusSearch })
</script>

<template>
  <div class="fa-kanban-toolbar">
    <div class="fa-kanban-toolbar__title">
      <input
        v-if="editing"
        ref="input"
        v-model="draft"
        class="fa-kanban-toolbar__title-input"
        :aria-label="t('renameLabel')"
        @blur="commitRename"
        @keydown.enter.prevent="commitRename"
        @keydown.esc.prevent="editing = false"
      />
      <h1 v-else class="fa-kanban-toolbar__heading">
        <button v-if="canRename" type="button" class="fa-kanban-toolbar__rename" :title="t('renameHint')" @click="startRename">{{ title }}</button>
        <template v-else>{{ title }}</template>
      </h1>
      <div v-if="stats" class="fa-kanban-toolbar__progress">
        <span>{{ t('progress', { done: stats.done, total: stats.total }) }}</span>
        <span class="fa-kanban-toolbar__bar" role="progressbar" :aria-valuenow="stats.progress" aria-valuemin="0" aria-valuemax="100" :aria-label="t('progress', { done: stats.done, total: stats.total })">
          <span :style="{ width: `${stats.progress}%` }" />
        </span>
        <span>{{ stats.progress }} %</span>
      </div>
    </div>
    <div class="fa-kanban-toolbar__tools">
      <FaTextField ref="search" :model-value="filter.query" class="fa-kanban-toolbar__search" type="search" :label="t('search')" :placeholder="t('searchPlaceholder')" hide-label @update:model-value="emit('filter-change', { query: $event })" />
      <select :value="filter.priority" class="fa-kanban-select" :aria-label="t('priorityFilter')" @change="emit('filter-change', { priority: ($event.target as HTMLSelectElement).value as KanbanFilterState['priority'] })">
        <option value="">{{ t('allPriorities') }}</option>
        <option v-for="priority in PRIORITIES" :key="priority" :value="priority">{{ t(`priority_${priority}`) }}</option>
      </select>
      <select :value="filter.due" class="fa-kanban-select" :aria-label="t('dueFilter')" @change="emit('filter-change', { due: ($event.target as HTMLSelectElement).value as KanbanFilterState['due'] })">
        <option value="">{{ t('allDue') }}</option>
        <option v-for="state in DUE_STATES" :key="state" :value="state">{{ t(`due_${state}`) }}</option>
      </select>
      <FaButton v-if="filterActive" size="sm" variant="ghost" icon="close" @click="emit('reset-filter')">{{ t('resetFilter') }}</FaButton>
      <FaButton v-if="showFullscreen" variant="ghost" icon="expand" icon-only :label="t('fullscreen')" @click="emit('fullscreen')" />
      <FaButton v-if="canShare" variant="ghost" icon="share" icon-only :label="t('share')" @click="emit('share')" />
      <FaButton v-if="canConfigure" variant="ghost" icon="settings" icon-only :label="t('settings')" @click="emit('settings')" />
    </div>
  </div>
</template>
