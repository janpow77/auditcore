<script setup lang="ts">
/**
 * Page break guides over the canvas (display only, no pointer events),
 * ported from the page view of the audit_designer canvas.
 */
import { computed } from 'vue'
import { computePageGrid, pageSize, type Orientation, type ViewboxLike } from '@flowaudit/bpmn-flowaudit'
import { useI18n } from '../../i18n/useI18n'

const props = defineProps<{ view: string; viewbox: ViewboxLike; width: number; height: number }>()
const { t } = useI18n()

const grid = computed(() => {
  if (props.view === 'aus') return { vertical: [], horizontal: [], pages: [] }
  const [format = 'a4', orientation = 'hoch'] = props.view.split('-')
  return computePageGrid(props.viewbox, pageSize(format, orientation as Orientation), props.width, props.height, t('canvas.page'))
})
</script>

<template>
  <svg v-if="view !== 'aus'" class="fa-page-grid" :width="width" :height="height" aria-hidden="true">
    <line v-for="(x, index) in grid.vertical" :key="`v${index}`" :x1="x" y1="0" :x2="x" :y2="height" />
    <line v-for="(y, index) in grid.horizontal" :key="`h${index}`" x1="0" :y1="y" :x2="width" :y2="y" />
    <text v-for="(page, index) in grid.pages" :key="`p${index}`" :x="page.x" :y="page.y">{{ page.label }}</text>
  </svg>
</template>

<style>
.fa-page-grid {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.fa-page-grid line {
  stroke: var(--fa-primary);
  stroke-width: 1;
  stroke-dasharray: 6 6;
  opacity: 0.55;
}

.fa-page-grid text {
  fill: var(--fa-primary);
  font-size: 10px;
  opacity: 0.75;
}
</style>
