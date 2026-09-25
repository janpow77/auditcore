<script setup lang="ts">
/**
 * Small popover at a point of the canvas (colour choice and role choice
 * from the context pad). Stays inside the canvas and closes on Escape.
 */
import { computed } from 'vue'

const props = defineProps<{ x: number; y: number; width: number; height: number; title: string }>()
const emit = defineEmits<{ (e: 'close'): void }>()

const style = computed(() => ({
  left: `${Math.max(4, Math.min(props.x + 8, props.width - 260))}px`,
  top: `${Math.max(4, Math.min(props.y + 8, props.height - 320))}px`,
}))
</script>

<template>
  <div class="fa-menu fa-canvas-popover" role="dialog" :aria-label="title" :style="style" @keydown.esc="emit('close')" @mousedown.stop>
    <p class="fa-label">{{ title }}</p>
    <slot />
  </div>
</template>

<style>
.fa-canvas-popover {
  width: 250px;
  max-height: 320px;
  overflow: auto;
}
</style>
