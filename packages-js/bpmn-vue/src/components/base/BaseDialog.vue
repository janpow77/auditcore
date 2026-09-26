<script setup lang="ts">
/**
 * Accessible modal dialog: `role="dialog"`, labelled by its title, closes on
 * Escape and backdrop click, keeps focus inside and returns it afterwards.
 */
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { createFocusTrap } from '@auditcore/ui-core'
import FaIcon from './FaIcon.vue'
import { useI18n } from '../../i18n/useI18n'

const props = withDefaults(defineProps<{ open: boolean; title: string; width?: string; subtitle?: string }>(), { width: '640px', subtitle: '' })
const emit = defineEmits<{ (e: 'update:open', value: boolean): void; (e: 'close'): void }>()
const { t } = useI18n()

const panel = ref<HTMLElement | null>(null)
const titleId = `fa-dialog-${Math.random().toString(36).slice(2, 9)}`
const trap = createFocusTrap(() => panel.value)

function close(): void {
  emit('update:open', false)
  emit('close')
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key !== 'Escape') return
  event.stopPropagation()
  close()
}

watch(
  () => props.open,
  async (open) => {
    if (!open) return trap.deactivate()
    await nextTick()
    trap.activate()
  },
  { immediate: true },
)

onBeforeUnmount(trap.deactivate)
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
      @keydown="onKeydown"
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
