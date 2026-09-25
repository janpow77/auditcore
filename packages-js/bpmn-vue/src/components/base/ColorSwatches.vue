<script setup lang="ts">
/** List of palette colours with meaning plus „remove colour“ (legacy colour menu). */
import type { PaletteColor } from '@flowaudit/bpmn-flowaudit'
import { useI18n } from '../../i18n/useI18n'

defineProps<{ colors: readonly PaletteColor[]; disabled?: boolean }>()
const emit = defineEmits<{ (e: 'choose', color: PaletteColor | null): void }>()
const { t } = useI18n()
</script>

<template>
  <div class="fa-swatches" role="menu">
    <button v-for="color in colors" :key="color.id" type="button" role="menuitem" class="fa-menu-item" :title="color.meaning" :disabled="disabled" @click="emit('choose', color)">
      <span class="fa-swatch" :style="{ background: color.fill, borderColor: color.stroke }" />
      <span>
        {{ color.label }}
        <span class="fa-menu-hint">{{ color.meaning }}</span>
      </span>
    </button>
    <button type="button" role="menuitem" class="fa-menu-item" :disabled="disabled" @click="emit('choose', null)">
      <span class="fa-swatch fa-swatch--empty" />{{ t('toolbar.colorRemove') }}
    </button>
  </div>
</template>

<style>
.fa-swatch {
  display: inline-block;
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  margin-top: 1px;
  border: 1.5px solid;
  border-radius: 4px;
}

.fa-swatch--empty {
  border-style: dashed;
  border-color: var(--fa-border-strong);
}
</style>
