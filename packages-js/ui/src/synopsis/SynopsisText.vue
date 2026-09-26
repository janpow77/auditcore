<script setup lang="ts">
import type { DiffSegment } from '@flowaudit/ui-core'

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
