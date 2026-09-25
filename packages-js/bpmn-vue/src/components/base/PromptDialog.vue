<script setup lang="ts">
/** Small dialog asking for one name (replaces `window.prompt`). */
import { ref, watch } from 'vue'
import BaseDialog from './BaseDialog.vue'
import { useI18n } from '../../i18n/useI18n'

const props = defineProps<{ open: boolean; title: string; label: string; value?: string }>()
const emit = defineEmits<{ (e: 'update:open', value: boolean): void; (e: 'confirm', value: string): void }>()
const { t } = useI18n()
const text = ref(props.value ?? '')

watch(
  () => props.open,
  (open) => {
    if (open) text.value = props.value ?? ''
  },
)

function confirm(): void {
  if (!text.value.trim()) return
  emit('confirm', text.value.trim())
  emit('update:open', false)
}
</script>

<template>
  <BaseDialog :open="open" :title="title" width="420px" @update:open="emit('update:open', $event)">
    <label class="fa-field">
      <span class="fa-label">{{ label }}</span>
      <input v-model="text" class="fa-input" @keydown.enter.prevent="confirm" />
    </label>
    <template #footer>
      <button type="button" class="fa-btn" @click="emit('update:open', false)">{{ t('common.cancel') }}</button>
      <button type="button" class="fa-btn fa-btn--primary" :disabled="!text.trim()" @click="confirm">{{ t('common.apply') }}</button>
    </template>
  </BaseDialog>
</template>
