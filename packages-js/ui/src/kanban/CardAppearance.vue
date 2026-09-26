<script setup lang="ts">
import { ref } from 'vue'
import FaButton from '../base/FaButton.vue'
import { useI18n, type Locale } from '../i18n'
import { CARD_COLORS } from './cardView'
import { kanbanDialogMessages } from './messages'

const MAX_IMAGE_BYTES = 2 * 1024 * 1024

const props = withDefaults(defineProps<{ color: string | null; image: string | null; readOnly?: boolean; locale?: Locale }>(), { readOnly: false, locale: undefined })
const emit = defineEmits<{ change: [patch: { color?: string; image?: string }] }>()
const { t } = useI18n(kanbanDialogMessages, () => props.locale)
const problem = ref('')

/** Bild als Data-URI (höchstens 2 MB, wie im Original). */
function pickImage(event: Event): void {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  problem.value = ''
  if (!file) return
  if (file.size > MAX_IMAGE_BYTES) {
    problem.value = t('imageTooLarge')
    return
  }
  const reader = new FileReader()
  reader.onload = () => emit('change', { image: String(reader.result) })
  reader.readAsDataURL(file)
}
</script>

<template>
  <div class="fa-kanban-detail__section">
    <span class="fa-kanban-detail__label">{{ t('appearance') }}</span>
    <div class="fa-kanban-detail__row" role="group" :aria-label="t('appearance')">
      <button
        v-for="swatch in CARD_COLORS"
        :key="swatch.value"
        type="button"
        class="fa-kanban-detail__swatch"
        :style="{ background: swatch.value }"
        :title="swatch.label"
        :aria-label="swatch.label"
        :aria-pressed="color === swatch.value"
        :disabled="readOnly"
        @click="emit('change', { color: color === swatch.value ? '' : swatch.value })"
      />
      <label v-if="!readOnly" class="fa-kanban-detail__swatch" :title="t('customColor')" :style="{ background: 'conic-gradient(red, yellow, lime, aqua, blue, magenta, red)' }">
        <input type="color" class="fa-sr-only" :value="color ?? '#7c3aed'" :aria-label="t('customColor')" @change="emit('change', { color: ($event.target as HTMLInputElement).value })" />
      </label>
      <FaButton v-if="color && !readOnly" size="sm" variant="ghost" icon="close" icon-only :label="t('clearColor')" @click="emit('change', { color: '' })" />
    </div>
    <img v-if="image" class="fa-kanban-detail__image" :src="image" :alt="t('image')" />
    <div v-if="!readOnly" class="fa-kanban-detail__row">
      <label class="fa-button fa-button--secondary fa-button--sm">
        {{ t('uploadImage') }}
        <input type="file" accept="image/*" class="fa-sr-only" @change="pickImage" />
      </label>
      <FaButton v-if="image" size="sm" variant="ghost" icon="trash" @click="emit('change', { image: '' })">{{ t('removeImage') }}</FaButton>
    </div>
    <p v-if="problem" class="fa-field__note" role="alert">{{ problem }}</p>
  </div>
</template>
