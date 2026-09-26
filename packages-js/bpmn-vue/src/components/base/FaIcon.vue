<script setup lang="ts">
/**
 * Icon from the FlowAudit icon set (24 px grid, `currentColor`). Decorative
 * by default; pass `label` to make it meaningful for assistive technology.
 */
import { computed, h } from 'vue'
import { iconPrimitives } from '@auditcore/bpmn-flowaudit'

const props = withDefaults(defineProps<{ name: string; size?: number; label?: string }>(), { size: 18, label: '' })

const children = computed(() => iconPrimitives(props.name).map(([tag, attrs]) => h(tag, attrs)))

function Render() {
  return h(
    'svg',
    {
      class: 'fa-icon',
      width: props.size,
      height: props.size,
      viewBox: '0 0 24 24',
      fill: 'none',
      stroke: 'currentColor',
      'stroke-width': 1.75,
      'stroke-linecap': 'round',
      'stroke-linejoin': 'round',
      role: props.label ? 'img' : undefined,
      'aria-label': props.label || undefined,
      'aria-hidden': props.label ? undefined : 'true',
      focusable: 'false',
    },
    children.value,
  )
}
</script>

<template>
  <Render />
</template>
