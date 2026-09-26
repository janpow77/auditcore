<script setup lang="ts">
import { ref } from 'vue'
import { ExtrapolationPanel, createExtrapolationRestPort, type EvaluationResult, type StratumInput, type UnitInput } from '@flowaudit/ui'

const port = createExtrapolationRestPort({ baseUrl: '/api/extrapolation' })
// Synthetische Stichprobe: eine Schicht, eine Einheit der Vollerhebung,
// ein abgegrenzter systemischer und ein korrigierter anomaler Fehler.
const strata: StratumInput[] = [{ name: 'Programm', book_value: 1_000_000, population_size: 120, systemic_error: 2_000 }]
const units: UnitInput[] = [
  { id: 'V-01', stratum: 'Programm', book_value: 20_000, random_error: 1_000 },
  { id: 'V-02', stratum: 'Programm', book_value: 10_000, systemic_error: 500 },
  { id: 'V-03', stratum: 'Programm', book_value: 5_000 },
  { id: 'V-04', stratum: 'Programm', book_value: 8_000, anomalous_error: 800, anomalous_reason: 'Einmaliger Übertragungsfehler', anomalous_corrected: true },
  { id: 'V-05', stratum: 'Programm', book_value: 200_000, random_error: 4_000, exhaustive: true },
]
const last = ref('')

function onEvaluation(result: EvaluationResult): void {
  last.value = `Ereignis evaluation-completed: ${result.total_error_rate.conclusion}`
}
</script>

<template>
  <h1>Hochrechnung und Fehlerquoten</h1>
  <p>
    <code>&lt;ExtrapolationPanel&gt;</code> bzw. <code>&lt;flowaudit-extrapolation&gt;</code> mit dem REST-Port auf
    <code>auditcore_extrapolation.web</code>: Hochrechnung nach dem KOM-Leitfaden, Gesamtfehlerquote (TER)
    mit Fehlerobergrenze und getrennt davon die Restfehlerquote (RER).
  </p>
  <ExtrapolationPanel :port="port" :strata="strata" :units="units" @evaluation-completed="onEvaluation" />
  <p class="demo-event" aria-live="polite">{{ last }}</p>
</template>
