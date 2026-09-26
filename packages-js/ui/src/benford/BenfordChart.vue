<script setup lang="ts">
import { computed } from 'vue'
import { benfordBarTitle, benfordChartTitle, benfordMessages, benfordTickText, chartGeometry, type Conformity } from '@auditcore/ui-core'
import { useId } from '../composables/useId'
import { useI18n, type Locale } from '../i18n'

const props = withDefaults(defineProps<{ conformity: Conformity; testLabel: string; locale?: Locale }>(), { locale: undefined })
const { t, locale: active } = useI18n(benfordMessages, () => props.locale)
const id = useId('fa-benford-chart')
const geometry = computed(() => chartGeometry(props.conformity.rows))
</script>

<template>
  <figure class="fa-benford__figure">
    <svg
      class="fa-benford__chart"
      :viewBox="`0 0 ${geometry.box.width} ${geometry.box.height}`"
      role="img"
      :aria-labelledby="`${id}-title`"
      data-testid="benford-chart"
    >
      <title :id="`${id}-title`">{{ benfordChartTitle(conformity, testLabel, t) }}</title>
      <g class="fa-benford__grid">
        <g v-for="tick in geometry.yTicks" :key="tick.value">
          <line :x1="geometry.plot.x" :x2="geometry.plot.x + geometry.plot.width" :y1="tick.y" :y2="tick.y" />
          <text :x="geometry.plot.x - 8" :y="tick.y" text-anchor="end" dominant-baseline="middle">{{ benfordTickText(tick.value, geometry.tickDigits, active) }}</text>
        </g>
      </g>
      <g>
        <rect
          v-for="(bar, index) in geometry.bars"
          :key="bar.digit"
          class="fa-benford__bar"
          :class="{ 'fa-benford__bar--exceeds': bar.exceeds }"
          :data-digit="bar.digit"
          :x="bar.x"
          :y="bar.y"
          :width="bar.width"
          :height="bar.height"
          rx="2"
        >
          <title>{{ benfordBarTitle(conformity, index, t, active) }}</title>
        </rect>
      </g>
      <path class="fa-benford__expected" :d="geometry.expectedPath" />
      <circle v-for="(point, index) in geometry.expected" :key="index" class="fa-benford__expected-dot" :cx="point.x" :cy="point.y" :r="geometry.bars.length > 20 ? 1.8 : 3.5" />
      <g class="fa-benford__axis">
        <line :x1="geometry.plot.x" :x2="geometry.plot.x + geometry.plot.width" :y1="geometry.plot.y + geometry.plot.height" :y2="geometry.plot.y + geometry.plot.height" />
        <text v-for="label in geometry.xLabels" :key="label.digit" :x="label.x" :y="geometry.plot.y + geometry.plot.height + 18" text-anchor="middle">{{ label.digit }}</text>
      </g>
    </svg>
    <figcaption class="fa-benford__legend">
      <span><i class="fa-benford__swatch" />{{ t('legendObserved') }}</span>
      <span><i class="fa-benford__swatch fa-benford__swatch--exceeds" />{{ t('legendExceeds') }}</span>
      <span><i class="fa-benford__swatch fa-benford__swatch--expected" />{{ t('legendExpected') }}</span>
    </figcaption>
  </figure>
</template>
