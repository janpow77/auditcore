<script setup lang="ts">
/**
 * Toggle chips for the domain markers of the selected element. Turning on a
 * colouring marker (e.g. finding) also sets its colour if none is set.
 */
import { MARKER_COLORS, MARKERS, label, type Marker } from '@flowaudit/bpmn-flowaudit'
import FaIcon from '../../components/base/FaIcon.vue'
import { useI18n } from '../../i18n/useI18n'

const props = defineProps<{ markers: Marker[]; disabled?: boolean }>()
const emit = defineEmits<{ (e: 'update', markers: Marker[]): void; (e: 'color', color: { fill: string; stroke: string }): void }>()
const { t, locale } = useI18n()

const has = (type: string) => props.markers.some((marker) => marker.type === type)

function toggle(type: string): void {
  if (has(type)) {
    emit('update', props.markers.filter((marker) => marker.type !== type))
    return
  }
  emit('update', [...props.markers, { type }])
  if (MARKER_COLORS[type]) emit('color', MARKER_COLORS[type])
}

function setText(type: string, text: string): void {
  emit('update', props.markers.map((marker) => (marker.type === type ? { ...marker, text: text.trim() || undefined } : marker)))
}
</script>

<template>
  <fieldset class="fa-markers">
    <legend class="fa-label">{{ t('props.markers') }}</legend>
    <p class="fa-help">{{ t('props.markersHelp') }}</p>
    <div class="fa-markers__chips">
      <button
        v-for="(text, type) in MARKERS"
        :key="type"
        type="button"
        class="fa-chip"
        :aria-pressed="has(String(type))"
        :disabled="disabled"
        @click="toggle(String(type))"
      >
        <FaIcon :name="`marker-${type}`" :size="14" />{{ label(text, locale) }}
      </button>
    </div>
    <label v-for="marker in markers" :key="marker.type" class="fa-field fa-markers__text">
      <span class="fa-label">{{ label(MARKERS[marker.type], locale) || marker.type }} – {{ t('field.text') }}</span>
      <input class="fa-input" :value="marker.text ?? ''" :disabled="disabled" @change="setText(marker.type, ($event.target as HTMLInputElement).value)" />
    </label>
  </fieldset>
</template>

<style>
.fa-markers {
  margin: 0;
  padding: 0;
  border: 0;
}

.fa-markers__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 6px 0 8px;
}

.fa-markers__text {
  margin-top: 6px;
}
</style>
