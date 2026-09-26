<script setup lang="ts">
/**
 * Renders one object from declarative field descriptions. Emits the whole
 * updated object on every committed change (blur/enter for text fields).
 */
import { fieldText, inputType, isWide, parseFieldInput, unknownOption, withField, type FieldDescriptor, type Option } from '@auditcore/bpmn-flowaudit/ui'
import { useI18n } from '../i18n/useI18n'

const props = defineProps<{
  value: Record<string, unknown>
  fields: FieldDescriptor[]
  optionsFor: (field: FieldDescriptor) => Option[]
  disabled?: boolean
}>()
const emit = defineEmits<{ (e: 'update', value: Record<string, unknown>): void }>()
const { t } = useI18n()
const uid = Math.random().toString(36).slice(2, 8)

const set = (key: string, raw: unknown) => emit('update', withField(props.value, key, raw))
const text = (field: FieldDescriptor) => fieldText(props.value, field)
const onText = (field: FieldDescriptor, event: Event) => set(field.key, parseFieldInput(field, (event.target as HTMLInputElement).value))
</script>

<template>
  <div class="fa-grid-2 fa-field-form">
    <label v-for="field in fields" :key="field.key" class="fa-field" :class="{ 'fa-field--wide': isWide(field) }">
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
          <option v-if="unknownOption(optionsFor(field), text(field))" :value="text(field)">{{ text(field) }}</option>
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
          :type="inputType(field)"
          :value="text(field)"
          :disabled="disabled"
          :placeholder="field.placeholder"
          @change="onText(field, $event)"
        />
      </template>
    </label>
  </div>
</template>
