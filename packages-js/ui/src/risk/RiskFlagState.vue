<script setup lang="ts">
import { computed } from 'vue'
import type { Locale } from '../i18n'
import { useI18n } from '../i18n'
import { riskMessages } from './messages'
import { STATE_ICONS, stateTone } from './view/format'
import { STATE_KEYS } from './view/labels'
import type { FlagState } from './view/state'

const props = withDefaults(defineProps<{
  state: FlagState
  /** Code für die Beschriftung (Tabellenzelle), sonst nur der Zustand. */
  code?: string
  /** Nur Symbol sichtbar, Text für Screenreader und Tooltip. */
  compact?: boolean
  locale?: Locale
}>(), { code: '', compact: false, locale: undefined })

const { t } = useI18n(riskMessages, () => props.locale)
const text = computed(() => t(STATE_KEYS[props.state]))
const label = computed(() => (props.code ? t('stateCell', { code: props.code, state: text.value }) : text.value))
</script>

<template>
  <span
    class="fa-risk-state"
    :class="[`fa-risk-state--${state}`, `fa-risk-state--${stateTone(state)}`, { 'fa-risk-state--compact': compact }]"
    :title="compact ? label : undefined"
    :aria-label="compact ? label : undefined"
    :role="compact ? 'img' : undefined"
  >
    <span class="fa-risk-state__icon" aria-hidden="true">{{ STATE_ICONS[state] }}</span>
    <span v-if="!compact" class="fa-risk-state__text">{{ text }}</span>
  </span>
</template>

<style>
.fa-risk-state { display: inline-flex; align-items: center; gap: var(--fa-space-1); padding: 0.0625rem var(--fa-space-2); border-radius: 999px; border: 1px solid transparent; font: 600 var(--fa-font-size-xs) / 1.3 var(--fa-font-sans); white-space: nowrap; }
.fa-risk-state__icon { display: inline-grid; place-items: center; width: 1.1em; height: 1.1em; font-weight: 700; }
.fa-risk-state--compact { padding: 0.0625rem; min-width: 1.6em; justify-content: center; }
.fa-risk-state--danger { background: var(--fa-color-danger-soft); color: var(--fa-color-danger); border-color: var(--fa-color-danger); }
.fa-risk-state--warning { background: var(--fa-color-warning-soft); color: var(--fa-color-warning); border: 1px dashed var(--fa-color-warning); }
.fa-risk-state--neutral { color: var(--fa-color-text-muted); }
.fa-risk-state--skipped { border: 1px dotted var(--fa-color-border-strong); }
</style>
