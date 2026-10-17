<script setup lang="ts">
import type { MessageKey, SummaryView, Tone, Translate } from '@auditcore/sampling-templates-core'
import { FaBadge, useId } from '@auditcore/ui'
import { computed } from 'vue'
import ErrorGauge from './ErrorGauge.vue'

/**
 * Kennzahlenspalte: Hauptgröße als große Karte, die hervorgehobenen Kennzahlen
 * (Gesamtfehlerquote, obere Fehlergrenze) als eigene Karten, die übrigen als
 * kompaktes Raster; darunter die Skala mit Ampel gegen die Wesentlichkeitsschwelle
 * und alle Prüfhinweise als Text und Farbe.
 */
const props = defineProps<{ summary: SummaryView; t: Translate }>()

const id = useId('fa-st-result')
const TONE_KEYS: Readonly<Record<Tone, MessageKey>> = { success: 'toneSuccess', warning: 'toneWarning', danger: 'toneDanger', neutral: 'toneNeutral' }
const strong = computed(() => props.summary.rows.filter((row) => row.strong))
const other = computed(() => props.summary.rows.filter((row) => !row.strong))
</script>

<template>
  <section class="fa-st__card fa-st__summary" :aria-labelledby="`${id}-summary`">
    <h3 :id="`${id}-summary`" class="fa-st__caption">{{ summary.primaryLabel }}</h3>
    <p class="fa-st__big" data-result="primary">
      <template v-if="summary.primaryValue">{{ summary.primaryValue }} <small>{{ summary.primaryUnit }}</small></template>
      <small v-else>{{ summary.primaryNote || t('noValue') }}</small>
    </p>
    <dl v-if="strong.length" class="fa-st__kv fa-st__kpis" data-kpis>
      <div v-for="row in strong" :key="row.label" class="fa-st__kpi">
        <dt>{{ row.label }}</dt>
        <dd class="fa-st__strong">{{ row.value }}</dd>
      </div>
    </dl>
    <ErrorGauge v-if="summary.gauge" :gauge="summary.gauge" :t="t" />
    <dl v-if="other.length" class="fa-st__kv fa-st__kv--more" :aria-label="t('kpiMore')">
      <template v-for="row in other" :key="row.label">
        <dt>{{ row.label }}</dt>
        <dd>{{ row.value }}</dd>
      </template>
    </dl>
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
