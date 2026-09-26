<script setup lang="ts">
import type { BadgeTone } from '@auditcore/ui-core'

withDefaults(defineProps<{ tone?: BadgeTone; label?: string }>(), { tone: 'neutral', label: '' })
</script>

<template>
  <span class="fa-badge" :class="`fa-badge--${tone}`"><slot>{{ label }}</slot></span>
</template>
