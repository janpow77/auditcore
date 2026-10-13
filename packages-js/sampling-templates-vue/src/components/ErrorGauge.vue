<script setup lang="ts">
import type { GaugeView, Translate } from '@auditcore/sampling-templates-core'
import { computed } from 'vue'

/** Skala: Gesamtfehlerquote und obere Fehlergrenze gegen die Wesentlichkeitsschwelle. */
const props = defineProps<{ gauge: GaugeView; t: Translate }>()

const LEFT = 8
const WIDTH = 284
const Y = 22
const x = (position: number): number => LEFT + position * WIDTH
const rate = computed(() => x(props.gauge.rate))
const upper = computed(() => (props.gauge.upper === null ? null : x(props.gauge.upper)))
const threshold = computed(() => x(props.gauge.threshold))
</script>

<template>
  <svg class="fa-st__gauge" viewBox="0 0 300 56" role="img" :aria-label="gauge.description">
    <rect class="fa-st__gauge-track" :x="LEFT" :y="Y - 3" :width="WIDTH" height="6" rx="3" />
    <rect v-if="upper !== null" class="fa-st__gauge-range" :x="rate" :y="Y - 3" :width="Math.max(0, upper - rate)" height="6" />
    <rect class="fa-st__gauge-rate" :x="LEFT" :y="Y - 3" :width="rate - LEFT" height="6" rx="3" />
    <line class="fa-st__gauge-threshold" :x1="threshold" :x2="threshold" :y1="Y - 11" :y2="Y + 11" />
    <text class="fa-st__gauge-text fa-st__gauge-text--threshold" :x="threshold" :y="Y - 14" text-anchor="middle">{{ gauge.thresholdLabel }}</text>
    <circle class="fa-st__gauge-rate" :cx="rate" :cy="Y" r="4.5" />
    <circle v-if="upper !== null" class="fa-st__gauge-upper" :cx="upper" :cy="Y" r="3.5" />
    <text class="fa-st__gauge-text" :x="LEFT" :y="Y + 26">● {{ t('gaugeRate') }}  ○ {{ t('gaugeUpper') }}</text>
    <text class="fa-st__gauge-text" :x="LEFT + WIDTH" :y="Y + 26" text-anchor="end">{{ gauge.maxLabel }}</text>
  </svg>
</template>
