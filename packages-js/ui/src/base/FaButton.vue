<script setup lang="ts">
import { computed } from 'vue'
import FaIcon from './FaIcon.vue'
import type { IconName } from '@flowaudit/ui-core'
import type { ButtonSize, ButtonVariant } from '@flowaudit/ui-core'

const props = withDefaults(defineProps<{
  variant?: ButtonVariant
  size?: ButtonSize
  icon?: IconName
  /** Nur Symbol: `label` wird dann zur zugänglichen Beschriftung und zum Tooltip. */
  iconOnly?: boolean
  label?: string
  type?: 'button' | 'submit' | 'reset'
  disabled?: boolean
  loading?: boolean
  pressed?: boolean
}>(), {
  variant: 'secondary',
  size: 'md',
  icon: undefined,
  iconOnly: false,
  label: '',
  type: 'button',
  disabled: false,
  loading: false,
  pressed: undefined,
})

defineEmits<{ click: [event: MouseEvent] }>()

const classes = computed(() => [
  'fa-button',
  `fa-button--${props.variant}`,
  `fa-button--${props.size}`,
  { 'fa-button--icon-only': props.iconOnly, 'fa-button--loading': props.loading },
])
</script>

<template>
  <button
    :class="classes"
    :type="type"
    :disabled="disabled || loading"
    :aria-busy="loading || undefined"
    :aria-pressed="pressed"
    :aria-label="iconOnly ? label : undefined"
    :title="iconOnly ? label : undefined"
    @click="$emit('click', $event)"
  >
    <FaIcon v-if="icon" :name="icon" :size="size === 'sm' ? 14 : 16" />
    <span v-if="!iconOnly" class="fa-button__label"><slot>{{ label }}</slot></span>
  </button>
</template>
