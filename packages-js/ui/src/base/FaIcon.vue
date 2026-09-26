<script setup lang="ts">
import { computed } from 'vue'
import { ICONS, type IconName } from '@auditcore/ui-core'

const props = withDefaults(defineProps<{
  name: IconName
  size?: number | string
  /** Mit Beschriftung ist das Symbol bedeutungstragend (role="img"), sonst dekorativ. */
  label?: string
}>(), { size: 18, label: '' })

const paths = computed(() => ICONS[props.name])
const dimension = computed(() => (typeof props.size === 'number' ? `${props.size}px` : props.size))
</script>

<template>
  <svg
    class="fa-icon"
    viewBox="0 0 24 24"
    :width="dimension"
    :height="dimension"
    fill="none"
    stroke="currentColor"
    stroke-linecap="round"
    stroke-linejoin="round"
    :role="label ? 'img' : undefined"
    :aria-label="label || undefined"
    :aria-hidden="label ? undefined : 'true'"
    focusable="false"
  >
    <path v-for="(d, index) in paths" :key="index" :d="d" />
  </svg>
</template>
