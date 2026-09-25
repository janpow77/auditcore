<script setup lang="ts">
import { computed } from 'vue'
import FaIcon from './FaIcon.vue'
import type { IconName } from './icons'
import type { ButtonSize, ButtonVariant } from './types'

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

<style>
.fa-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--fa-space-2);
  min-height: 2.25rem;
  padding: 0 var(--fa-space-4);
  border: 1px solid transparent;
  border-radius: var(--fa-radius);
  font: 500 var(--fa-font-size-sm) / 1 var(--fa-font-sans);
  cursor: pointer;
  transition: background var(--fa-transition), border-color var(--fa-transition), color var(--fa-transition);
}
.fa-button:focus-visible { outline: none; box-shadow: var(--fa-focus-ring); }
.fa-button:disabled { cursor: not-allowed; opacity: 0.55; }
.fa-button--sm { min-height: 1.75rem; padding: 0 var(--fa-space-3); font-size: var(--fa-font-size-xs); }
.fa-button--icon-only { padding: 0; width: 2.25rem; }
.fa-button--sm.fa-button--icon-only { width: 1.75rem; }
.fa-button--primary { background: var(--fa-color-accent); color: var(--fa-color-accent-contrast); }
.fa-button--primary:hover:not(:disabled) { background: var(--fa-color-accent-hover); }
.fa-button--secondary { background: var(--fa-color-surface); border-color: var(--fa-color-border); color: var(--fa-color-text); }
.fa-button--secondary:hover:not(:disabled) { border-color: var(--fa-color-border-strong); }
.fa-button--ghost { background: transparent; color: var(--fa-color-text-muted); }
.fa-button--ghost:hover:not(:disabled), .fa-button--ghost[aria-pressed='true'] { background: var(--fa-color-surface-sunken); color: var(--fa-color-text); }
.fa-button--danger { background: var(--fa-color-danger); color: #fff; }
.fa-button--loading { cursor: progress; }
</style>
