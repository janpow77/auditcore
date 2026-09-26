<script setup lang="ts">
import { useId } from '../../composables/useId'
import type { TabItem } from '../core'

const props = defineProps<{ tabs: TabItem[]; active: string; label: string }>()
const emit = defineEmits<{ 'tab-change': [key: string] }>()
const base = useId('fa-dsfa-tab')

/** Pfeiltasten, Pos1 und Ende wechseln den Abschnitt (WAI-ARIA Tabs). */
function onKey(event: KeyboardEvent): void {
  const index = props.tabs.findIndex((tab) => tab.key === props.active)
  const moves: Record<string, number> = { ArrowRight: index + 1, ArrowLeft: index - 1, Home: 0, End: props.tabs.length - 1 }
  const target = moves[event.key]
  if (target === undefined) return
  event.preventDefault()
  const next = props.tabs[(target + props.tabs.length) % props.tabs.length]
  if (!next) return
  emit('tab-change', next.key)
  const list = (event.currentTarget as HTMLElement | null)
  list?.querySelector<HTMLElement>(`#${base}-${next.key}`)?.focus()
}
</script>

<template>
  <div class="fa-dsfa__tabs" role="tablist" :aria-label="label" @keydown="onKey">
    <button
      v-for="tab in tabs"
      :id="`${base}-${tab.key}`"
      :key="tab.key"
      type="button"
      role="tab"
      class="fa-dsfa__tab"
      :aria-selected="tab.key === active ? 'true' : 'false'"
      :aria-controls="`${base}-panel`"
      :tabindex="tab.key === active ? 0 : -1"
      @click="emit('tab-change', tab.key)"
    >
      {{ tab.label }}
    </button>
  </div>
  <div :id="`${base}-panel`" role="tabpanel" :aria-labelledby="`${base}-${active}`" tabindex="0">
    <slot />
  </div>
</template>
