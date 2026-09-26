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
