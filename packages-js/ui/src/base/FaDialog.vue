<script setup lang="ts">
import { ref, toRef } from 'vue'
import { useFocusTrap } from '../composables/useFocusTrap'
import { useId } from '../composables/useId'
import { baseMessages, useI18n, type Locale } from '../i18n'
import FaButton from './FaButton.vue'

const props = withDefaults(defineProps<{
  open: boolean
  title: string
  description?: string
  size?: 'sm' | 'md' | 'lg'
  /** Seitliches Panel statt zentriertem Dialog. */
  placement?: 'center' | 'side'
  closeOnBackdrop?: boolean
  locale?: Locale
}>(), { description: '', size: 'md', placement: 'center', closeOnBackdrop: true, locale: undefined })

const emit = defineEmits<{ 'update:open': [open: boolean]; close: [] }>()

const panel = ref<HTMLElement | null>(null)
const titleId = useId('fa-dialog-title')
const descriptionId = useId('fa-dialog-description')
const { t } = useI18n(baseMessages, () => props.locale)
useFocusTrap(panel, toRef(props, 'open'))

function close(): void {
  emit('update:open', false)
  emit('close')
}

function onBackdrop(event: MouseEvent): void {
  if (props.closeOnBackdrop && event.target === event.currentTarget) close()
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="fa-dialog" :class="`fa-dialog--${placement}`" @mousedown="onBackdrop">
      <section
        ref="panel"
        class="fa-dialog__panel"
        :class="`fa-dialog__panel--${size}`"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="titleId"
        :aria-describedby="description ? descriptionId : undefined"
        tabindex="-1"
        @keydown.esc.stop.prevent="close"
      >
        <header class="fa-dialog__header">
          <div>
            <h2 :id="titleId" class="fa-dialog__title">{{ title }}</h2>
            <p v-if="description" :id="descriptionId" class="fa-dialog__description">{{ description }}</p>
          </div>
          <FaButton variant="ghost" icon="close" icon-only :label="t('close')" @click="close" />
        </header>
        <div class="fa-dialog__body"><slot /></div>
        <footer v-if="$slots.footer" class="fa-dialog__footer"><slot name="footer" /></footer>
      </section>
    </div>
  </Teleport>
</template>
