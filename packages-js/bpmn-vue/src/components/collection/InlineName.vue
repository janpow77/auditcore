<script setup lang="ts">
/**
 * Name shown as text; a click turns it into a one-line field. Enter or
 * leaving the field saves, Escape discards. Blanks are trimmed; an empty
 * name is not saved, the old one stays.
 */
import { nextTick, ref } from 'vue'
import { useI18n } from '../../i18n/useI18n'

const props = defineProps<{ text: string; readonly?: boolean }>()
const emit = defineEmits<{ (e: 'save', text: string): void }>()
const { t } = useI18n()
const editing = ref(false)
const draft = ref('')
const field = ref<HTMLInputElement | null>(null)

async function start(): Promise<void> {
  if (props.readonly) return
  draft.value = props.text
  editing.value = true
  await nextTick()
  field.value?.select()
}

function finish(save: boolean): void {
  if (!editing.value) return
  editing.value = false
  const text = draft.value.trim()
  if (save && text && text !== props.text) emit('save', text)
}

function onKey(event: KeyboardEvent): void {
  if (event.key === 'Escape') {
    finish(false)
  } else if (event.key === 'Enter') {
    event.preventDefault()
    finish(true)
  }
}
</script>

<template>
  <input
    v-if="editing"
    ref="field"
    v-model="draft"
    class="fa-input fa-inline-name__field"
    :aria-label="t('collection.name.field', { name: text })"
    @keydown="onKey"
    @blur="finish(true)"
  />
  <button
    v-else
    type="button"
    class="fa-inline-name"
    :title="t('collection.name.edit')"
    :aria-label="`${t('collection.name.edit')}: ${text}`"
    :disabled="readonly"
    @click="start"
  >{{ text }}</button>
</template>
