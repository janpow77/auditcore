<script setup lang="ts">
import { ref, watch } from 'vue'
import { PRIORITIES, type Attachment, type Card, type CardLink, type Column, type Priority } from '@flowaudit/kanban-core'
import FaButton from '../base/FaButton.vue'
import FaDialog from '../base/FaDialog.vue'
import FaTextField from '../base/FaTextField.vue'
import { formatDate, useI18n, type Locale } from '../i18n'
import CardAppearance from './CardAppearance.vue'
import CardChecklistEditor from './CardChecklistEditor.vue'
import CardReferences from './CardReferences.vue'
import CardTagsEditor from './CardTagsEditor.vue'
import { kanbanDialogMessages, kanbanMessages } from './messages'

const props = withDefaults(defineProps<{
  card: Card | null
  columns: readonly Column[]
  readOnly?: boolean
  canDelete?: boolean
  locale?: Locale
}>(), { readOnly: false, canDelete: false, locale: undefined })

const emit = defineEmits<{
  close: []
  update: [fields: Record<string, unknown>]
  delete: [card: Card]
  navigate: [link: CardLink]
  attachment: [attachment: Attachment]
}>()

const { t, locale: active } = useI18n(kanbanDialogMessages, () => props.locale)
const { t: tk } = useI18n(kanbanMessages, () => props.locale)
const title = ref('')
const description = ref('')
const confirming = ref(false)

watch(() => props.card, (card) => {
  title.value = card?.title ?? ''
  description.value = card?.description ?? ''
  if (!card) confirming.value = false
}, { immediate: true })

function update(fields: Record<string, unknown>): void {
  if (!props.readOnly) emit('update', fields)
}

function commitTitle(): void {
  const value = title.value.trim()
  if (props.card && value && value !== props.card.title) update({ title: value })
}

function commitDescription(): void {
  if (props.card && description.value !== props.card.description) update({ description: description.value })
}

function remove(): void {
  if (!props.card) return
  if (!confirming.value) {
    confirming.value = true
    return
  }
  emit('delete', props.card)
}
</script>

<template>
  <FaDialog :open="card !== null" :title="card?.title || t('detailTitle')" placement="side" :locale="locale" @close="emit('close')">
    <div v-if="card" class="fa-kanban-detail">
      <div class="fa-kanban-detail__row">
        <FaTextField
          :model-value="card.badge ?? ''"
          :label="t('badge')"
          :placeholder="t('badgePlaceholder')"
          :disabled="readOnly"
          style="width: 7rem"
          @change="update({ badge: ($event.target as HTMLInputElement).value.trim().toUpperCase() })"
        />
        <FaTextField v-model="title" :label="t('title')" :disabled="readOnly" style="flex: 1" @focusout="commitTitle" @keydown.enter="commitTitle" />
      </div>
      <div class="fa-kanban-detail__row">
        <label class="fa-field">
          <span class="fa-field__label">{{ t('column') }}</span>
          <select class="fa-kanban-select" :value="card.column_id" :disabled="readOnly" @change="update({ column_id: ($event.target as HTMLSelectElement).value })">
            <option v-for="column in columns" :key="column.id" :value="column.id">{{ column.label }}</option>
          </select>
        </label>
        <label class="fa-field">
          <span class="fa-field__label">{{ t('due') }}</span>
          <input class="fa-field__input" type="date" :value="card.due?.slice(0, 10) ?? ''" :disabled="readOnly" @change="update({ due: ($event.target as HTMLInputElement).value })" />
        </label>
        <FaButton v-if="card.due && !readOnly" size="sm" variant="ghost" icon="close" icon-only :label="t('clearDue')" @click="update({ due: '' })" />
      </div>
      <div class="fa-kanban-detail__section">
        <span id="fa-kanban-priority" class="fa-kanban-detail__label">{{ t('priority') }}</span>
        <div class="fa-kanban-detail__row" role="radiogroup" aria-labelledby="fa-kanban-priority">
          <FaButton
            v-for="priority in PRIORITIES"
            :key="priority"
            size="sm"
            :variant="card.priority === priority ? 'primary' : 'secondary'"
            role="radio"
            :aria-checked="card.priority === priority"
            :disabled="readOnly"
            @click="update({ priority: priority as Priority })"
          >
            {{ tk(`priority_${priority}`) }}
          </FaButton>
        </div>
      </div>
      <label class="fa-kanban-detail__section">
        <span class="fa-kanban-detail__label">{{ t('description') }}</span>
        <textarea v-model="description" class="fa-kanban-detail__textarea" :placeholder="t('descriptionPlaceholder')" :readonly="readOnly" @blur="commitDescription" />
      </label>
      <CardTagsEditor :tags="card.tags" :read-only="readOnly" :locale="locale" @change="update({ tags: $event })" />
      <CardChecklistEditor :items="card.checklist" :read-only="readOnly" :locale="locale" @change="update({ checklist: $event })" />
      <CardAppearance :color="card.color" :image="card.image" :read-only="readOnly" :locale="locale" @change="update($event)" />
      <CardReferences :links="card.links" :attachments="card.attachments" :locale="locale" @navigate="emit('navigate', $event)" @attachment="emit('attachment', $event)" />
      <slot name="extra" :card="card" />
      <div class="fa-kanban-detail__meta">
        <p>{{ t('created', { date: formatDate(card.created_at, active, true) }) }}</p>
        <p>{{ t('updated', { date: formatDate(card.updated_at, active, true) }) }}</p>
      </div>
    </div>
    <template v-if="card && canDelete && !readOnly" #footer>
      <FaButton :variant="confirming ? 'danger' : 'secondary'" icon="trash" @click="remove">{{ confirming ? t('confirmDelete') : t('deleteCard') }}</FaButton>
    </template>
  </FaDialog>
</template>
