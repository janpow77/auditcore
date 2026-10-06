<script setup lang="ts">
/**
 * Description shown as text; a click turns it into a text field. Enter or
 * leaving the field saves, Escape discards. Without a text a quiet
 * placeholder („Keine Beschreibung“) stands in its place.
 */
import { nextTick, ref } from 'vue'
import { useI18n } from '../../i18n/useI18n'

const props = defineProps<{ text: string; name: string; readonly?: boolean }>()
const emit = defineEmits<{ (e: 'save', text: string): void }>()
const { t } = useI18n()
const editing = ref(false)
const draft = ref('')
const field = ref<HTMLTextAreaElement | null>(null)

async function start(): Promise<void> {
  if (props.readonly) return
  draft.value = props.text
  editing.value = true
  await nextTick()
  field.value?.focus()
}

function finish(save: boolean): void {
  if (!editing.value) return
  editing.value = false
  if (save && draft.value.trim() !== props.text.trim()) emit('save', draft.value.trim())
}

function onKey(event: KeyboardEvent): void {
  if (event.key === 'Escape') {
    finish(false)
  } else if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    finish(true)
  }
}
</script>

<template>
  <textarea
    v-if="editing"
    ref="field"
    v-model="draft"
    class="fa-input fa-describe__field"
    rows="3"
    :aria-label="t('collection.description.field', { name })"
    @keydown="onKey"
    @blur="finish(true)"
  />
  <button
    v-else
    type="button"
    class="fa-describe"
    :class="{ 'fa-describe--empty': !text }"
    :title="text || t('collection.description.edit')"
    :aria-label="`${t('collection.description.edit')}: ${name}`"
    :disabled="readonly"
    @click="start"
  >{{ text || t('collection.description.none') }}</button>
</template>
