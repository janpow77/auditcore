<script setup lang="ts">
/**
 * Handle between a side panel and the main area: drag (pointer), arrows or
 * Home/End to resize, double click for the standard width, the small button
 * collapses the panel. A collapsed panel leaves a narrow rail to show it again.
 */
import { ref } from 'vue'
import { dragWidth, keyWidth, type PanelBounds, type PanelEdge } from '@auditcore/bpmn-flowaudit/ui'
import FaIcon from './FaIcon.vue'
import { useI18n } from '../../i18n/useI18n'

const props = defineProps<{ width: number; open: boolean; bounds: PanelBounds; edge: PanelEdge; name: string }>()
const emit = defineEmits<{ (e: 'update:width', width: number): void; (e: 'update:open', open: boolean): void }>()
const { t } = useI18n()
const drag = ref<{ x: number; width: number } | null>(null)

function start(event: PointerEvent): void {
  if (event.button !== 0) return
  drag.value = { x: event.clientX, width: props.width }
  ;(event.currentTarget as HTMLElement).setPointerCapture?.(event.pointerId)
  event.preventDefault()
}

function move(event: PointerEvent): void {
  if (drag.value) emit('update:width', dragWidth(drag.value.width, drag.value.x, event.clientX, props.edge, props.bounds))
}

function stop(event: PointerEvent): void {
  drag.value = null
  ;(event.currentTarget as HTMLElement).releasePointerCapture?.(event.pointerId)
}

function onKey(event: KeyboardEvent): void {
  const width = keyWidth(props.width, event.key, props.edge, props.bounds)
  if (width === null) return
  event.preventDefault()
  emit('update:width', width)
}
</script>

<template>
  <div
    v-if="open"
    class="fa-resizer"
    :class="[`fa-resizer--${edge}`, { 'fa-resizer--active': drag }]"
    role="separator"
    aria-orientation="vertical"
    tabindex="0"
    :aria-label="t('panel.resize', { name })"
    :aria-valuemin="bounds.min"
    :aria-valuemax="bounds.max"
    :aria-valuenow="width"
    @pointerdown="start"
    @pointermove="move"
    @pointerup="stop"
    @pointercancel="stop"
    @keydown="onKey"
    @dblclick="emit('update:width', bounds.initial)"
  >
    <button
      type="button"
      class="fa-resizer__toggle"
      :title="t('panel.collapse', { name })"
      :aria-label="t('panel.collapse', { name })"
      @pointerdown.stop
      @dblclick.stop
      @click="emit('update:open', false)"
    >
      <FaIcon :name="edge === 'right' ? 'chevron-right' : 'chevron-left'" :size="12" />
    </button>
  </div>
  <div v-else class="fa-panel-rail" :class="`fa-panel-rail--${edge}`">
    <button type="button" class="fa-panel-rail__button" :title="t('panel.expand', { name })" :aria-label="t('panel.expand', { name })" @click="emit('update:open', true)">
      <FaIcon :name="edge === 'right' ? 'panel-right' : 'panel-left'" :size="16" />
      <span class="fa-panel-rail__label">{{ name }}</span>
    </button>
  </div>
</template>
