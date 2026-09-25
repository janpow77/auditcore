<script setup lang="ts">
/**
 * Renders one object from declarative field descriptions. Emits the whole
 * updated object on every committed change (blur/enter for text fields).
 */
import { useI18n } from '../i18n/useI18n'
import type { FieldDescriptor } from './descriptors'
import type { Option } from './useOptions'

const props = defineProps<{
  value: Record<string, unknown>
  fields: FieldDescriptor[]
  optionsFor: (field: FieldDescriptor) => Option[]
  disabled?: boolean
}>()
const emit = defineEmits<{ (e: 'update', value: Record<string, unknown>): void }>()
const { t } = useI18n()
const uid = Math.random().toString(36).slice(2, 8)

function set(key: string, raw: unknown): void {
  const next: Record<string, unknown> = { ...props.value }
  const value = typeof raw === 'string' ? raw.trim() : raw
  if (value === '' || value === false || value === undefined || (Array.isArray(value) && !value.length)) delete next[key]
  else next[key] = value
  emit('update', next)
}

function text(field: FieldDescriptor): string {
  const value = props.value[field.key]
  return Array.isArray(value) ? value.join(' ') : value === undefined ? '' : String(value)
}

function onText(field: FieldDescriptor, event: Event): void {
  const raw = (event.target as HTMLInputElement).value
  set(field.key, field.kind === 'tokens' ? raw.split(/[\s,]+/).filter(Boolean) : raw)
}
</script>

<template>
  <div class="fa-grid-2 fa-field-form">
    <label v-for="field in fields" :key="field.key" class="fa-field" :class="{ 'fa-field--wide': field.wide || field.kind === 'textarea' }">
      <template v-if="field.kind === 'checkbox'">
        <span class="fa-check">
          <input type="checkbox" :checked="Boolean(value[field.key])" :disabled="disabled" @change="set(field.key, ($event.target as HTMLInputElement).checked)" />
          {{ t(field.label) }}
        </span>
      </template>
      <template v-else>
        <span :id="`${uid}-${field.key}`" class="fa-label">{{ t(field.label) }}</span>
        <select
          v-if="field.kind === 'select'"
          class="fa-select"
          :value="text(field)"
          :disabled="disabled"
          :aria-labelledby="`${uid}-${field.key}`"
          @change="set(field.key, ($event.target as HTMLSelectElement).value)"
        >
          <option value="">{{ t('common.none') }}</option>
          <option v-for="option in optionsFor(field)" :key="option.value" :value="option.value">{{ option.label }}</option>
          <option v-if="text(field) && !optionsFor(field).some((o) => o.value === text(field))" :value="text(field)">{{ text(field) }}</option>
        </select>
        <textarea
          v-else-if="field.kind === 'textarea'"
          class="fa-textarea"
          rows="3"
          :value="text(field)"
          :disabled="disabled"
          :placeholder="field.placeholder"
          @change="onText(field, $event)"
        />
        <input
          v-else
          class="fa-input"
          :type="field.kind === 'date' ? 'date' : field.kind === 'number' ? 'number' : 'text'"
          :value="text(field)"
          :disabled="disabled"
          :placeholder="field.placeholder"
          @change="onText(field, $event)"
        />
      </template>
    </label>
  </div>
</template>

<style>
.fa-field--wide {
  grid-column: 1 / -1;
}

.fa-check {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}
</style>
