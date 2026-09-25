<script setup lang="ts">
/**
 * Button with a popover menu: opens on click, closes on Escape, on click
 * outside and after choosing an item (`close` slot prop).
 */
import { onBeforeUnmount, onMounted, ref } from 'vue'
import FaIcon from './FaIcon.vue'

defineProps<{ label: string; icon: string; showLabel?: boolean; align?: 'left' | 'right' }>()
const open = ref(false)
const root = ref<HTMLElement | null>(null)

function close(): void {
  open.value = false
}

function onDocument(event: MouseEvent): void {
  if (open.value && root.value && !root.value.contains(event.target as Node)) close()
}

function onKey(event: KeyboardEvent): void {
  if (event.key === 'Escape' && open.value) {
    close()
    root.value?.querySelector<HTMLElement>('button')?.focus()
  }
}

onMounted(() => document.addEventListener('mousedown', onDocument))
onBeforeUnmount(() => document.removeEventListener('mousedown', onDocument))
</script>

<template>
  <div ref="root" class="fa-toolbar-menu" @keydown="onKey">
    <button
      type="button"
      :class="showLabel ? 'fa-btn fa-btn--ghost' : 'fa-icon-btn'"
      :aria-label="label"
      :title="label"
      aria-haspopup="menu"
      :aria-expanded="open"
      @click="open = !open"
    >
      <FaIcon :name="icon" />
      <span v-if="showLabel">{{ label }}</span>
      <FaIcon v-if="showLabel" name="chevron-down" :size="14" />
    </button>
    <div v-if="open" class="fa-menu" :class="{ 'fa-menu--right': align === 'right' }" role="menu">
      <slot :close="close" />
    </div>
  </div>
</template>

<style>
.fa-toolbar-menu {
  position: relative;
}

.fa-toolbar-menu > .fa-menu {
  top: calc(100% + 4px);
  left: 0;
}

.fa-toolbar-menu > .fa-menu--right {
  left: auto;
  right: 0;
}
</style>
