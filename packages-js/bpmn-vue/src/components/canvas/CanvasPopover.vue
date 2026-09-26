<script setup lang="ts">
/**
 * Small popover at a point of the canvas (colour choice and role choice
 * from the context pad). Stays inside the canvas and closes on Escape.
 */
import { computed } from 'vue'
import { popoverPosition } from '@flowaudit/bpmn-flowaudit/ui'

const props = defineProps<{ x: number; y: number; width: number; height: number; title: string }>()
const emit = defineEmits<{ (e: 'close'): void }>()

const style = computed(() => popoverPosition(props.x, props.y, props.width, props.height))
</script>

<template>
  <div class="fa-menu fa-canvas-popover" role="dialog" :aria-label="title" :style="style" @keydown.esc="emit('close')" @mousedown.stop>
    <p class="fa-label">{{ title }}</p>
    <slot />
  </div>
</template>
