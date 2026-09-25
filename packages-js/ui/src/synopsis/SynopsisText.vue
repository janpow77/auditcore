<script setup lang="ts">
import type { DiffSegment } from './wordDiff'

/**
 * Wortsegmente mit `<del>`/`<ins>`. Streichungen sind durchgestrichen,
 * Einfügungen unterstrichen (nicht nur Farbe); Bildschirmleser hören
 * „gestrichen: … Ende“ bzw. „eingefügt: … Ende“.
 */
withDefaults(
  defineProps<{
    segments?: readonly DiffSegment[]
    empty?: string
    srRemoved?: string
    srAdded?: string
    srEnd?: string
  }>(),
  { segments: () => [], empty: '', srRemoved: '', srAdded: '', srEnd: '' },
)
</script>

<template>
  <p class="fa-synopsis__text">
    <span v-if="segments.length === 0" class="fa-synopsis__empty">{{ empty }}</span>
    <template v-for="(segment, index) in segments" :key="index">
      <del v-if="segment.kind === 'removed'" class="fa-synopsis__del"><span class="fa-sr-only">{{ srRemoved }} </span>{{ segment.text }}<span class="fa-sr-only"> {{ srEnd }}</span></del>
      <ins v-else-if="segment.kind === 'added'" class="fa-synopsis__ins"><span class="fa-sr-only">{{ srAdded }} </span>{{ segment.text }}<span class="fa-sr-only"> {{ srEnd }}</span></ins>
      <template v-else>{{ segment.text }}</template>
    </template>
  </p>
</template>

<style>
.fa-synopsis__text { margin: 0; white-space: pre-wrap; overflow-wrap: anywhere; line-height: 1.7; }
.fa-synopsis__empty { color: var(--fa-color-text-muted); font-style: italic; }
.fa-synopsis__del { background: var(--fa-color-danger-soft); color: var(--fa-color-danger); text-decoration: line-through; text-decoration-thickness: 1.5px; border-radius: 2px; }
.fa-synopsis__ins { background: var(--fa-color-success-soft); color: var(--fa-color-success); text-decoration: underline; text-decoration-thickness: 1.5px; text-underline-offset: 2px; border-radius: 2px; }
</style>
