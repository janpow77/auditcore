<script setup lang="ts">
/**
 * Toggle chips for the domain markers of the selected element. Turning on a
 * colouring marker (e.g. finding) also sets its colour if none is set.
 */
import { MARKERS, label, type Marker } from '@auditcore/bpmn-flowaudit'
import { setMarkerText, toggleMarker } from '@auditcore/bpmn-flowaudit/ui'
import FaIcon from '../../components/base/FaIcon.vue'
import { useI18n } from '../../i18n/useI18n'

const props = defineProps<{ markers: Marker[]; disabled?: boolean }>()
const emit = defineEmits<{ (e: 'update', markers: Marker[]): void; (e: 'color', color: { fill: string; stroke: string }): void }>()
const { t, locale } = useI18n()

const has = (type: string) => props.markers.some((marker) => marker.type === type)

function toggle(type: string): void {
  const next = toggleMarker(props.markers, type)
  emit('update', next.markers)
  if (next.color) emit('color', next.color)
}

const setText = (type: string, text: string) => emit('update', setMarkerText(props.markers, type, text))
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
