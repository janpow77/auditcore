<script setup lang="ts">
import { computed, ref } from 'vue'
import type { ChecklistItem } from '@flowaudit/kanban-core'
import FaButton from '../base/FaButton.vue'
import { useI18n, type Locale } from '../i18n'
import { kanbanDialogMessages } from './messages'

const props = withDefaults(defineProps<{ items: readonly ChecklistItem[]; readOnly?: boolean; locale?: Locale }>(), { readOnly: false, locale: undefined })
const emit = defineEmits<{ change: [items: ChecklistItem[]] }>()
const { t } = useI18n(kanbanDialogMessages, () => props.locale)
const draft = ref('')
const done = computed(() => props.items.filter((item) => item.done).length)

function replace(index: number, patch: Partial<ChecklistItem>): void {
  emit('change', props.items.map((item, position) => (position === index ? { ...item, ...patch } : item)))
}

function rename(index: number, event: Event): void {
  const text = (event.target as HTMLInputElement).value.trim()
  if (text && text !== props.items[index]?.text) replace(index, { text })
}

function add(): void {
  const text = draft.value.trim()
  draft.value = ''
  if (text) emit('change', [...props.items, { text, done: false }])
}
</script>

<template>
  <div class="fa-kanban-detail__section">
    <span class="fa-kanban-detail__label">
      {{ t('checklist') }}
      <template v-if="items.length">· {{ t('checklistSummary', { done, total: items.length }) }}</template>
    </span>
    <ul v-if="items.length" class="fa-kanban-detail__list">
      <li v-for="(item, index) in items" :key="index" class="fa-kanban-detail__item" :class="{ 'is-done': item.done }">
        <input type="checkbox" :checked="item.done" :disabled="readOnly" :aria-label="item.text" @change="replace(index, { done: !item.done })" />
        <input type="text" :value="item.text" :readonly="readOnly" :aria-label="t('checklist')" @change="rename(index, $event)" />
        <FaButton v-if="!readOnly" size="sm" variant="ghost" icon="close" icon-only :label="t('removeItem', { text: item.text })" @click="emit('change', items.filter((_, position) => position !== index))" />
      </li>
    </ul>
    <input v-if="!readOnly" v-model="draft" class="fa-field__input" :placeholder="t('checklistPlaceholder')" :aria-label="t('checklistPlaceholder')" @keydown.enter.prevent="add" />
  </div>
</template>
