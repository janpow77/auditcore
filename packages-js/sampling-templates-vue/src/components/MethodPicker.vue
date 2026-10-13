<script setup lang="ts">
import { findAvailableSheet, tableOf, type Family, type GuideView, type MatrixGap, type MessageKey, type SheetModule, type Translate, type Variant } from '@auditcore/sampling-templates-core'
import { useId } from '@auditcore/ui'
import { computed, nextTick, ref } from 'vue'
import MethodGuide from './MethodGuide.vue'
import VariantTile from './VariantTile.vue'

/**
 * Verfahrensauswahl: Familien als senkrechte Reiterliste (Pfeiltasten, Pos1/Ende),
 * daneben die Varianten der gewählten Familie als Tabelle Zeiträume × Schichtung
 * bzw. als Liste. Varianten ohne Rechenkern sind gekennzeichnet und nicht wählbar.
 */
const props = defineProps<{ families: readonly Family[]; sheets: readonly SheetModule[]; t: Translate; current?: string | null; guide?: GuideView | null }>()
defineEmits<{ select: [sheet: string]; table: [sheet: string] }>()

const id = useId('fa-st-picker')
const initial = props.families.findIndex((family) => family.variants.some((variant) => variant.sheet === props.current))
const selected = ref(Math.max(0, initial))
const tabs = ref<HTMLButtonElement[]>([])
const family = computed(() => props.families[selected.value] ?? props.families[0]!)
const PERIODS: readonly { count: 1 | 2 | 3; key: MessageKey }[] = [
  { count: 1, key: 'periods1' },
  { count: 2, key: 'periods2' },
  { count: 3, key: 'periods3' },
]
const KEY_STEPS: Readonly<Record<string, (index: number, last: number) => number>> = {
  ArrowDown: (index, last) => (index === last ? 0 : index + 1),
  ArrowUp: (index, last) => (index === 0 ? last : index - 1),
  Home: () => 0,
  End: (_, last) => last,
}

const isAvailable = (variant: Variant): boolean => findAvailableSheet(variant.sheet, props.sheets) !== undefined
/** Nachschlagetabelle der Vorlage (Blatt X1a): kein Verfahren, aber anzeigbar. */
const isTable = (variant: Variant): boolean => tableOf(variant.sheet, props.sheets) !== undefined
const variantAt = (periods: number, stratified: boolean): Variant | undefined => family.value.variants.find((variant) => variant.periods === periods && variant.stratified === stratified)
const gapAt = (periods: number, stratified: boolean): MatrixGap | undefined => family.value.gaps?.find((gap) => gap.periods === periods && gap.stratified === stratified)

function onKeydown(event: KeyboardEvent): void {
  const step = KEY_STEPS[event.key]
  if (!step) return
  event.preventDefault()
  selected.value = step(selected.value, props.families.length - 1)
  void nextTick(() => tabs.value[selected.value]?.focus())
}
</script>

<template>
  <section class="fa-st__picker fa-st__inner" :aria-labelledby="`${id}-question`">
    <h2 :id="`${id}-question`" class="fa-st__question">{{ t('pickerQuestion') }}</h2>
    <p class="fa-st__muted">{{ t('pickerIntro') }}</p>
    <MethodGuide v-if="guide" :guide="guide" :t="t" />
    <div class="fa-st__picker-grid">
      <div class="fa-st__families" role="tablist" aria-orientation="vertical" :aria-label="t('families')" @keydown="onKeydown">
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
          <span class="fa-st__family-name">{{ entry.name }}</span>
          <span class="fa-st__tile-ref">{{ entry.reference }}</span>
        </button>
      </div>
      <div :id="`${id}-panel`" class="fa-st__variants" role="tabpanel" :aria-labelledby="`${id}-tab-${family.id}`" tabindex="0">
        <p v-if="family.notice" class="fa-st__callout">{{ family.notice }}</p>
        <table v-if="family.layout === 'matrix'" class="fa-st__matrix">
          <caption class="fa-sr-only">{{ t('variants') }}: {{ family.name }}</caption>
          <thead>
            <tr>
              <th scope="col">{{ t('periods') }}</th>
              <th scope="col">{{ t('unstratified') }}</th>
              <th scope="col">{{ t('stratified') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="period in PERIODS" :key="period.count">
              <th scope="row">{{ t(period.key) }}</th>
              <td v-for="stratified in [false, true]" :key="String(stratified)">
                <VariantTile v-if="variantAt(period.count, stratified)" :variant="variantAt(period.count, stratified)!" :available="isAvailable(variantAt(period.count, stratified)!)" :table="isTable(variantAt(period.count, stratified)!)" :t="t" @select="$emit('select', $event)" @table="$emit('table', $event)" />
                <div v-else-if="gapAt(period.count, stratified)" class="fa-st__tile fa-st__tile--gap" aria-disabled="true">
                  <span class="fa-st__tile-name">{{ t(period.key) }}, {{ t('stratified') }}: {{ t('noSheet') }}</span>
                  <span class="fa-st__tile-ref">{{ gapAt(period.count, stratified)!.note }}</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <ul v-else class="fa-st__variant-list" :aria-label="`${t('variants')}: ${family.name}`">
          <li v-for="variant in family.variants" :key="variant.sheet">
            <VariantTile :variant="variant" :available="isAvailable(variant)" :table="isTable(variant)" :t="t" @select="$emit('select', $event)" @table="$emit('table', $event)" />
          </li>
        </ul>
      </div>
    </div>
  </section>
</template>
