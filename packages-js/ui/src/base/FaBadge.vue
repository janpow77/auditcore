<script setup lang="ts">
import type { BadgeTone } from './types'

withDefaults(defineProps<{ tone?: BadgeTone; label?: string }>(), { tone: 'neutral', label: '' })
</script>

<template>
  <span class="fa-badge" :class="`fa-badge--${tone}`"><slot>{{ label }}</slot></span>
</template>

<style>
.fa-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--fa-space-1);
  padding: 0.125rem var(--fa-space-2);
  border-radius: 999px;
  font: 600 var(--fa-font-size-xs) / 1.3 var(--fa-font-sans);
  background: var(--fa-color-surface-sunken);
  color: var(--fa-color-text-muted);
}
.fa-badge--accent { background: var(--fa-color-accent-soft); color: var(--fa-color-accent); }
.fa-badge--success { background: var(--fa-color-success-soft); color: var(--fa-color-success); }
.fa-badge--warning { background: var(--fa-color-warning-soft); color: var(--fa-color-warning); }
.fa-badge--danger { background: var(--fa-color-danger-soft); color: var(--fa-color-danger); }
</style>
