<script setup lang="ts">
/**
 * Accessible modal dialog: `role="dialog"`, labelled by its title, closes on
 * Escape and backdrop click, keeps focus inside and returns it afterwards.
 */
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import FaIcon from './FaIcon.vue'
import { useI18n } from '../../i18n/useI18n'

const props = withDefaults(defineProps<{ open: boolean; title: string; width?: string; subtitle?: string }>(), { width: '640px', subtitle: '' })
const emit = defineEmits<{ (e: 'update:open', value: boolean): void; (e: 'close'): void }>()
const { t } = useI18n()

const panel = ref<HTMLElement | null>(null)
const titleId = `fa-dialog-${Math.random().toString(36).slice(2, 9)}`
let previousFocus: HTMLElement | null = null

const FOCUSABLE = 'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'

function close(): void {
  emit('update:open', false)
  emit('close')
}

function trapFocus(event: KeyboardEvent): void {
  if (event.key === 'Escape') {
    event.stopPropagation()
    close()
    return
  }
  if (event.key !== 'Tab' || !panel.value) return
  const items = Array.from(panel.value.querySelectorAll<HTMLElement>(FOCUSABLE))
  const first = items[0]
  const last = items[items.length - 1]
  if (!first || !last) return
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

watch(
  () => props.open,
  async (open) => {
    if (open) {
      previousFocus = document.activeElement as HTMLElement | null
      await nextTick()
      panel.value?.querySelector<HTMLElement>(FOCUSABLE)?.focus()
    } else {
      previousFocus?.focus?.()
    }
  },
  { immediate: true },
)

onBeforeUnmount(() => previousFocus?.focus?.())
</script>

<template>
  <div v-if="open" class="fa-dialog-backdrop" @mousedown.self="close">
    <section
      ref="panel"
      class="fa-dialog"
      role="dialog"
      aria-modal="true"
      :aria-labelledby="titleId"
      :style="{ width }"
      @keydown="trapFocus"
    >
      <header class="fa-dialog__head">
        <div>
          <h2 :id="titleId" class="fa-dialog__title">{{ title }}</h2>
          <p v-if="subtitle" class="fa-dialog__subtitle">{{ subtitle }}</p>
        </div>
        <button type="button" class="fa-icon-btn" :aria-label="t('common.close')" @click="close">
          <FaIcon name="close" />
        </button>
      </header>
      <div class="fa-dialog__body"><slot /></div>
      <footer v-if="$slots.footer" class="fa-dialog__foot"><slot name="footer" /></footer>
    </section>
  </div>
</template>

<style>
.fa-dialog-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: rgba(10, 14, 22, 0.5);
  backdrop-filter: blur(2px);
}

.fa-dialog {
  display: flex;
  flex-direction: column;
  max-width: 100%;
  max-height: calc(100vh - 32px);
  border: 1px solid var(--fa-border);
  border-radius: 12px;
  background: var(--fa-surface);
  color: var(--fa-text);
  box-shadow: var(--fa-shadow);
}

.fa-dialog__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 18px 10px;
  border-bottom: 1px solid var(--fa-border);
}

.fa-dialog__title {
  margin: 0;
  font-size: 17px;
  font-weight: 650;
}

.fa-dialog__subtitle {
  margin: 2px 0 0;
  font-size: 13px;
  color: var(--fa-text-muted);
}

.fa-dialog__body {
  padding: 14px 18px;
  overflow: auto;
}

.fa-dialog__foot {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 18px;
  border-top: 1px solid var(--fa-border);
}
</style>
