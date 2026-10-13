<script setup lang="ts">
import type { MessageKey, SummaryView, Tone, Translate } from '@auditcore/sampling-templates-core'
import { FaBadge, useId } from '@auditcore/ui'
import ErrorGauge from './ErrorGauge.vue'

/** Mitlaufende Ergebnisspalte: Hauptgröße, Kennzahlen, Skala und alle Prüfhinweise als Text und Farbe. */
defineProps<{ summary: SummaryView; t: Translate }>()

const id = useId('fa-st-result')
const TONE_KEYS: Readonly<Record<Tone, MessageKey>> = { success: 'toneSuccess', warning: 'toneWarning', danger: 'toneDanger', neutral: 'toneNeutral' }
</script>

<template>
  <section class="fa-st__card fa-st__summary" :aria-labelledby="`${id}-summary`">
    <h3 :id="`${id}-summary`" class="fa-st__caption">{{ summary.primaryLabel }}</h3>
    <p class="fa-st__big" data-result="primary">
      <template v-if="summary.primaryValue">{{ summary.primaryValue }} <small>{{ summary.primaryUnit }}</small></template>
      <small v-else>{{ summary.primaryNote || t('noValue') }}</small>
    </p>
    <dl class="fa-st__kv">
      <template v-for="row in summary.rows" :key="row.label">
        <dt>{{ row.label }}</dt>
        <dd :class="{ 'fa-st__strong': row.strong }">{{ row.value }}</dd>
      </template>
    </dl>
    <ErrorGauge v-if="summary.gauge" :gauge="summary.gauge" :t="t" />
  </section>
  <section class="fa-st__card fa-st__hints" :aria-labelledby="`${id}-hints`">
    <h3 :id="`${id}-hints`" class="fa-st__caption">{{ t('hints') }}</h3>
    <ul class="fa-st__hint-list">
      <li v-for="hint in summary.hints" :key="hint.id" :data-hint="hint.source">
        <span v-if="hint.source === 'web'" class="fa-st__web">{{ t('webHint') }}</span>
        <FaBadge class="fa-st__pill" :tone="hint.tone"><span class="fa-sr-only">{{ t(TONE_KEYS[hint.tone]) }}: </span>{{ hint.text }}</FaBadge>
      </li>
      <li v-if="summary.hints.length === 0"><FaBadge class="fa-st__pill" :label="t('noHints')" /></li>
    </ul>
  </section>
</template>
