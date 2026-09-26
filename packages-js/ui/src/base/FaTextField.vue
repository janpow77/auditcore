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
