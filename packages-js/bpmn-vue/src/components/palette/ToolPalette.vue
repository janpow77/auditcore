<script setup lang="ts">
/**
 * Palette in the left column (legacy: mirrored palette): tools, BPMN
 * elements and pools per role. Entries trigger the palette of the running
 * editor; icons come from the FlowAudit set. „Elemente“ and „Pool mit
 * Rolle“ are shown as icons, large tiles or a list; the choice is kept per
 * browser and switched in one menu in the head of the palette.
 */
import { computed, ref } from 'vue'
import FaIcon from '../base/FaIcon.vue'
import ToolbarMenu from '../base/ToolbarMenu.vue'
import { useI18n } from '../../i18n/useI18n'
import { PALETTE_VIEWS, paletteCaption, paletteName, paletteSections, readPaletteView, writePaletteView, type PaletteItem, type PaletteView } from '@auditcore/bpmn-flowaudit/ui'

const props = defineProps<{ items: PaletteItem[]; disabled?: boolean }>()
const emit = defineEmits<{ (e: 'trigger', id: string, event: Event): void }>()
const { t, locale } = useI18n()

const sections = computed(() => paletteSections(props.items))
const view = ref<PaletteView>(readPaletteView())
const viewOf = (sectionId: string): PaletteView => (sectionId === 'tools' ? 'icons' : view.value)
const iconSize = (sectionId: string) => (viewOf(sectionId) === 'tiles' ? 28 : 20)
const name = (item: PaletteItem) => paletteName(item, t, locale.value)

function choose(next: PaletteView): void {
  view.value = next
  writePaletteView(next)
}
</script>

<template>
  <nav class="fa-palette" :class="`fa-palette--${view}`" :aria-label="t('palette.label')">
    <div class="fa-palette__head">
      <ToolbarMenu v-slot="{ close }" :label="t('palette.view')" icon="overview">
        <button
          v-for="option in PALETTE_VIEWS"
          :key="option"
          type="button"
          role="menuitemradio"
          class="fa-menu-item"
          :aria-checked="view === option"
          @click="(choose(option), close())"
        >
          <FaIcon v-if="view === option" name="check" :size="14" />
          <span v-else class="fa-menu-item__spacer" />
          <span>{{ t(`palette.view.${option}`) }}</span>
        </button>
      </ToolbarMenu>
    </div>
    <section v-for="section in sections" v-show="section.items.length" :key="section.id" class="fa-palette__section" :class="`fa-palette__section--${section.id}`">
      <h2 class="fa-palette__title">{{ t(section.title) }}</h2>
      <div class="fa-palette__grid" :class="`fa-palette__grid--${viewOf(section.id)}`">
        <button
          v-for="item in section.items"
          :key="item.id"
          type="button"
          class="fa-palette__item"
          :class="{ 'fa-palette__item--role': section.id === 'roles' }"
          :title="item.title"
          :aria-label="item.title"
          :disabled="disabled && section.id !== 'tools'"
          draggable="true"
          @click="emit('trigger', item.id, $event)"
          @dragstart="emit('trigger', item.id, $event)"
        >
          <span v-if="item.icon && item.color" class="fa-palette__role" :style="{ color: item.color.stroke, background: item.color.fill }"><FaIcon :name="item.icon" :size="iconSize(section.id)" /></span>
          <FaIcon v-else-if="item.icon" :name="item.icon" :size="iconSize(section.id)" />
          <span v-else class="fa-palette__fallback">{{ item.title.slice(0, 2) }}</span>
          <span v-if="viewOf(section.id) === 'tiles'" class="fa-palette__caption">{{ paletteCaption(item, t) }}</span>
          <span v-else-if="viewOf(section.id) === 'list'" class="fa-palette__text">
            <strong v-if="item.short" class="fa-palette__short">{{ item.short }}</strong>
            <span class="fa-palette__name" :lang="locale">{{ name(item) }}</span>
          </span>
        </button>
      </div>
    </section>
    <p class="fa-help fa-palette__hint">{{ t('palette.hint') }}</p>
  </nav>
</template>
