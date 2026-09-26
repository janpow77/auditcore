<script setup lang="ts">
/**
 * Palette in the left column (legacy: mirrored palette): tools, BPMN
 * elements and pools per role. Entries trigger the palette of the running
 * editor; icons come from the FlowAudit set.
 */
import { computed } from 'vue'
import FaIcon from '../base/FaIcon.vue'
import { useI18n } from '../../i18n/useI18n'
import { paletteSections, type PaletteItem } from '@flowaudit/bpmn-flowaudit/ui'

const props = defineProps<{ items: PaletteItem[]; disabled?: boolean }>()
const emit = defineEmits<{ (e: 'trigger', id: string, event: Event): void }>()
const { t } = useI18n()

const sections = computed(() => paletteSections(props.items))
</script>

<template>
  <nav class="fa-palette" :aria-label="t('palette.label')">
    <section v-for="section in sections" v-show="section.items.length" :key="section.id" class="fa-palette__section">
      <h2 class="fa-palette__title">{{ t(section.title) }}</h2>
      <div class="fa-palette__grid">
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
          <span v-if="item.icon && item.color" class="fa-palette__role" :style="{ color: item.color.stroke, background: item.color.fill }"><FaIcon :name="item.icon" :size="20" /></span>
          <FaIcon v-else-if="item.icon" :name="item.icon" :size="20" />
          <span v-else class="fa-palette__fallback">{{ item.title.slice(0, 2) }}</span>
        </button>
      </div>
    </section>
    <p class="fa-help fa-palette__hint">{{ t('palette.hint') }}</p>
  </nav>
</template>
