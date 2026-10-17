<script setup lang="ts">
import { findAvailableSheet, findVariant, tableOf, type Family, type GuideView, type MatrixGap, type MessageKey, type SheetModule, type Translate, type Variant } from '@auditcore/sampling-templates-core'
import { FaButton, useId } from '@auditcore/ui'
import { computed, nextTick, ref } from 'vue'
import MethodGlossary from './MethodGlossary.vue'
import MethodGuide from './MethodGuide.vue'
import VariantTile from './VariantTile.vue'

/**
 * Verfahrensauswahl als Filter: Methode (Reiter), Zahl der Zeiträume und
 * Schichtung grenzen die Varianten auf genau ein Verfahren ein, das dann
 * übernommen wird. Familien ohne diese Merkmale (Altvorlagen) erscheinen als
 * Liste. Varianten ohne Rechenkern sind gekennzeichnet und nicht wählbar.
 */
const props = defineProps<{ families: readonly Family[]; sheets: readonly SheetModule[]; t: Translate; current?: string | null; guide?: GuideView | null }>()
const emit = defineEmits<{ select: [sheet: string]; table: [sheet: string] }>()

const id = useId('fa-st-picker')
const initial = props.families.findIndex((family) => family.variants.some((variant) => variant.sheet === props.current))
const selected = ref(Math.max(0, initial))
const currentVariant = props.current ? findVariant(props.current, props.families) : undefined
const periods = ref<1 | 2 | 3>(currentVariant?.periods ?? 1)
const stratified = ref(currentVariant?.stratified ?? false)
const tabs = ref<HTMLButtonElement[]>([])
const family = computed(() => props.families[selected.value] ?? props.families[0]!)
const PERIODS: readonly { count: 1 | 2 | 3; key: MessageKey }[] = [
  { count: 1, key: 'periods1' },
  { count: 2, key: 'periods2' },
  { count: 3, key: 'periods3' },
]
const next = (index: number, last: number): number => (index === last ? 0 : index + 1)
const previous = (index: number, last: number): number => (index === 0 ? last : index - 1)
const KEY_STEPS: Readonly<Record<string, (index: number, last: number) => number>> = {
  ArrowRight: next,
  ArrowDown: next,
  ArrowLeft: previous,
  ArrowUp: previous,
  Home: () => 0,
  End: (_, last) => last,
}

const isAvailable = (variant: Variant): boolean => findAvailableSheet(variant.sheet, props.sheets) !== undefined
/** Nachschlagetabelle der Vorlage (Blatt X1a): kein Verfahren, aber anzeigbar. */
const isTable = (variant: Variant): boolean => tableOf(variant.sheet, props.sheets) !== undefined

/** Filterbar ist eine Familie, deren Varianten alle eine Schichtung angeben; Zeiträume nur in Matrixfamilien. */
const filterable = computed(() => family.value.variants.every((variant) => variant.stratified !== undefined))
const hasPeriods = computed(() => family.value.layout === 'matrix')
const match = computed<Variant | undefined>(() =>
  family.value.variants.find((variant) => variant.stratified === stratified.value && (!hasPeriods.value || variant.periods === periods.value)),
)
const gap = computed<MatrixGap | undefined>(() => (hasPeriods.value ? family.value.gaps?.find((entry) => entry.periods === periods.value && entry.stratified === stratified.value) : undefined))

function onKeydown(event: KeyboardEvent): void {
  const step = KEY_STEPS[event.key]
  if (!step) return
  event.preventDefault()
  selected.value = step(selected.value, props.families.length - 1)
  void nextTick(() => tabs.value[selected.value]?.focus())
}

function use(variant: Variant): void {
  if (isAvailable(variant)) emit('select', variant.sheet)
}
</script>

