<script setup lang="ts">
/**
 * Palette in the left column (legacy: mirrored palette): tools, BPMN
 * elements and pools per role. Entries trigger the palette of the running
 * editor; icons come from the FlowAudit set.
 */
import { computed } from 'vue'
import FaIcon from '../base/FaIcon.vue'
import { useI18n } from '../../i18n/useI18n'
import type { PaletteItem } from './paletteEntries'

const props = defineProps<{ items: PaletteItem[]; disabled?: boolean }>()
const emit = defineEmits<{ (e: 'trigger', id: string, event: Event): void }>()
const { t } = useI18n()

const tools = computed(() => props.items.filter((item) => item.group === 'tools'))
const roles = computed(() => props.items.filter((item) => item.group === 'flowaudit-roles'))
const shapes = computed(() => props.items.filter((item) => item.group !== 'tools' && item.group !== 'flowaudit-roles'))
const sections = computed(() => [
  { id: 'tools', title: 'palette.tools', items: tools.value },
  { id: 'shapes', title: 'palette.shapes', items: shapes.value },
  { id: 'roles', title: 'palette.roles', items: roles.value },
])
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

<style>
.fa-palette {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 132px;
  padding: 10px 8px;
  border-right: 1px solid var(--fa-border);
  background: var(--fa-surface);
  overflow: auto;
}

.fa-palette__title {
  margin: 0 0 6px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--fa-text-muted);
}

.fa-palette__grid {
  display: grid;
  grid-template-columns: repeat(3, 36px);
  gap: 4px;
}

.fa-palette__item {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
  border: 1px solid var(--fa-border);
  border-radius: var(--fa-radius-sm);
  background: var(--fa-surface);
  color: var(--fa-text);
  cursor: grab;
}

.fa-palette__item:hover:not(:disabled) {
  border-color: var(--fa-primary);
  color: var(--fa-primary);
}

.fa-palette__role {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 6px;
}

.fa-palette__fallback {
  font-size: 11px;
  font-weight: 700;
}

.fa-palette__hint {
  margin-top: auto;
}
</style>
