<script setup lang="ts">
import { computed } from 'vue'
import type { Locale } from '../i18n'
import { useI18n } from '../i18n'
import { riskMessages, STATE_ICONS, stateTone, STATE_KEYS, type FlagState } from '@auditcore/ui-core'

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
