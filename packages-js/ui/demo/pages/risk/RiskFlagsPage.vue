<script setup lang="ts">
import { computed, ref } from 'vue'
import { RiskFlags, type Evaluation, type ProfileDetail } from '@auditcore/ui'
import flowstatJson from '../../../../ui-core/test/fixtures/risk/evaluation-flowstat.json'
import profileJson from '../../../../ui-core/test/fixtures/risk/profile-year-bound.json'
import yearBoundJson from '../../../../ui-core/test/fixtures/risk/evaluation-year-bound.json'

// Echte Antworten von auditcore_risk.web mit synthetischen Belegen.
const SAMPLES = {
  riskanalysis: { evaluation: yearBoundJson as unknown as Evaluation, profile: profileJson as unknown as ProfileDetail },
  flowstat: { evaluation: flowstatJson as unknown as Evaluation, profile: null },
} as const

const sample = ref<keyof typeof SAMPLES>('riskanalysis')
const current = computed(() => SAMPLES[sample.value])
const last = ref('')
</script>

<template>
  <h1>Risiko-Merkmale</h1>
  <p>
    <code>RiskFlags</code> bzw. <code>&lt;flowaudit-risk-flags&gt;</code> zeigt eine Auswertung von
    <code>auditcore_risk.web</code> (<code>POST /evaluate</code>): Verteilung, Filter, Zustand je Datensatz und
    Karten mit Begründung, Eingabewerten und Schwellen. Unbestimmte Merkmale (z. B. fehlender Nettobetrag) bleiben unbestimmt.
  </p>
  <fieldset class="demo-risk__switch">
    <legend>Beispiel</legend>
    <label><input v-model="sample" type="radio" value="riskanalysis" data-testid="sample-riskanalysis"> riskanalysis.year_bound 2026.09.5</label>
    <label><input v-model="sample" type="radio" value="flowstat" data-testid="sample-flowstat"> FlowStat-Belegliste (fehlende Spalten)</label>
  </fieldset>
  <RiskFlags
    :key="sample"
    :evaluation="current.evaluation"
    :profile="current.profile"
    heading="Red Flags der Belegliste"
    @record-select="(index) => (last = index === null ? '' : `Datensatz ${index + 1}`)"
  />
  <p aria-live="polite" class="demo-risk__event">{{ last ? `Ereignis record-select: ${last}` : '' }}</p>
</template>

<style>
.demo-risk__switch { display: flex; flex-wrap: wrap; gap: var(--fa-space-4); margin: 0 0 var(--fa-space-4); padding: var(--fa-space-2) var(--fa-space-3); border: 1px solid var(--fa-color-border); border-radius: var(--fa-radius); font-size: var(--fa-font-size-sm); }
.demo-risk__event { color: var(--fa-color-text-muted); font-size: var(--fa-font-size-sm); }
</style>
