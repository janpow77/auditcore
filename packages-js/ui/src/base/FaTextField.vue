<script setup lang="ts">
import { useId } from '../composables/useId'

withDefaults(defineProps<{
  label: string
  type?: 'text' | 'search' | 'email' | 'date' | 'number' | 'password'
  placeholder?: string
  hint?: string
  error?: string
  disabled?: boolean
  required?: boolean
  hideLabel?: boolean
  autofocus?: boolean
}>(), { type: 'text', placeholder: '', hint: '', error: '', disabled: false, required: false, hideLabel: false, autofocus: false })

const model = defineModel<string>({ default: '' })
const id = useId('fa-field')
</script>

<template>
  <div class="fa-field" :class="{ 'fa-field--error': !!error }">
    <label :for="id" class="fa-field__label" :class="{ 'fa-sr-only': hideLabel }">{{ label }}</label>
    <input
      :id="id"
      v-model="model"
      class="fa-field__input"
      :type="type"
      :placeholder="placeholder"
      :disabled="disabled"
      :required="required"
      :autofocus="autofocus || undefined"
      :aria-invalid="error ? 'true' : undefined"
      :aria-describedby="error || hint ? `${id}-note` : undefined"
    />
    <p v-if="error || hint" :id="`${id}-note`" class="fa-field__note" :role="error ? 'alert' : undefined">
      {{ error || hint }}
    </p>
  </div>
</template>

<style>
.fa-field { display: flex; flex-direction: column; gap: var(--fa-space-1); font-family: var(--fa-font-sans); }
.fa-field__label { font-size: var(--fa-font-size-xs); font-weight: 600; color: var(--fa-color-text-muted); }
.fa-field__input {
  min-height: 2.25rem;
  padding: 0 var(--fa-space-3);
  border: 1px solid var(--fa-color-border);
  border-radius: var(--fa-radius);
  background: var(--fa-color-surface);
  color: var(--fa-color-text);
  font: var(--fa-font-size-sm) var(--fa-font-sans);
}
.fa-field__input:focus-visible { outline: none; border-color: var(--fa-color-accent); box-shadow: var(--fa-focus-ring); }
.fa-field__note { margin: 0; font-size: var(--fa-font-size-xs); color: var(--fa-color-text-muted); }
.fa-field--error .fa-field__input { border-color: var(--fa-color-danger); }
.fa-field--error .fa-field__note { color: var(--fa-color-danger); }
</style>
