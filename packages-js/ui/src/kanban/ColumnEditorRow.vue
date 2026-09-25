<script setup lang="ts">
import type { Column } from '@flowaudit/kanban-core'
import FaButton from '../base/FaButton.vue'
import { useI18n, type Locale } from '../i18n'
import { COLUMN_COLORS } from './cardView'
import { kanbanDialogMessages } from './messages'

const props = withDefaults(defineProps<{ column: Column; first?: boolean; last?: boolean; canRemove?: boolean; locale?: Locale }>(), { first: false, last: false, canRemove: true, locale: undefined })
const emit = defineEmits<{ update: [patch: Partial<Column>]; remove: []; move: [step: -1 | 1] }>()
const { t } = useI18n(kanbanDialogMessages, () => props.locale)

function limit(event: Event): void {
  const value = (event.target as HTMLInputElement).value
  emit('update', { wip_limit: value === '' ? null : Math.max(0, Math.floor(Number(value))) })
}
</script>

<template>
  <li class="fa-kanban-settings__row" :data-column-editor="column.id">
    <span class="fa-kanban-column__dot" :style="{ '--fa-kanban-column-color': column.color, width: '1rem', height: '1rem' }" aria-hidden="true" />
    <label class="fa-field">
      <span class="fa-field__label">{{ t('columnLabel') }}</span>
      <input class="fa-field__input" :value="column.label" maxlength="80" @input="emit('update', { label: ($event.target as HTMLInputElement).value })" />
    </label>
    <label class="fa-field">
      <span class="fa-field__label">{{ t('wipLimit') }}</span>
      <input class="fa-field__input" type="number" min="1" :value="column.wip_limit ?? ''" @change="limit" />
    </label>
    <label class="fa-kanban-settings__check">
      <input type="checkbox" :checked="column.done" @change="emit('update', { done: ($event.target as HTMLInputElement).checked })" />
      {{ t('doneColumn') }}
    </label>
    <div class="fa-kanban-detail__row">
      <FaButton size="sm" variant="ghost" icon="chevron-up" icon-only :label="t('moveUp')" :disabled="first" @click="emit('move', -1)" />
      <FaButton size="sm" variant="ghost" icon="chevron-down" icon-only :label="t('moveDown')" :disabled="last" @click="emit('move', 1)" />
      <FaButton size="sm" variant="ghost" icon="trash" icon-only :label="t('removeColumn', { label: column.label })" :disabled="!canRemove" @click="emit('remove')" />
    </div>
    <div class="fa-kanban-settings__colors" role="group" :aria-label="t('columnColor', { label: column.label })">
      <button
        v-for="color in COLUMN_COLORS"
        :key="color"
        type="button"
        class="fa-kanban-detail__swatch"
        :style="{ background: color }"
        :aria-label="color"
        :aria-pressed="column.color === color"
        @click="emit('update', { color })"
      />
      <input type="color" :value="column.color" :aria-label="t('columnColor', { label: column.label })" @change="emit('update', { color: ($event.target as HTMLInputElement).value })" />
    </div>
  </li>
</template>
