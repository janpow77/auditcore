<script setup lang="ts">
/** Colour of the selected element: audit palette, removal and colour from markers. */
import { computed } from 'vue'
import { MARKER_COLOR_PRECEDENCE, MARKER_COLORS, PALETTE_COLORS, type PaletteColor } from '@flowaudit/bpmn-flowaudit'
import { useI18n } from '../../i18n/useI18n'
import { useEditorContext } from '../../stores/context'
import ColorSwatches from '../../components/base/ColorSwatches.vue'

const props = defineProps<{ palette?: readonly PaletteColor[] }>()
const { selection, editor, readonly } = useEditorContext()
const { t } = useI18n()

const colors = computed(() => props.palette ?? PALETTE_COLORS)
const fromMarkers = computed(() => {
  const types = new Set(selection.extensions.value.markers.map((marker) => marker.type))
  const winner = MARKER_COLOR_PRECEDENCE.find((type) => types.has(type))
  return winner ? MARKER_COLORS[winner] : null
})

function apply(color: { fill: string; stroke: string } | null): void {
  const element = selection.element.value
  if (element) editor.services().modeling.setColor([element], { fill: color?.fill ?? null, stroke: color?.stroke ?? null })
}
</script>

<template>
  <div class="fa-tab-color">
    <h3 class="fa-section__title">{{ t('props.color.palette') }}</h3>
    <ColorSwatches :colors="colors" :disabled="readonly()" @choose="apply" />
    <button v-if="fromMarkers" type="button" class="fa-btn fa-section" :disabled="readonly()" @click="apply(fromMarkers)">
      <span class="fa-swatch" :style="{ background: fromMarkers.fill, borderColor: fromMarkers.stroke }" />{{ t('props.color.fromMarkers') }}
    </button>
  </div>
</template>
