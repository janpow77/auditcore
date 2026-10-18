<script setup lang="ts">
import type { SummaryView, Translate } from '@auditcore/sampling-templates-core'
import { FaBadge } from '@auditcore/ui'
import { computed } from 'vue'

/**
 * Kompakte Kennzahlenleiste für schmale Behälter: Hauptgröße, hervorgehobene
 * Kennzahlen (Gesamtfehlerquote, obere Fehlergrenze) und Ampel gegen die
 * Signifikanzschwelle. Sie klebt beim Rollen oben, damit die Ampel beim
 * Ausfüllen sichtbar bleibt. Für Hilfstechniken ausgeblendet: Dieselben Werte
 * stehen in der Kennzahlenspalte und werden bei Änderung angesagt.
 */
const props = defineProps<{ summary: SummaryView; t: Translate }>()

const primary = computed(() => (props.summary.primaryValue ? `${props.summary.primaryValue} ${props.summary.primaryUnit}` : props.summary.primaryNote || props.t('noValue')))
const rows = computed(() => props.summary.rows.filter((row) => row.strong))
const ampel = computed(() => {
  const gauge = props.summary.gauge
  if (!gauge) return null
  const below = (gauge.upper ?? gauge.rate) < gauge.threshold
  return { tone: below ? ('success' as const) : ('danger' as const), label: props.t(below ? 'kpiBelow' : 'kpiAbove') }
})
</script>

<template>
  <div class="fa-st__strip" aria-hidden="true" data-kpi-strip>
    <span class="fa-st__strip-item"><span class="fa-st__strip-label">{{ summary.primaryLabel }}</span> <strong>{{ primary }}</strong></span>
    <span v-for="row in rows" :key="row.label" class="fa-st__strip-item"><span class="fa-st__strip-label">{{ row.label }}</span> <strong>{{ row.value }}</strong></span>
    <FaBadge v-if="ampel" class="fa-st__strip-ampel" :tone="ampel.tone" :label="ampel.label" />
    <span v-if="summary.invalidNote" class="fa-st__strip-item fa-st__strip-invalid" data-strip-invalid>{{ summary.invalidNote }}</span>
  </div>
</template>

<style>
/* Kompakte Kennzahlenleiste: nur in schmalen Behältern, dort klebt sie beim Rollen oben. */
.fa-st__strip { display: none; }
@container fa-st (max-width: 56rem) {
  .fa-st__strip {
    position: sticky;
    top: var(--fa-st-sticky-top, 0);
    z-index: 5;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--fa-space-1) var(--fa-space-3);
    padding: var(--fa-space-2) var(--fa-space-3);
    border: 1px solid var(--fa-color-border);
    border-radius: var(--fa-radius);
    background: var(--fa-color-surface);
    box-shadow: 0 2px 6px rgb(0 0 0 / 0.08);
    font-size: var(--fa-font-size-sm);
  }
  .fa-st__strip-item { display: inline-flex; flex-wrap: wrap; align-items: baseline; gap: 0 var(--fa-space-1); min-width: 0; max-width: 100%; }
  .fa-st__strip-item strong { overflow-wrap: anywhere; }
  .fa-st__strip-invalid { font-size: var(--fa-font-size-sm); overflow-wrap: anywhere; }
  .fa-st__strip-item strong { font-family: var(--fa-font-mono); font-variant-numeric: tabular-nums; }
  .fa-st__strip-label { color: var(--fa-color-text-muted); font-size: var(--fa-font-size-xs); }
  .fa-st .fa-st__strip-ampel { white-space: normal; }
}
@media print { .fa-st__strip { display: none !important; } }
</style>
