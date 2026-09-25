<script setup lang="ts">
import { ref } from 'vue'
import FaIcon from '../base/FaIcon.vue'
import { useI18n, type Locale } from '../i18n'
import { kanbanDialogMessages } from './messages'

const props = withDefaults(defineProps<{ tags: readonly string[]; readOnly?: boolean; locale?: Locale }>(), { readOnly: false, locale: undefined })
const emit = defineEmits<{ change: [tags: string[]] }>()
const { t } = useI18n(kanbanDialogMessages, () => props.locale)
const draft = ref('')

function add(): void {
  const tag = draft.value.trim()
  draft.value = ''
  if (tag && !props.tags.includes(tag)) emit('change', [...props.tags, tag])
}
</script>

<template>
  <div class="fa-kanban-detail__section">
    <span class="fa-kanban-detail__label">{{ t('tags') }}</span>
    <div class="fa-kanban-detail__row">
      <span v-for="tag in tags" :key="tag" class="fa-badge fa-badge--accent">
        {{ tag }}
        <button v-if="!readOnly" type="button" class="fa-kanban-detail__chip-remove" :aria-label="t('removeTag', { tag })" @click="emit('change', tags.filter((entry) => entry !== tag))">
          <FaIcon name="close" :size="11" />
        </button>
      </span>
    </div>
    <input v-if="!readOnly" v-model="draft" class="fa-field__input" :placeholder="t('tagPlaceholder')" :aria-label="t('tagPlaceholder')" @keydown.enter.prevent="add" />
  </div>
</template>
