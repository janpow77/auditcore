<script setup lang="ts">
import type { ExportFormat } from './types'

withDefaults(defineProps<{ saving?: boolean; disabled?: boolean; saveLabel?: string }>(), {
  saving: false, disabled: false, saveLabel: 'Speichern',
})
const emit = defineEmits<{ save: []; export: [format: ExportFormat] }>()
</script>

<template>
  <div class="fa-export-actions" role="group" aria-label="Speichern und exportieren">
    <button class="fa-export-button" type="button" :disabled="disabled || saving" :aria-busy="saving || undefined" @click="emit('save')">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 3h12l3 3v15H4V3zM8 3v6h8V3M8 21v-8h8v8" /></svg><span>{{ saving ? 'Speichert …' : saveLabel }}</span>
    </button>
    <button class="fa-export-button" type="button" aria-label="Als PDF exportieren" :disabled="disabled" @click="emit('export', 'pdf')">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 2h9l4 4v16H6zM14 2v5h5M8.5 16h2a1.5 1.5 0 0 0 0-3h-2v5m5-5v5h1a2.5 2.5 0 0 0 0-5h-1m5 0h-2v5m0-2h2" /></svg><span>PDF</span>
    </button>
    <button class="fa-export-button" type="button" aria-label="Als JPG exportieren" :disabled="disabled" @click="emit('export', 'jpg')">
      <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2" /><circle cx="9" cy="10" r="1.5" /><path d="m4 18 5-5 3 3 3-4 5 6" /></svg><span>JPG</span>
    </button>
    <slot />
  </div>
</template>