<template>
  <section class="fa-st__picker fa-st__inner" :aria-labelledby="`${id}-question`">
    <h2 :id="`${id}-question`" class="fa-st__question">{{ t('pickerQuestion') }}</h2>
    <div class="fa-st__picker-grid">
      <div class="fa-st__picker-main">
        <div class="fa-st__filter">
          <span class="fa-st__filter-label">{{ t('pickerFilterMethod') }}</span>
          <div class="fa-st__families" role="tablist" :aria-label="t('families')" @keydown="onKeydown">
            <button
              v-for="(entry, index) in families"
              :id="`${id}-tab-${entry.id}`"
              :key="entry.id"
              ref="tabs"
              type="button"
              role="tab"
              class="fa-st__family"
              :aria-selected="index === selected"
              :aria-controls="`${id}-panel`"
              :tabindex="index === selected ? 0 : -1"
              @click="selected = index"
            >
              {{ entry.name }}
            </button>
          </div>
        </div>
        <div :id="`${id}-panel`" class="fa-st__variants" role="tabpanel" :aria-labelledby="`${id}-tab-${family.id}`">
          <template v-if="filterable">
            <div v-if="hasPeriods" class="fa-st__filter">
              <span :id="`${id}-periods`" class="fa-st__filter-label">{{ t('pickerFilterPeriods') }}</span>
              <div class="fa-st__segmented" role="group" :aria-labelledby="`${id}-periods`">
                <button v-for="period in PERIODS" :key="period.count" type="button" class="fa-st__segment" :aria-pressed="periods === period.count" :data-periods="period.count" @click="periods = period.count">{{ t(period.key) }}</button>
              </div>
            </div>
            <div class="fa-st__filter">
              <span :id="`${id}-strata`" class="fa-st__filter-label">{{ t('pickerFilterStrata') }}</span>
              <div class="fa-st__segmented" role="group" :aria-labelledby="`${id}-strata`">
                <button v-for="value in [false, true]" :key="String(value)" type="button" class="fa-st__segment" :aria-pressed="stratified === value" :data-stratified="String(value)" @click="stratified = value">{{ t(value ? 'stratified' : 'unstratified') }}</button>
              </div>
            </div>
            <div class="fa-st__card fa-st__match" data-match>
              <p class="fa-st__caption">{{ t('pickerMatch') }}</p>
              <template v-if="match">
                <p :id="`${id}-match`" class="fa-st__match-name">{{ match.name }}</p>
                <p class="fa-st__tile-ref">{{ match.reference }} · {{ t('template2017', { name: match.template2017 }) }}</p>
                <p v-if="match.sheet === current" class="fa-st__tile-ref">{{ t('pickerCurrent') }}</p>
                <div class="fa-st__match-actions">
                  <FaButton
                    variant="primary"
                    :label="isAvailable(match) ? t('pickerUse') : t('notAvailable')"
                    :aria-describedby="`${id}-match`"
                    :aria-disabled="isAvailable(match) ? undefined : 'true'"
                    :data-sheet="match.sheet"
                    @click="use(match)"
                  />
                </div>
              </template>
              <p v-else-if="gap" class="fa-st__tile-ref" data-gap>{{ t('noSheet') }}. {{ gap.note }}</p>
            </div>
          </template>
          <template v-else>
            <p v-if="family.notice" class="fa-st__callout">{{ family.notice }}</p>
            <ul class="fa-st__variant-list" :aria-label="`${t('variants')}: ${family.name}`">
              <li v-for="variant in family.variants" :key="variant.sheet">
                <VariantTile :variant="variant" :available="isAvailable(variant)" :table="isTable(variant)" :t="t" @select="$emit('select', $event)" @table="$emit('table', $event)" />
              </li>
            </ul>
          </template>
          <p class="fa-st__tile-ref fa-st__family-ref">{{ family.reference }}</p>
        </div>
      </div>
      <div class="fa-st__picker-side">
        <MethodGuide v-if="guide" :guide="guide" :t="t" />
        <MethodGlossary :t="t" />
      </div>
    </div>
  </section>
</template>
