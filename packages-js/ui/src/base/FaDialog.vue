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

<style>
.fa-dialog {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--fa-space-4);
  background: var(--fa-color-overlay);
  font-family: var(--fa-font-sans);
}
.fa-dialog--side { justify-content: flex-end; align-items: stretch; padding: 0; }
.fa-dialog__panel {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-height: calc(100vh - 2 * var(--fa-space-4));
  background: var(--fa-color-surface);
  color: var(--fa-color-text);
  border-radius: var(--fa-radius-lg);
  box-shadow: var(--fa-shadow-lg);
  outline: none;
}
.fa-dialog__panel--sm { max-width: 24rem; }
.fa-dialog__panel--md { max-width: 34rem; }
.fa-dialog__panel--lg { max-width: 52rem; }
.fa-dialog--side .fa-dialog__panel { max-height: none; height: 100%; border-radius: 0; max-width: 30rem; }
.fa-dialog__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--fa-space-3);
  padding: var(--fa-space-4) var(--fa-space-4) var(--fa-space-3) var(--fa-space-5);
  border-bottom: 1px solid var(--fa-color-border);
}
.fa-dialog__title { margin: 0; font-size: var(--fa-font-size-lg); font-weight: 600; }
.fa-dialog__description { margin: var(--fa-space-1) 0 0; font-size: var(--fa-font-size-sm); color: var(--fa-color-text-muted); }
.fa-dialog__body { flex: 1; overflow-y: auto; padding: var(--fa-space-4) var(--fa-space-5); }
.fa-dialog__footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--fa-space-2);
  padding: var(--fa-space-3) var(--fa-space-5);
  border-top: 1px solid var(--fa-color-border);
}
</style>
